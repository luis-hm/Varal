import uuid
from datetime import UTC, date, datetime
from unittest.mock import patch

import pytest
from django.db import IntegrityError, transaction

from apps.lancamentos.models import Lancamento
from apps.recorrencias.models import CompetenciaDevida, Recorrencia
from apps.recorrencias.servicos import processar_recorrencia, vencimento
from tests import test_contas
from tests.test_grupos import cliente, rodar_em_paralelo

contas_fixture = test_contas.f
pytestmark = pytest.mark.django_db


@pytest.fixture
def f(contas_fixture):
    return contas_fixture


@pytest.fixture
def agora():
    with patch("django.utils.timezone.now", return_value=datetime(2026, 11, 16, 15, 0, tzinfo=UTC)):
        yield


def criar(f, **extras):
    corpo = {
        "chave_idempotencia": str(uuid.uuid4()),
        "descricao": "Energia",
        "dia_vencimento": 31,
        "valor_tipo": "variavel",
        "valor_centavos": None,
        **extras,
    }
    response = cliente(f.u["membro"]).post(
        f"/api/espacos/{f.grupo.pk}/recorrencias/", corpo, content_type="application/json"
    )
    return response, corpo


def test_rn17_variavel_null_e_retry_idempotente(f, agora):
    resposta, corpo = criar(f)
    assert resposta.status_code == 201, resposta.content
    conta = resposta.json()["ocorrencia"]
    assert conta["status"] == "aguardando" and conta["valor_centavos"] is None
    assert conta["competencia"] == "2026-11-01" and conta["vencimento"] == "2026-11-30"
    retry = cliente(f.u["membro"]).post(
        f"/api/espacos/{f.grupo.pk}/recorrencias/", corpo, content_type="application/json"
    )
    assert retry.status_code == 200
    assert retry.json()["ocorrencia"]["id"] == conta["id"]
    assert Recorrencia.objects.count() == Lancamento.objects.count() == 1


def test_rn23_dias_curtos():
    assert vencimento(date(2025, 2, 1), 31) == date(2025, 2, 28)
    assert vencimento(date(2024, 2, 1), 31) == date(2024, 2, 29)
    assert vencimento(date(2026, 4, 1), 31) == date(2026, 4, 30)


def test_rn17_null_status_e_confirmacao_explicita(f, agora):
    resposta, _ = criar(f)
    conta = resposta.json()["ocorrencia"]
    c = cliente(f.u["membro"])
    url = f"/api/lancamentos/{conta['id']}/"
    assert c.patch(url, {"valor_centavos": 500}, content_type="application/json").status_code == 400
    assert (
        c.patch(
            url, {"valor_centavos": 500, "confirmar_chegada": True}, content_type="application/json"
        ).status_code
        == 200
    )
    assert c.get(url).json()["status"] == "pendente"
    with pytest.raises(IntegrityError), transaction.atomic():
        Lancamento.objects.filter(pk=conta["id"]).update(valor_centavos=None)


def test_rn17_catchup_pausa_retomada_sem_gerar_meses_pausados(f, agora):
    resposta, _ = criar(f)
    rid = resposta.json()["recorrencia"]["id"]
    c = cliente(f.u["membro"])
    with patch("django.utils.timezone.now", return_value=datetime(2027, 2, 2, 12, 0, tzinfo=UTC)):
        c = cliente(f.u["membro"])
        assert c.post(f"/api/recorrencias/{rid}/pausar/").status_code == 200
        processar_recorrencia(rid)
    with patch("django.utils.timezone.now", return_value=datetime(2027, 5, 2, 12, 0, tzinfo=UTC)):
        c = cliente(f.u["membro"])
        assert c.post(f"/api/recorrencias/{rid}/retomar/").status_code == 200
        processar_recorrencia(rid)
    meses = list(
        Lancamento.objects.filter(recorrencia_id=rid)
        .order_by("competencia")
        .values_list("competencia", flat=True)
    )
    assert meses == [
        date(2026, 11, 1),
        date(2026, 12, 1),
        date(2027, 1, 1),
        date(2027, 2, 1),
        date(2027, 5, 1),
    ]


def test_q08_9_primeira_conferida_variavel_sem_copia(f, agora):
    resposta, _ = criar(f, ocorrencia_inicial={"valor_centavos": 765, "vencimento": "2026-11-22"})
    assert resposta.status_code == 201, resposta.content
    assert resposta.json()["recorrencia"]["valor_centavos"] is None
    conta = resposta.json()["ocorrencia"]
    assert conta["valor_centavos"] == 765 and conta["status"] == "pendente"
    rid = resposta.json()["recorrencia"]["id"]
    with patch("django.utils.timezone.now", return_value=datetime(2026, 12, 1, 12, 0, tzinfo=UTC)):
        processar_recorrencia(rid)
    seguinte = Lancamento.objects.get(recorrencia_id=rid, competencia=date(2026, 12, 1))
    assert seguinte.status == "aguardando" and seguinte.valor_centavos is None
    assert not hasattr(seguinte, "instrumento")


def test_q08_9_mes_diferente_faz_rollback(f, agora):
    resposta, _ = criar(f, ocorrencia_inicial={"valor_centavos": 765, "vencimento": "2026-12-01"})
    assert resposta.status_code == 400
    assert not Recorrencia.objects.exists() and not Lancamento.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_rnf07_duas_execucoes_concorrentes_geram_uma(f, agora):
    resposta, _ = criar(f)
    rid = resposta.json()["recorrencia"]["id"]
    with patch("django.utils.timezone.now", return_value=datetime(2026, 12, 1, 12, 0, tzinfo=UTC)):
        resultados = rodar_em_paralelo(
            lambda: processar_recorrencia(rid), lambda: processar_recorrencia(rid)
        )
    assert resultados == [None, None]
    assert Lancamento.objects.filter(recorrencia_id=rid, competencia=date(2026, 12, 1)).count() == 1
    assert (
        CompetenciaDevida.objects.filter(
            recorrencia_id=rid, competencia=date(2026, 12, 1), estado="gerada"
        ).count()
        == 1
    )


@pytest.mark.parametrize("estado", ["pendente", "paga", "confirmada"])
def test_d08_1_status_fechado_ou_pendente_proibe_null(f, estado):
    conta = test_contas.nova(f.u["membro"], f.grupo)
    with pytest.raises(IntegrityError), transaction.atomic():
        Lancamento.objects.filter(pk=conta.pk).update(status=estado, valor_centavos=None)


def test_d08_1_aguardando_legado_positivo_preservado(f):
    conta = test_contas.nova(f.u["membro"], f.grupo)
    Lancamento.objects.filter(pk=conta.pk).update(status="aguardando")
    resposta = cliente(f.u["membro"]).patch(
        f"/api/lancamentos/{conta.pk}/", {"descricao": "Nova"}, content_type="application/json"
    )
    assert resposta.status_code == 200, resposta.content
    conta.refresh_from_db()
    assert conta.status == "aguardando" and conta.valor_centavos == 1000


def test_q08_9_primeiro_pdf_permanece_na_primeira_conta(f, agora):
    from apps.boletos.models import DocumentoBoleto

    pdf = DocumentoBoleto.objects.create(
        espaco=f.grupo,
        criado_por=f.u["membro"],
        estado="conferencia_manual",
        nome="boleto.pdf",
        tamanho=20,
        resultado={},
    )
    resposta, _ = criar(
        f,
        ocorrencia_inicial={
            "valor_centavos": 1000,
            "vencimento": "2026-11-23",
            "documento_pdf": str(pdf.pk),
        },
    )
    assert resposta.status_code == 201, resposta.content
    rid = resposta.json()["recorrencia"]["id"]
    pdf.refresh_from_db()
    assert str(pdf.lancamento_id) == resposta.json()["ocorrencia"]["id"] and pdf.vinculado_em
    with patch("django.utils.timezone.now", return_value=datetime(2026, 12, 2, 12, 0, tzinfo=UTC)):
        processar_recorrencia(rid)
    seguinte = Lancamento.objects.get(recorrencia_id=rid, competencia=date(2026, 12, 1))
    assert (
        seguinte.valor_centavos is None
        and not DocumentoBoleto.objects.filter(lancamento=seguinte).exists()
    )


def test_q08_3_proximos_rollback_quando_valor_diverge_codigo(f):
    from tests.test_boletos_parser import bancario

    with patch("django.utils.timezone.now", return_value=datetime(2025, 2, 15, 12, 0, tzinfo=UTC)):
        resposta, _ = criar(
            f,
            valor_tipo="fixo",
            valor_centavos=12345,
            ocorrencia_inicial={
                "valor_centavos": 12345,
                "vencimento": "2025-02-22",
                "instrumento": {"codigo": bancario(1000)},
            },
        )
        assert resposta.status_code == 201, resposta.content
        conta = resposta.json()["ocorrencia"]
        rid = resposta.json()["recorrencia"]["id"]
        c = cliente(f.u["membro"])
        resposta = c.patch(
            f"/api/lancamentos/{conta['id']}/",
            {"escopo": "proximos", "valor_centavos": 999},
            content_type="application/json",
        )
        assert resposta.status_code == 400
        assert Recorrencia.objects.get(pk=rid).valor_centavos == 12345
        assert Lancamento.objects.get(pk=conta["id"]).valor_centavos == 12345


def test_q08_6_arquivar_casa_preserva_invisiveis_e_futuro_sem_casa(f, agora):
    visivel, _ = criar(f, subgrupo=str(f.casa.pk))
    oculta, _ = criar(f, subgrupo=str(f.casa.pk), visibilidade="restrita")
    assert visivel.status_code == oculta.status_code == 201
    # The member created both models; grant admin access only to the first.
    aberto = Recorrencia.objects.get(pk=visivel.json()["recorrencia"]["id"])
    aberto.visibilidade = "grupo"
    aberto.save(update_fields=["visibilidade"])
    conta_oculta = Lancamento.objects.get(pk=oculta.json()["ocorrencia"]["id"])
    c = cliente(f.u["admin"])
    prefixo = f"/api/grupos/{f.grupo.pk}/subgrupos/{f.casa.pk}/"
    preview = c.get(prefixo + "arquivamento/").json()
    assert preview == {"contas_qtd": 1, "recorrencias_qtd": 1}
    assert (
        c.patch(
            prefixo, {"arquivado": True, "destino_subgrupo": None}, content_type="application/json"
        ).status_code
        == 200
    )
    conta_oculta.refresh_from_db()
    assert conta_oculta.subgrupo_id == f.casa.pk
    rid = oculta.json()["recorrencia"]["id"]
    assert Recorrencia.objects.get(pk=rid).subgrupo_id == f.casa.pk
    with patch("django.utils.timezone.now", return_value=datetime(2026, 12, 2, 12, 0, tzinfo=UTC)):
        processar_recorrencia(rid)
    futura = Lancamento.objects.get(recorrencia_id=rid, competencia=date(2026, 12, 1))
    assert futura.subgrupo_id is None
    assert c.get(f"/api/lancamentos/{futura.pk}/").status_code == 404


def test_q08_5_ausencia_audiencia_pausa_privada(f, agora):
    from apps.espacos import servicos as grupos
    from apps.lancamentos import servicos as contas

    resposta, _ = criar(f, visibilidade="restrita")
    rid = resposta.json()["recorrencia"]["id"]
    cid = resposta.json()["ocorrencia"]["id"]
    contas.cancelar(f.u["membro"], cid)
    grupos.sair(f.u["membro"], f.grupo)
    with patch("django.utils.timezone.now", return_value=datetime(2026, 12, 2, 12, 0, tzinfo=UTC)):
        processar_recorrencia(rid)
    modelo = Recorrencia.objects.get(pk=rid)
    assert modelo.estado == "pausada" and modelo.motivo_pausa == "sem_audiencia"
    assert modelo.competencias.get(competencia=date(2026, 12, 1)).estado == "bloqueada"
    assert cliente(f.u["admin"]).get(f"/api/recorrencias/{rid}/").status_code == 404
    assert not Lancamento.objects.filter(recorrencia=modelo, competencia=date(2026, 12, 1)).exists()


def test_q08_3_editar_e_cancelar_proximos_preserva_final(f, agora):
    resposta, _ = criar(f, valor_tipo="fixo", valor_centavos=1200)
    rid = resposta.json()["recorrencia"]["id"]
    cid = resposta.json()["ocorrencia"]["id"]
    with patch("django.utils.timezone.now", return_value=datetime(2027, 1, 2, 12, 0, tzinfo=UTC)):
        processar_recorrencia(rid)
        contas = list(Lancamento.objects.filter(recorrencia_id=rid).order_by("competencia"))
        Lancamento.objects.filter(pk=contas[1].pk).update(status="paga")
        c = cliente(f.u["membro"])
        alterada = c.patch(
            f"/api/lancamentos/{cid}/",
            {"escopo": "proximos", "descricao": "Conta revisada", "valor_centavos": 1800},
            content_type="application/json",
        )
        assert alterada.status_code == 200, alterada.content
        contas[0].refresh_from_db()
        contas[1].refresh_from_db()
        contas[2].refresh_from_db()
        assert contas[0].descricao == contas[2].descricao == "Conta revisada"
        assert contas[0].valor_centavos == contas[2].valor_centavos == 1800
        assert contas[1].descricao == "Energia" and contas[1].valor_centavos == 1200
        cancelada = c.post(
            f"/api/lancamentos/{cid}/cancelar/",
            {"escopo": "proximos"},
            content_type="application/json",
        )
        assert cancelada.status_code == 200, cancelada.content
        for conta in contas:
            conta.refresh_from_db()
        assert [conta.status for conta in contas] == ["cancelada", "paga", "cancelada"]
        assert Recorrencia.objects.get(pk=rid).estado == "encerrada"


def test_q08_1_somas_e_contagens_ignoram_cancelada_desconhecida(f, agora):
    ativa, _ = criar(f, subgrupo=str(f.casa.pk))
    cancelada, _ = criar(f, subgrupo=str(f.casa.pk))
    fixa, _ = criar(f, valor_tipo="fixo", valor_centavos=2000, subgrupo=str(f.casa.pk))
    assert ativa.status_code == cancelada.status_code == fixa.status_code == 201
    c = cliente(f.u["membro"])
    cid = cancelada.json()["ocorrencia"]["id"]
    assert c.post(f"/api/lancamentos/{cid}/cancelar/").status_code == 200
    corpo = c.get(f"/api/espacos/{f.grupo.pk}/resumo/").json()
    assert corpo["total_centavos"] == 2000 and corpo["valores_indefinidos_qtd"] == 1
    assert corpo["por_casa"][0]["total_centavos"] == 2000
    assert corpo["por_casa"][0]["valores_indefinidos_qtd"] == 1
    lista = c.get(f"/api/espacos/{f.grupo.pk}/lancamentos/").json()
    assert lista["total_centavos"] == 2000 and lista["valores_indefinidos_qtd"] == 1
    assert c.get(f"/api/lancamentos/{cid}/").json()["valor_centavos"] is None


@pytest.mark.django_db(transaction=True)
def test_cu04_concorrencia_renomear_e_arquivar_nao_reabre(f, agora):
    from apps.espacos import servicos as grupos

    c = cliente(f.u["admin"])
    caminho = f"/api/grupos/{f.grupo.pk}/subgrupos/{f.casa.pk}/"
    resultados = rodar_em_paralelo(
        lambda: grupos.arquivar_casa(f.u["admin"], f.grupo, f.casa.pk, None),
        lambda: c.patch(caminho, {"nome": "Casa nova"}, content_type="application/json"),
    )
    assert not isinstance(resultados[0], Exception), resultados
    assert resultados[1].status_code == 200
    f.casa.refresh_from_db()
    assert f.casa.arquivado and f.casa.nome == "Casa nova"


@pytest.mark.django_db(transaction=True)
def test_rn32_concorrencia_geracao_e_saida_sem_orfa(f, agora):
    from apps.espacos import servicos as grupos
    from apps.espacos.acesso import quem_ve

    resposta, _ = criar(f, visibilidade="restrita")
    rid = resposta.json()["recorrencia"]["id"]
    with patch("django.utils.timezone.now", return_value=datetime(2026, 12, 2, 12, 0, tzinfo=UTC)):
        resultados = rodar_em_paralelo(
            lambda: processar_recorrencia(rid),
            lambda: grupos.remover_membro(f.grupo, f.m["membro"].pk),
        )
    assert resultados == [None, None]
    for conta in Lancamento.objects.filter(
        recorrencia_id=rid, status__in=["aguardando", "pendente"]
    ):
        assert quem_ve(conta)
    assert cliente(f.u["admin"]).get(f"/api/recorrencias/{rid}/").status_code == 404


def test_rn06_conta_visivel_nao_revela_modelo_invisivel(f, agora):
    resposta, _ = criar(f, visibilidade="restrita")
    rid = resposta.json()["recorrencia"]["id"]
    conta = Lancamento.objects.get(pk=resposta.json()["ocorrencia"]["id"])
    conta.acesso.add(f.u["admin"])
    c = cliente(f.u["admin"])
    detalhe = c.get(f"/api/lancamentos/{conta.pk}/")
    assert detalhe.status_code == 200
    assert detalhe.json()["recorrente"] is True
    assert detalhe.json()["recorrencia_id"] is None
    assert detalhe.json()["pode_ver_recorrencia"] is False
    assert rid not in detalhe.content.decode()
    assert c.get(f"/api/recorrencias/{rid}/").status_code == 404


def test_q08_10_reingresso_recupera_autoria_mas_nao_grant_antigo(f, agora):
    from apps.espacos import servicos as grupos
    from apps.espacos.models import Membro
    from apps.lancamentos import servicos as contas

    resposta, _ = criar(
        f,
        visibilidade="restrita",
        pagador=str(f.u["membro"].pk),
        acesso=[str(f.u["observador"].pk)],
    )
    rid = resposta.json()["recorrencia"]["id"]
    cid = resposta.json()["ocorrencia"]["id"]
    contas.cancelar(f.u["membro"], cid)
    grupos.sair(f.u["observador"], f.grupo)
    grupos.sair(f.u["membro"], f.grupo)
    modelo = Recorrencia.objects.get(pk=rid)
    assert modelo.pagador_id is None and not modelo.acesso.filter(pk=f.u["observador"].pk).exists()
    with patch("django.utils.timezone.now", return_value=datetime(2026, 12, 2, 12, 0, tzinfo=UTC)):
        processar_recorrencia(rid)
        modelo.refresh_from_db()
        assert modelo.estado == "pausada" and modelo.motivo_pausa == "sem_audiencia"
        Membro.objects.create(espaco=f.grupo, usuario=f.u["membro"], papel="membro")
        Membro.objects.create(espaco=f.grupo, usuario=f.u["observador"], papel="membro")
        assert cliente(f.u["observador"]).get(f"/api/recorrencias/{rid}/").status_code == 404
        c = cliente(f.u["membro"])
        assert c.get(f"/api/recorrencias/{rid}/").status_code == 200
        assert c.post(f"/api/recorrencias/{rid}/retomar/").status_code == 200
        modelo.refresh_from_db()
        assert modelo.estado == "ativa"


def test_rn22_criacao_automatica_de_recorrencia_identifica_sistema(f, agora):
    resposta, _ = criar(f)
    assert resposta.status_code == 201, resposta.content
    conta_id = resposta.json()["ocorrencia"]["id"]
    detalhe = cliente(f.u["membro"]).get(f"/api/lancamentos/{conta_id}/")
    assert detalhe.status_code == 200
    criacao = next(item for item in detalhe.json()["historico"] if item["acao"] == "criada")
    assert criacao["automatica"] is True
    assert criacao["autor"] is None
    assert criacao["sou_eu"] is False
    assert criacao["dados"] == {"competencia": "2026-11-01"}


def test_rn22_criacao_manual_autor_excluido_permanece_ex_membro(f):
    conta = test_contas.nova(f.u["membro"], f.grupo)
    f.u["membro"].delete()
    detalhe = cliente(f.u["admin"]).get(f"/api/lancamentos/{conta.pk}/")
    assert detalhe.status_code == 200
    criacao = next(item for item in detalhe.json()["historico"] if item["acao"] == "criada")
    assert criacao["automatica"] is False
    assert criacao["autor"] == "Ex-membro"
    assert criacao["sou_eu"] is False
    assert criacao["dados"] == {}
