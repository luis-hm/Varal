import uuid
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.lancamentos import servicos as contas
from apps.pagamentos.models import Pagamento
from apps.solicitacoes.models import Solicitacao
from apps.solicitacoes.tasks import processar_solicitacao
from tests import test_contas, test_pagamentos
from tests.test_grupos import cliente

contas_fixture = test_contas.f
pytestmark = pytest.mark.django_db


@pytest.fixture
def f(contas_fixture):
    return contas_fixture


def origem_e_payload(f):
    origem = test_contas.nova(f.u["membro"], f.pessoal["membro"])
    c = cliente(f.u["membro"])
    detalhe = c.get(f"/api/lancamentos/{origem.pk}/").json()
    payload = {
        "nonce": str(uuid.uuid4()),
        "grupo_id": str(f.grupo.pk),
        "pagador_id": str(f.u["pagador"].pk),
        "mensagem": "Por favor",
        "confirmar_compartilhamento": True,
        "versao_compartilhamento": detalhe["versao_compartilhamento"],
    }
    return origem, c, payload


def criar(f):
    origem, c, payload = origem_e_payload(f)
    url = f"/api/lancamentos/{origem.pk}/solicitacoes/"
    response = c.post(url, payload, content_type="application/json")
    assert response.status_code == 202, response.content
    reserva = Solicitacao.objects.get(pk=response.json()["id"])
    processar_solicitacao(str(reserva.pk))
    reserva.refresh_from_db()
    assert reserva.estado == "ativa"
    return origem, reserva, c, payload


def test_rn20_solicitacao_copia_privada_pagamento_e_undo(f):
    origem, reserva, c, payload = criar(f)
    copia = reserva.copia
    assert copia.espaco_id == f.grupo.pk and copia.visibilidade == "restrita"
    assert cliente(f.u["admin"]).get(f"/api/lancamentos/{copia.pk}/").status_code == 404
    detalhe = cliente(f.u["pagador"]).get(f"/api/lancamentos/{copia.pk}/")
    assert detalhe.status_code == 200
    assert str(origem.pk) not in detalhe.content.decode()
    assert detalhe.json()["mensagem_solicitacao"] == payload["mensagem"]
    response = test_pagamentos.pagar(f, copia, nome="pagador")
    assert response.status_code == 201, response.content
    origem.refresh_from_db()
    assert origem.status == "paga"
    grupo = Pagamento.objects.get(lancamento=copia, desfeito_em__isnull=True)
    assert Pagamento.objects.filter(lancamento=origem, desfeito_em__isnull=True).count() == 1
    assert test_pagamentos.desfazer(f, copia, grupo, nome="pagador").status_code == 200
    origem.refresh_from_db()
    assert origem.status == "pendente"
    historico = c.get(f"/api/lancamentos/{origem.pk}/").json()["historico"]
    undo = next(h for h in historico if h["acao"] == "pagamento_desfeito")
    assert undo["automatica"] is True and undo["autor"] is None
    assert str(f.u["pagador"].pk) not in str(undo)


def test_q10_2_versao_revisada_impede_compartilhar_alteracao(f):
    origem, c, payload = origem_e_payload(f)
    contas.editar(f.u["membro"], origem.pk, {"descricao": "Alterada"})
    r = c.post(
        f"/api/lancamentos/{origem.pk}/solicitacoes/", payload, content_type="application/json"
    )
    assert r.status_code == 409 and not Solicitacao.objects.exists()


def test_q10_3_nonce_tombstone_impede_post_tardio(f):
    origem, c, payload = origem_e_payload(f)
    url = f"/api/lancamentos/{origem.pk}/solicitacoes/nonce/{payload['nonce']}/"
    assert c.delete(url).status_code == 204
    assert (
        c.post(
            f"/api/lancamentos/{origem.pk}/solicitacoes/", payload, content_type="application/json"
        ).status_code
        == 409
    )
    assert not Solicitacao.objects.exists()


def test_q10_10_modo_simples_abertas_de_todos_meses(f):
    for delta in (3, 45):
        test_contas.nova(
            f.u["membro"],
            f.grupo,
            pagador=f.u["pagador"].pk,
            vencimento=timezone.localdate() + timedelta(days=delta),
        )
    r = cliente(f.u["pagador"]).get(f"/api/espacos/{f.grupo.pk}/lancamentos/simples/")
    assert r.status_code == 200, r.content
    assert r.json()["abertas_qtd"] == len(r.json()["itens"]) == 2
    assert all(item["pode_pagar"] for item in r.json()["itens"])


def test_rn20_pagar_pessoal_cancela_copia_sem_reabrir_undo(f):
    origem, reserva, _, _ = criar(f)
    r = test_pagamentos.pagar(f, origem, nome="membro")
    assert r.status_code == 201, r.content
    reserva.refresh_from_db()
    reserva.copia.refresh_from_db()
    assert reserva.estado == "encerrada" and reserva.copia.status == "cancelada"
    marca = Pagamento.objects.get(lancamento=origem, desfeito_em__isnull=True)
    assert test_pagamentos.desfazer(f, origem, marca, nome="membro").status_code == 200
    reserva.copia.refresh_from_db()
    assert reserva.copia.status == "cancelada"


def test_q10_4_bloqueio_financeiro_sem_impedir_noop(f):
    origem, reserva, _, _ = criar(f)
    dono = cliente(f.u["membro"])
    url = f"/api/lancamentos/{origem.pk}/"
    assert (
        dono.patch(url, {"valor_centavos": 1001}, content_type="application/json").status_code
        == 409
    )
    assert (
        dono.patch(url, {"valor_centavos": 1000}, content_type="application/json").status_code
        == 200
    )
    url_grupo = f"/api/lancamentos/{reserva.copia_id}/"
    assert (
        dono.patch(
            url_grupo,
            {"vencimento": (timezone.localdate() + timedelta(days=20)).isoformat()},
            content_type="application/json",
        ).status_code
        == 409
    )
    assert (
        dono.patch(
            url_grupo, {"descricao": "Nome local"}, content_type="application/json"
        ).status_code
        == 200
    )


def test_q10_9_avisos_pagamento_pareado_causa_unica(f):
    from apps.notificacoes.models import Notificacao, TipoEvento
    from apps.notificacoes.servicos import consumir_fontes

    origem, reserva, _, _ = criar(f)
    consumir_fontes()
    n = Notificacao.objects.get(evento__tipo=TipoEvento.SOLICITACAO)
    assert n.destinatario_id == f.u["pagador"].pk
    assert test_pagamentos.pagar(f, reserva.copia, nome="pagador").status_code == 201
    consumir_fontes()
    n.refresh_from_db()
    assert n.revogado_em
    avisos = Notificacao.objects.filter(
        evento__tipo=TipoEvento.PAGAMENTO, destinatario=f.u["membro"]
    )
    assert avisos.count() == 1
    assert avisos.get().evento.lancamento_id == origem.pk


@pytest.mark.django_db(transaction=True)
def test_rn20_concorrencia_real_pagamento_pessoal_e_grupo(f):
    from tests.test_grupos import rodar_em_paralelo

    origem, reserva, _, _ = criar(f)
    resultados = rodar_em_paralelo(
        lambda: test_pagamentos.pagar(f, origem, nome="membro"),
        lambda: test_pagamentos.pagar(f, reserva.copia, nome="pagador"),
    )
    assert all(hasattr(r, "status_code") for r in resultados), resultados
    assert sorted(r.status_code for r in resultados) == [201, 409]
    origem.refresh_from_db()
    reserva.copia.refresh_from_db()
    assert origem.status == "paga"
    ativas = Pagamento.objects.filter(lancamento=origem, desfeito_em__isnull=True)
    assert ativas.count() == 1
    if reserva.copia.status == "paga":
        assert (
            Pagamento.objects.filter(lancamento=reserva.copia, desfeito_em__isnull=True).count()
            == 1
        )
    else:
        assert reserva.copia.status == "cancelada"


def test_q10_9_revogacao_fonte_antes_de_consumir_nao_reaparece(f):
    from apps.espacos import servicos as grupos
    from apps.notificacoes.models import Notificacao, TipoEvento
    from apps.notificacoes.servicos import consumir_fontes

    _, reserva, _, _ = criar(f)
    membro = f.m["pagador"]
    grupos.alterar_papel(f.grupo, membro.pk, "observador")
    grupos.alterar_papel(f.grupo, membro.pk, "pagador")
    consumir_fontes()
    reserva.evento.refresh_from_db()
    assert reserva.evento.processado_em and reserva.evento.resultado == "inaplicavel"
    assert not Notificacao.objects.filter(evento__tipo=TipoEvento.SOLICITACAO).exists()


def test_q10_8_preparacao_revogada_se_autor_perde_papel_mesmo_com_retorno(f):
    from apps.espacos import servicos as grupos

    origem, c, payload = origem_e_payload(f)
    r = c.post(
        f"/api/lancamentos/{origem.pk}/solicitacoes/", payload, content_type="application/json"
    )
    assert r.status_code == 202
    reserva = Solicitacao.objects.get(pk=r.json()["id"])
    grupos.alterar_papel(f.grupo, f.m["membro"].pk, "observador")
    grupos.alterar_papel(f.grupo, f.m["membro"].pk, "membro")
    processar_solicitacao(str(reserva.pk))
    reserva.refresh_from_db()
    assert reserva.estado == "encerrada" and reserva.copia_id is None


def test_q10_6_flags_derivada_exigem_direitos_grupo(f):
    origem, reserva, c, _ = criar(f)
    assert test_pagamentos.pagar(f, reserva.copia, nome="pagador").status_code == 201
    detalhe = c.get(f"/api/lancamentos/{origem.pk}/").json()
    assert detalhe["pagamento_ativo"]["derivado"] is True
    assert detalhe["pode_desfazer_pagamento"] is False
    assert detalhe["pode_anexar_comprovante"] is False
    marca = Pagamento.objects.get(lancamento=origem, desfeito_em__isnull=True)
    assert test_pagamentos.desfazer(f, origem, marca, nome="membro").status_code == 409
    origem.refresh_from_db()
    assert origem.status == "paga"


def test_q10_8_exclusao_fisica_dono_nao_cancela_reserva_aceita(f):
    origem, c, payload = origem_e_payload(f)
    r = c.post(
        f"/api/lancamentos/{origem.pk}/solicitacoes/", payload, content_type="application/json"
    )
    assert r.status_code == 202
    reserva = Solicitacao.objects.get(pk=r.json()["id"])
    f.u["membro"].delete()
    reserva.refresh_from_db()
    assert reserva.origem_id is None and reserva.solicitante_id is None
    processar_solicitacao(str(reserva.pk))
    reserva.refresh_from_db()
    assert reserva.estado == "ativa" and reserva.copia.criador_id is None
    assert test_pagamentos.pagar(f, reserva.copia, nome="pagador").status_code == 201
    assert not Solicitacao.objects.filter(origem_id=origem.pk).exists()


@pytest.mark.django_db(transaction=True)
def test_q10_3_dupla_reserva_concorrente_so_uma_viva(f):
    from tests.test_grupos import rodar_em_paralelo

    origem, _, payload = origem_e_payload(f)
    outro = {**payload, "nonce": str(uuid.uuid4())}
    url = f"/api/lancamentos/{origem.pk}/solicitacoes/"
    resultados = rodar_em_paralelo(
        lambda: cliente(f.u["membro"]).post(url, payload, content_type="application/json"),
        lambda: cliente(f.u["membro"]).post(url, outro, content_type="application/json"),
    )
    assert all(hasattr(r, "status_code") for r in resultados), resultados
    assert sorted(r.status_code for r in resultados) == [202, 409]
    assert (
        Solicitacao.objects.filter(origem=origem, estado__in=["preparando", "ativa"]).count() == 1
    )


@pytest.mark.django_db(transaction=True)
def test_rnf06_limpeza_comprovante_nao_bloqueia_renovacao_durante_s3(settings, tmp_path):
    import threading
    from unittest.mock import patch

    from django.db import connection

    from apps.pagamentos.models import LimpezaComprovante
    from apps.pagamentos.tasks import intencao_limpeza, recuperar_limpeza

    settings.PDF_SPOOL_DIR = str(tmp_path)
    pk = uuid.uuid4()
    LimpezaComprovante.objects.create(pk=pk)
    entrou, liberar = threading.Event(), threading.Event()
    erros = []

    def apagar(_chave):
        entrou.set()
        assert liberar.wait(5)

    def worker():
        try:
            recuperar_limpeza.run()
        except Exception as exc:
            erros.append(exc)
        finally:
            connection.close()

    with (
        patch("apps.pagamentos.tasks.armazenamento") as storage,
        patch("apps.pagamentos.tasks.agendar"),
    ):
        storage.return_value.delete.side_effect = apagar
        t = threading.Thread(target=worker)
        t.start()
        assert entrou.wait(5)
        try:
            intencao_limpeza(pk)
            assert LimpezaComprovante.objects.get(pk=pk).geracao == 2
        finally:
            liberar.set()
            t.join(5)
        assert not t.is_alive() and not erros
    assert LimpezaComprovante.objects.get(pk=pk).geracao == 2


def test_rnf06_put_comprovante_incerto_mantem_intencao(f, settings, tmp_path):
    from unittest.mock import patch

    from apps.pagamentos.models import DocumentoComprovante, LimpezaComprovante
    from apps.pagamentos.storage import spool
    from apps.pagamentos.tasks import processar_comprovante, recuperar_limpeza

    settings.PDF_SPOOL_DIR = str(tmp_path)
    conta = test_pagamentos.criar(f)
    doc = DocumentoComprovante.objects.create(
        lancamento=conta, criado_por=f.u["membro"], versao=0, nome="teste.png", tamanho=8
    )
    path = spool(doc.pk)
    doc_id = doc.pk
    path.parent.mkdir(parents=True)
    path.write_bytes(b"sintetico")
    with (
        patch("apps.pagamentos.tasks.validar_isolado", return_value="image/png"),
        patch("apps.pagamentos.tasks.armazenamento") as storage,
        patch("apps.pagamentos.tasks.agendar"),
        patch.object(processar_comprovante, "retry", side_effect=RuntimeError("retry")),
    ):
        storage.return_value.save.side_effect = TimeoutError()
        with pytest.raises(RuntimeError):
            processar_comprovante.run(str(doc.pk))
        assert LimpezaComprovante.objects.get(pk=doc_id).incerta
        doc.delete()
        recuperar_limpeza.run()
        assert LimpezaComprovante.objects.get(pk=doc_id).incerta


def test_q23_opcoes_identificam_membros_atuais_sem_nome_e_excluem_ex_membro(f):
    from apps.contas_usuario.models import Usuario

    origem = test_contas.nova(f.u["membro"], f.pessoal["membro"])
    atuais = [f.u["admin"], f.u["pagador"]]
    Usuario.objects.filter(pk__in=[u.pk for u in atuais]).update(nome="")
    url = f"/api/lancamentos/{origem.pk}/solicitacoes/opcoes/"
    assert cliente().get(url).status_code == 403
    assert cliente(f.u["fora"]).get(url).status_code == 404
    resposta = cliente(f.u["membro"]).get(url)
    assert resposta.status_code == 200
    grupo = next(g for g in resposta.json() if g["id"] == str(f.grupo.pk))
    nomes = {p["id"]: p["nome"] for p in grupo["pagadores"]}
    assert nomes[str(atuais[0].pk)] == atuais[0].email
    assert nomes[str(atuais[1].pk)] == atuais[1].email
    assert nomes[str(atuais[0].pk)] != nomes[str(atuais[1].pk)]
    f.m["pagador"].delete()
    resposta = cliente(f.u["membro"]).get(url)
    assert resposta.status_code == 200
    grupo = next(g for g in resposta.json() if g["id"] == str(f.grupo.pk))
    assert str(atuais[1].pk) not in {p["id"] for p in grupo["pagadores"]}
    assert atuais[1].email not in str(grupo)
