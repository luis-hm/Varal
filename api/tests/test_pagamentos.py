import io
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image
from reportlab.pdfgen import canvas

from apps.espacos.models import Membro
from apps.lancamentos.models import Historico
from apps.pagamentos.models import DocumentoComprovante, EventoPagamento, Pagamento
from apps.pagamentos.tasks import validar_isolado
from tests import test_contas
from tests.test_grupos import cliente

contas_fixture = test_contas.f
pytestmark = pytest.mark.django_db


@pytest.fixture
def f(contas_fixture):
    return contas_fixture


def criar(f, **kwargs):
    return test_contas.nova(f.u["membro"], f.grupo, **kwargs)


def pagar(f, conta, nome="membro", **kwargs):
    dados = {
        "pago_em": timezone.localdate().isoformat(),
        "valor_centavos_esperado": conta.valor_centavos,
        **kwargs,
    }
    return cliente(f.u[nome]).post(
        f"/api/lancamentos/{conta.pk}/pagamentos/", dados, content_type="application/json"
    )


def desfazer(f, conta, pagamento, nome="membro"):
    return cliente(f.u[nome]).post(
        f"/api/lancamentos/{conta.pk}/pagamentos/{pagamento.pk}/desfazer/",
        {},
        content_type="application/json",
    )


def test_rn14_rn22_pagamento_e_evento_atomicos(f):
    conta = criar(f)
    resp = pagar(f, conta)
    assert resp.status_code == 201, resp.content
    pagamento = Pagamento.objects.get(lancamento=conta)
    assert pagamento.valor_pago_centavos == 1000
    assert (
        EventoPagamento.objects.filter(pagamento=pagamento, destinatario=conta.criador).count() == 1
    )
    assert resp.json()["pagamento_ativo"]["id"] == str(pagamento.pk)
    assert pagar(f, conta).status_code == 409
    assert Historico.objects.filter(lancamento=conta, acao="paga").count() == 1


def test_rn14_valor_data_e_edicao_com_marca(f):
    conta = criar(f)
    assert (
        pagar(f, conta, pago_em=(timezone.localdate() + timedelta(days=1)).isoformat()).status_code
        == 400
    )
    assert pagar(f, conta, valor_centavos_esperado=999).status_code == 409
    assert not Pagamento.objects.exists()
    assert pagar(f, conta).status_code == 201
    url = f"/api/lancamentos/{conta.pk}/"
    assert (
        cliente(f.u["membro"])
        .patch(url, {"valor_centavos": 999}, content_type="application/json")
        .status_code
        == 409
    )
    assert (
        cliente(f.u["membro"])
        .patch(url, {"valor_centavos": 1000}, content_type="application/json")
        .status_code
        == 200
    )


def test_rn16_autor_observador_pode_desfazer_sem_pagar(f):
    conta = criar(f)
    assert pagar(f, conta).status_code == 201
    pagamento = Pagamento.objects.get(lancamento=conta)
    Membro.objects.filter(espaco=f.grupo, usuario=f.u["membro"]).update(papel="observador")
    assert desfazer(f, conta, pagamento).status_code == 200
    assert desfazer(f, conta, pagamento).status_code == 409
    assert pagar(f, conta).status_code == 403


def test_rn01_rn05_endpoint_nao_vaza_conta(f, settings, tmp_path):
    settings.PDF_SPOOL_DIR = str(tmp_path)
    conta = criar(f, visibilidade="restrita", acesso=[])
    assert pagar(f, conta, nome="fora").status_code == 404
    assert pagar(f, conta, nome="admin").status_code == 404
    assert (
        cliente(f.u["fora"])
        .post(
            f"/api/lancamentos/{conta.pk}/comprovantes/",
            {"arquivo": SimpleUploadedFile("x.png", b"x")},
        )
        .status_code
        == 404
    )
    assert pagar(f, conta).status_code == 201
    pagamento = Pagamento.objects.get(lancamento=conta)
    assert desfazer(f, conta, pagamento, nome="admin").status_code == 404


def test_rf16_rn15_retencao_historica_e_draft_antigo(f):
    conta = criar(f)
    doc = DocumentoComprovante.objects.create(
        lancamento=conta,
        criado_por=f.u["membro"],
        versao=0,
        estado="valido",
        nome="foto.png",
        tamanho=20,
        mime="image/png",
    )
    assert pagar(f, conta, comprovante_id=str(doc.pk)).status_code == 201
    pagamento = Pagamento.objects.get(lancamento=conta)
    assert desfazer(f, conta, pagamento).status_code == 200
    doc.refresh_from_db()
    assert doc.pagamento_id == pagamento.pk and doc.vinculado_em
    assert cliente(f.u["observador"]).get(f"/api/comprovantes/{doc.pk}/").status_code == 200
    assert cliente(f.u["fora"]).get(f"/api/comprovantes/{doc.pk}/").status_code == 404
    antigo = DocumentoComprovante.objects.create(
        lancamento=conta,
        criado_por=f.u["membro"],
        versao=0,
        estado="valido",
        nome="a.png",
        tamanho=10,
        mime="image/png",
    )
    assert pagar(f, conta, comprovante_id=str(antigo.pk)).status_code == 409
    detalhe = cliente(f.u["membro"]).get(f"/api/lancamentos/{conta.pk}/").json()
    assert detalhe["pagamentos"][0]["comprovante_id"] == str(doc.pk)


def test_rf16_imagem_e_pdf_validados_em_processo():
    png = io.BytesIO()
    Image.new("RGB", (5, 5), "red").save(png, format="PNG")
    pdf = io.BytesIO()
    documento = canvas.Canvas(pdf)
    documento.drawString(10, 10, "comprovante")
    documento.save()
    assert validar_isolado(png.getvalue()) == "image/png"
    assert validar_isolado(pdf.getvalue()) == "application/pdf"
    assert validar_isolado(b"%PDF-invalido") == ""
    assert validar_isolado(png.getvalue()[:-8]) == ""


@pytest.mark.django_db(transaction=True)
def test_rf15_rn22_concorrencia_duas_marcacoes(f):
    from apps.pagamentos import servicos
    from tests.test_grupos import rodar_em_paralelo

    conta = criar(f)
    dados = {"pago_em": timezone.localdate(), "valor_centavos_esperado": 1000}
    resultados = rodar_em_paralelo(
        lambda: servicos.marcar(f.u["membro"], conta.pk, dados),
        lambda: servicos.marcar(f.u["admin"], conta.pk, dados),
    )
    assert sum(isinstance(r, tuple) for r in resultados) == 1
    assert Pagamento.objects.filter(lancamento=conta, desfeito_em__isnull=True).count() == 1
    assert EventoPagamento.objects.filter(pagamento__lancamento=conta).count() == 1
    assert Historico.objects.filter(lancamento=conta, acao="paga").count() == 1


@pytest.mark.django_db(transaction=True)
def test_rn16_concorrencia_dois_undos(f):
    from apps.pagamentos import servicos
    from tests.test_grupos import rodar_em_paralelo

    conta = criar(f)
    _, pagamento = servicos.marcar(
        f.u["membro"], conta.pk, {"pago_em": timezone.localdate(), "valor_centavos_esperado": 1000}
    )
    resultados = rodar_em_paralelo(
        lambda: servicos.desfazer(f.u["membro"], conta.pk, pagamento.pk),
        lambda: servicos.desfazer(f.u["admin"], conta.pk, pagamento.pk),
    )
    assert sum(not isinstance(r, Exception) for r in resultados) == 1
    assert Historico.objects.filter(lancamento=conta, acao="pagamento_desfeito").count() == 1


def test_rn06_arquivos_e_escritas_respeitam_visibilidade(f):
    from apps.pagamentos import servicos

    conta = criar(f, visibilidade="restrita", acesso=[])
    _, pagamento = servicos.marcar(
        f.u["membro"], conta.pk, {"pago_em": timezone.localdate(), "valor_centavos_esperado": 1000}
    )
    doc = DocumentoComprovante.objects.create(
        lancamento=conta,
        pagamento=pagamento,
        criado_por=f.u["membro"],
        versao=0,
        vinculado_em=timezone.now(),
        estado="valido",
        nome="x.png",
        tamanho=10,
        mime="image/png",
    )
    c = cliente(f.u["admin"])
    assert c.get(f"/api/comprovantes/{doc.pk}/").status_code == 404
    assert c.get(f"/api/comprovantes/{doc.pk}/arquivo/").status_code == 404
    assert (
        c.post(
            f"/api/lancamentos/{conta.pk}/pagamentos/{pagamento.pk}/comprovante/",
            {"comprovante_id": str(doc.pk)},
            content_type="application/json",
        ).status_code
        == 404
    )
    assert (
        c.post(
            f"/api/lancamentos/{conta.pk}/pagamentos/{pagamento.pk}/desfazer/",
            {},
            content_type="application/json",
        ).status_code
        == 404
    )


def test_rf16_rnf06_worker_preserva_original_e_mime(f, tmp_path, settings):
    from apps.pagamentos.storage import spool
    from apps.pagamentos.tasks import processar_comprovante

    settings.PDF_SPOOL_DIR = str(tmp_path)
    conta = criar(f)
    doc = DocumentoComprovante.objects.create(
        lancamento=conta, criado_por=f.u["membro"], versao=0, nome="imagem.png", tamanho=100
    )
    conteudo = io.BytesIO()
    Image.new("RGB", (8, 8)).save(conteudo, format="PNG")
    path = spool(doc.pk)
    path.parent.mkdir(parents=True)
    path.write_bytes(conteudo.getvalue())
    with patch("apps.pagamentos.tasks.armazenamento") as storage:
        processar_comprovante.run(str(doc.pk))
    doc.refresh_from_db()
    assert doc.estado == "valido" and doc.mime == "image/png"
    arquivo = storage.return_value.save.call_args.args[1]
    assert arquivo.read() == conteudo.getvalue() and arquivo.content_type == "image/png"
    assert not path.exists()
    conta.refresh_from_db()
    assert conta.status == "pendente"


@pytest.mark.django_db(transaction=True)
def test_rn15_upload_tardio_concorrente_com_undo(f):
    from apps.pagamentos import servicos
    from tests.test_grupos import rodar_em_paralelo

    conta = criar(f)
    _, pagamento = servicos.marcar(
        f.u["membro"], conta.pk, {"pago_em": timezone.localdate(), "valor_centavos_esperado": 1000}
    )
    conta.refresh_from_db()
    doc = DocumentoComprovante.objects.create(
        lancamento=conta,
        criado_por=f.u["membro"],
        pagamento_alvo=pagamento,
        versao=conta.versao_pagamento,
        estado="valido",
        nome="x.png",
        tamanho=5,
        mime="image/png",
    )
    resultados = rodar_em_paralelo(
        lambda: servicos.anexar(f.u["membro"], conta.pk, pagamento.pk, doc.pk),
        lambda: servicos.desfazer(f.u["membro"], conta.pk, pagamento.pk),
    )
    assert not isinstance(resultados[1], Exception)
    conta.refresh_from_db()
    pagamento.refresh_from_db()
    doc.refresh_from_db()
    assert conta.status == "pendente" and pagamento.desfeito_em
    assert doc.pagamento_id in (None, pagamento.pk)
    if doc.pagamento_id:
        assert doc.vinculado_em
    assert not Pagamento.objects.filter(lancamento=conta, desfeito_em__isnull=True).exists()


@pytest.mark.django_db(transaction=True)
def test_rn21_pagamento_concorrente_com_saida(f):
    from apps.espacos import servicos as grupos
    from apps.pagamentos import servicos
    from tests.test_grupos import rodar_em_paralelo

    conta = criar(f, pagador=f.u["membro"].pk)
    resultados = rodar_em_paralelo(
        lambda: servicos.marcar(
            f.u["membro"],
            conta.pk,
            {"pago_em": timezone.localdate(), "valor_centavos_esperado": 1000},
        ),
        lambda: grupos.sair(f.u["membro"], f.grupo),
    )
    assert resultados[1] is None
    conta.refresh_from_db()
    if conta.status == "pendente":
        assert not Pagamento.objects.filter(lancamento=conta).exists()
        assert conta.pagador_id is None
    else:
        assert conta.status == "paga"
        assert Pagamento.objects.filter(lancamento=conta, desfeito_em__isnull=True).count() == 1


def test_rnf11_rn14_data_civil_perto_da_virada_utc(f):
    from datetime import UTC, datetime

    conta = criar(f)
    with patch("django.utils.timezone.now", return_value=datetime(2026, 11, 16, 2, 30, tzinfo=UTC)):
        url = f"/api/lancamentos/{conta.pk}/pagamentos/"
        c = cliente(f.u["membro"])
        assert (
            c.post(
                url, {"valor_centavos_esperado": 1000}, content_type="application/json"
            ).status_code
            == 400
        )
        assert (
            c.post(
                url,
                {"pago_em": "2026-11-16", "valor_centavos_esperado": 1000},
                content_type="application/json",
            ).status_code
            == 400
        )
        assert not Pagamento.objects.filter(lancamento=conta).exists()
        assert (
            c.post(
                url,
                {"pago_em": "2026-11-15", "valor_centavos_esperado": 1000},
                content_type="application/json",
            ).status_code
            == 201
        )


def test_rn06_pagador_com_acesso_explicito_nao_paga_de_outro(f):
    Membro.objects.filter(pk=f.m["pagador"].pk).update(papel="membro")
    conta = criar(f, visibilidade="restrita", pagador=f.u["membro"].pk, acesso=[f.u["pagador"].pk])
    from apps.espacos import servicos as grupos

    grupos.alterar_papel(f.grupo, f.m["pagador"].pk, "pagador")
    c = cliente(f.u["pagador"])
    assert c.get(f"/api/lancamentos/{conta.pk}/").status_code == 200
    assert pagar(f, conta, nome="pagador").status_code == 403
    assert (
        c.post(
            f"/api/lancamentos/{conta.pk}/comprovantes/",
            {"arquivo": SimpleUploadedFile("x.png", b"x")},
        ).status_code
        == 403
    )


def test_rn06_comprovante_historico_revoga_acesso(f):
    from apps.pagamentos import servicos

    conta = criar(f, visibilidade="restrita", acesso=[f.u["observador"].pk])
    _, pagamento = servicos.marcar(
        f.u["membro"], conta.pk, {"pago_em": timezone.localdate(), "valor_centavos_esperado": 1000}
    )
    doc = DocumentoComprovante.objects.create(
        lancamento=conta,
        pagamento=pagamento,
        criado_por=f.u["membro"],
        versao=0,
        vinculado_em=timezone.now(),
        estado="valido",
        nome="x.png",
        tamanho=10,
        mime="image/png",
    )
    servicos.desfazer(f.u["membro"], conta.pk, pagamento.pk)
    c = cliente(f.u["observador"])
    assert c.get(f"/api/comprovantes/{doc.pk}/").status_code == 200
    conta.acesso.clear()
    assert c.get(f"/api/comprovantes/{doc.pk}/").status_code == 404
    assert c.get(f"/api/comprovantes/{doc.pk}/arquivo/").status_code == 404


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("com_comprovante", [False, True])
def test_rn06_detalhe_fechado_trava_papel_ate_serializar(f, com_comprovante):
    import threading

    from django.db import connection

    from apps.espacos import servicos as grupos
    from apps.lancamentos.views import ContaDetalheSerializer
    from apps.pagamentos import servicos

    conta = test_contas.nova(f.u["admin"], f.grupo, pagador=f.u["admin"].pk)
    _, pagamento = servicos.marcar(
        f.u["admin"], conta.pk, {"pago_em": timezone.localdate(), "valor_centavos_esperado": 1000}
    )
    if com_comprovante:
        DocumentoComprovante.objects.create(
            lancamento=conta,
            pagamento=pagamento,
            criado_por=f.u["admin"],
            versao=0,
            vinculado_em=timezone.now(),
            estado="valido",
            nome="x.png",
            tamanho=10,
            mime="image/png",
        )
        conta.status = "confirmada"
        conta.save(update_fields=["status"])
    iniciou = threading.Event()
    liberar = threading.Event()
    mudou = threading.Event()
    saida = []
    metodo_original = ContaDetalheSerializer.get_pagamento_ativo

    def pausar(serializer, obj):
        iniciou.set()
        assert liberar.wait(8)
        return metodo_original(serializer, obj)

    def ler():
        try:
            saida.append(cliente(f.u["membro"]).get(f"/api/lancamentos/{conta.pk}/").status_code)
        finally:
            connection.close()

    def mudar():
        try:
            grupos.alterar_papel(f.grupo, f.m["membro"].pk, "pagador")
            mudou.set()
        finally:
            connection.close()

    with patch.object(ContaDetalheSerializer, "get_pagamento_ativo", pausar):
        leitura = threading.Thread(target=ler)
        leitura.start()
        assert iniciou.wait(8)
        alteracao = threading.Thread(target=mudar)
        alteracao.start()
        try:
            assert not mudou.wait(0.4)
        finally:
            liberar.set()
            leitura.join(8)
            alteracao.join(8)
    assert saida == [200] and mudou.is_set()
    assert cliente(f.u["membro"]).get(f"/api/lancamentos/{conta.pk}/").status_code == 404


def test_q07_7_resumo_atribuicao_e_visibilidade(f):
    from datetime import UTC, datetime

    with patch("django.utils.timezone.now", return_value=datetime(2026, 11, 15, 15, 0, tzinfo=UTC)):
        paga = criar(f, pagador=f.u["membro"].pk, subgrupo=f.casa.pk)
        criar(f, pagador=f.u["membro"].pk, subgrupo=f.casa.pk)
        oculta = test_contas.nova(
            f.u["admin"],
            f.grupo,
            visibilidade="restrita",
            pagador=f.u["admin"].pk,
            subgrupo=f.casa.pk,
        )
        assert pagar(f, paga).status_code == 201
        assert pagar(f, oculta, nome="admin").status_code == 201
        c = cliente(f.u["membro"])
        resumo = c.get(f"/api/espacos/{f.grupo.pk}/resumo/").json()
        assert (resumo["qtd"], resumo["pagas_qtd"]) == (2, 1)
        assert (resumo["por_casa"][0]["qtd"], resumo["por_casa"][0]["pagas_qtd"]) == (2, 1)
        membros = c.get(f"/api/grupos/{f.grupo.pk}/").json()["membros"]
        membro = next(m for m in membros if m["usuario"] == str(f.u["membro"].pk))
        assert membro["contas_atribuidas_qtd"] == 2
