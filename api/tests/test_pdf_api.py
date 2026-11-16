from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from apps.boletos.models import DocumentoBoleto, Instrumento
from apps.boletos.tasks import extrair_isolado
from tests import test_contas
from tests.test_boletos_parser import bancario
from tests.test_contas import cliente, lista_url

pytestmark = pytest.mark.django_db
contas_fixture = test_contas.f
relogio_fixture = test_contas.relogio


@pytest.fixture
def f(contas_fixture):
    return contas_fixture


def upload(f, user="membro", content=b"%PDF-fake", **kwargs):
    arq = SimpleUploadedFile("boleto.pdf", content, content_type="application/pdf")
    return cliente(f.u[user]).post(
        f"/api/espacos/{f.grupo.pk}/boletos/pdf/", {"arquivo": arq, **kwargs}
    )


def test_rnf06_upload_spool_sem_s3(f, settings, tmp_path):
    settings.PDF_SPOOL_DIR = str(tmp_path)
    with (
        patch("apps.boletos.tasks.agendar") as agendar,
        patch("apps.boletos.tasks.armazenamento") as s3,
    ):
        response = upload(f)
    assert response.status_code == 202
    doc = DocumentoBoleto.objects.get(pk=response.json()["id"])
    assert doc.lancamento_id is None and doc.estado == "pendente"
    assert (tmp_path / f"{doc.pk}.pdf").read_bytes() == b"%PDF-fake"
    assert not s3.called and not agendar.called  # test transaction has not committed


def test_rn25_upload_limite_e_formato(f, settings, tmp_path):
    settings.PDF_SPOOL_DIR = str(tmp_path)
    assert upload(f, content=b"nao pdf").status_code == 400
    assert upload(f, content=b"%PDF-" + b"a" * (5 * 1024 * 1024)).status_code == 400
    assert not DocumentoBoleto.objects.exists()


def test_rn01_rn06_draft_privado_e_vinculo(f):
    doc = DocumentoBoleto.objects.create(
        espaco=f.grupo,
        criado_por=f.u["membro"],
        estado="conferencia_manual",
        nome="a.pdf",
        tamanho=12,
    )
    assert cliente(f.u["admin"]).get(f"/api/boletos/pdfs/{doc.pk}/").status_code == 404
    dados = {
        "descricao": "Conta",
        "valor_centavos": 12345,
        "vencimento": "2025-02-22",
        "documento_pdf": str(doc.pk),
    }
    resp = cliente(f.u["membro"]).post(lista_url(f.grupo), dados, content_type="application/json")
    assert resp.status_code == 201, resp.content
    doc.refresh_from_db()
    assert doc.lancamento_id and doc.vinculado_em
    assert Instrumento.objects.get(lancamento_id=doc.lancamento_id).tipo == "manual"
    assert cliente(f.u["admin"]).get(f"/api/boletos/pdfs/{doc.pk}/").status_code == 200


def test_rn27_pdf_codigo_nao_pode_ser_ignorado(f):
    doc = DocumentoBoleto.objects.create(
        espaco=f.grupo,
        criado_por=f.u["membro"],
        estado="lido",
        nome="a.pdf",
        tamanho=12,
        resultado={"candidatos": [{"codigo": bancario(1000)}]},
    )
    dados = {
        "descricao": "Conta",
        "valor_centavos": 12345,
        "vencimento": "2025-02-22",
        "documento_pdf": str(doc.pk),
    }
    resp = cliente(f.u["membro"]).post(lista_url(f.grupo), dados, content_type="application/json")
    assert resp.status_code == 400
    doc.refresh_from_db()
    assert doc.lancamento_id is None


def test_rnf01_upload_exige_csrf(f, settings, tmp_path):
    settings.PDF_SPOOL_DIR = str(tmp_path)
    client = Client(enforce_csrf_checks=True)
    client.force_login(f.u["membro"])
    arq = SimpleUploadedFile("boleto.pdf", b"%PDF-fake", content_type="application/pdf")
    assert (
        client.post(f"/api/espacos/{f.grupo.pk}/boletos/pdf/", {"arquivo": arq}).status_code == 403
    )


def test_rnf06_processo_isolado_timeout(settings):
    settings.PDF_EXTRACAO_TIMEOUT = 0.00001
    assert extrair_isolado(b"%PDF-fake")["estado"] == "conferencia_manual"


def test_rnf07_tentativa_antiga_nao_apaga_documento_vivo(f, settings, tmp_path):
    import uuid

    from apps.boletos.models import LimpezaPDF
    from apps.boletos.tasks import processar_pdf

    settings.PDF_SPOOL_DIR = str(tmp_path)
    doc = DocumentoBoleto.objects.create(
        espaco=f.grupo, criado_por=f.u["membro"], nome="a.pdf", tamanho=9
    )
    (tmp_path / f"{doc.pk}.pdf").write_bytes(b"%PDF-fake")

    def outra_tentativa(*args, **kwargs):
        DocumentoBoleto.objects.filter(pk=doc.pk).update(
            estado="lido", tentativa=uuid.uuid4(), resultado={"candidatos": []}
        )

    with (
        patch("apps.boletos.tasks.armazenamento") as storage,
        patch(
            "apps.boletos.tasks.extrair_isolado", return_value={"estado": "invalido", "avisos": []}
        ),
    ):
        storage.return_value.save.side_effect = outra_tentativa
        processar_pdf.run(str(doc.pk))
    doc.refresh_from_db()
    assert doc.estado == "lido"
    assert not LimpezaPDF.objects.filter(pk=doc.pk).exists()


def test_rn27_pdf_recusa_codigo_de_outra_cobranca(f):
    doc = DocumentoBoleto.objects.create(
        espaco=f.grupo,
        criado_por=f.u["membro"],
        estado="lido",
        nome="a.pdf",
        tamanho=12,
        resultado={"candidatos": [{"codigo": bancario(1000)}]},
    )
    dados = {
        "descricao": "Conta",
        "valor_centavos": 12345,
        "vencimento": "2025-02-22",
        "documento_pdf": str(doc.pk),
        "instrumento": {"codigo": bancario(1001)},
    }
    resposta = cliente(f.u["membro"]).post(
        lista_url(f.grupo), dados, content_type="application/json"
    )
    assert resposta.status_code == 400
    doc.refresh_from_db()
    assert not doc.lancamento_id


def test_rn01_rn06_rn29_rotas_negam_outro_usuario_e_draft_expirado(f):
    from datetime import timedelta

    from django.utils import timezone

    doc = DocumentoBoleto.objects.create(
        espaco=f.grupo,
        criado_por=f.u["membro"],
        estado="conferencia_manual",
        nome="a.pdf",
        tamanho=12,
    )
    conta = test_contas.nova(f.u["membro"], f.grupo, visibilidade="restrita")
    base = f"/api/boletos/pdfs/{doc.pk}/"
    for user in ("admin", "fora"):
        c = cliente(f.u[user])
        assert c.get(base).status_code == 404
        assert c.get(base + "arquivo/").status_code == 404
        assert c.get(f"/api/lancamentos/{conta.pk}/pdf/").status_code == 404
        dados = {
            "descricao": "Conta",
            "valor_centavos": 1,
            "vencimento": "2026-11-20",
            "documento_pdf": str(doc.pk),
        }
        assert c.post(lista_url(f.grupo), dados, content_type="application/json").status_code == 404
    DocumentoBoleto.objects.filter(pk=doc.pk).update(criado_em=timezone.now() - timedelta(hours=25))
    c = cliente(f.u["membro"])
    assert c.get(base).status_code == 404
    assert c.get(base + "arquivo/").status_code == 404
    dados = {
        "descricao": "Conta",
        "valor_centavos": 1,
        "vencimento": "2026-11-20",
        "documento_pdf": str(doc.pk),
    }
    assert c.post(lista_url(f.grupo), dados, content_type="application/json").status_code == 404


def test_rn06_vinculo_sem_backdoor_apos_uploader_perder_acesso(f):
    from django.utils import timezone

    from apps.espacos.models import Membro

    conta = test_contas.nova(f.u["admin"], f.grupo)
    doc = DocumentoBoleto.objects.create(
        espaco=f.grupo,
        criado_por=f.u["membro"],
        lancamento=conta,
        vinculado_em=timezone.now(),
        estado="conferencia_manual",
        nome="a.pdf",
        tamanho=12,
    )
    Membro.objects.filter(espaco=f.grupo, usuario=f.u["membro"]).delete()
    dono = cliente(f.u["membro"])
    assert dono.get(f"/api/boletos/pdfs/{doc.pk}/").status_code == 404
    assert dono.get(f"/api/boletos/pdfs/{doc.pk}/arquivo/").status_code == 404
    assert dono.get(f"/api/lancamentos/{conta.pk}/pdf/").status_code == 404
    with patch("apps.boletos.storage.cliente") as s3:
        s3.return_value.generate_presigned_url.return_value = "http://storage.local/assinada"
        observador = cliente(f.u["observador"])
        assert observador.get(f"/api/boletos/pdfs/{doc.pk}/").status_code == 200
        assert observador.get(f"/api/boletos/pdfs/{doc.pk}/arquivo/").status_code == 200
        assert observador.get(f"/api/lancamentos/{conta.pk}/pdf/").status_code == 200


def test_rn29_rollback_preserva_arquivo_e_limpeza_e_recupera_falha(f, settings, tmp_path):
    from django.db import transaction
    from django.utils import timezone

    from apps.boletos.models import LimpezaPDF
    from apps.boletos.tasks import recuperar_limpeza

    settings.PDF_SPOOL_DIR = str(tmp_path)
    conta = test_contas.nova(f.u["admin"], f.grupo)
    doc = DocumentoBoleto.objects.create(
        espaco=f.grupo,
        criado_por=f.u["admin"],
        lancamento=conta,
        vinculado_em=timezone.now(),
        estado="lido",
        nome="a.pdf",
        tamanho=12,
    )
    doc_id = doc.pk
    arquivo = tmp_path / f"{doc_id}.pdf"
    arquivo.write_bytes(b"conteudo")
    with patch("apps.boletos.tasks.agendar") as agendar:
        with pytest.raises(RuntimeError), transaction.atomic():
            doc.delete()
            raise RuntimeError("rollback")
        assert DocumentoBoleto.objects.filter(pk=doc_id).exists()
        assert not LimpezaPDF.objects.filter(pk=doc_id).exists()
        assert arquivo.exists() and not agendar.called
        DocumentoBoleto.objects.get(pk=doc_id).delete()
        assert LimpezaPDF.objects.filter(pk=doc_id).exists()
        with patch("apps.boletos.tasks.armazenamento") as storage:
            storage.return_value.delete.side_effect = OSError("indisponivel")
            recuperar_limpeza.run()
            assert LimpezaPDF.objects.filter(pk=doc_id).exists() and arquivo.exists()
            storage.return_value.delete.side_effect = None
            recuperar_limpeza.run()
        assert not LimpezaPDF.objects.filter(pk=doc_id).exists()
        assert not arquivo.exists()


@pytest.mark.parametrize("modo", ["memoria", "saida"])
def test_rnf06_limites_reais_subprocesso(settings, tmp_path, monkeypatch, modo):
    import os
    import shutil
    import subprocess
    import sys
    import tempfile
    from pathlib import Path

    package = tmp_path / "apps" / "boletos"
    package.mkdir(parents=True)
    (tmp_path / "apps" / "__init__.py").touch()
    (package / "__init__.py").touch()
    runner = Path(__file__).resolve().parents[1] / "apps" / "boletos" / "pdf_runner.py"
    shutil.copyfile(runner, package / "pdf_runner.py")
    payload = "'x' * (1024 * 1024 * 1024)" if modo == "memoria" else "'x' * (256 * 1024)"
    (package / "pdf.py").write_text(
        "from dataclasses import dataclass\n@dataclass\nclass R:\n"
        "    estado: str\n    beneficiario: str\n"
        "def extrair_pdf(data):\n    open('executou', 'w').close()\n"
        f"    return R('lido', {payload})\n"
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PYTHONPATH", str(tmp_path) + os.pathsep + os.environ.get("PYTHONPATH", ""))
    settings.PDF_EXTRACAO_MEMORIA = 64 * 1024 * 1024 if modo == "memoria" else 512 * 1024 * 1024
    with tempfile.TemporaryFile() as saida:
        filho = subprocess.run(
            [sys.executable, "-m", "apps.boletos.pdf_runner", str(settings.PDF_EXTRACAO_MEMORIA)],
            input=b"%PDF-fake",
            stdout=saida,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
        assert filho.returncode != 0
        assert (tmp_path / "executou").exists()
        if modo == "saida":
            assert saida.tell() == 128 * 1024
    result = extrair_isolado(b"%PDF-fake")
    assert result["estado"] == "conferencia_manual"
    assert result["candidatos"] == []


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("modo", ["saida", "remocao"])
def test_rn01_upload_revalida_permissao_apos_desligamento_concorrente(f, settings, tmp_path, modo):
    import threading

    from django.db import connection

    from apps.espacos import acesso, servicos

    settings.PDF_SPOOL_DIR = str(tmp_path)
    validou, continuar = threading.Event(), threading.Event()
    real = acesso.espaco_ou_404
    resultado = {}

    def acesso_pausado(*args, **kwargs):
        espaco = real(*args, **kwargs)
        if threading.current_thread().name == "upload" and not validou.is_set():
            validou.set()
            assert continuar.wait(10)
        return espaco

    def enviar():
        try:
            resultado["resposta"] = upload(f).status_code
        except Exception as exc:  # noqa: BLE001
            resultado["erro"] = exc
        finally:
            connection.close()

    with patch("apps.espacos.acesso.espaco_ou_404", acesso_pausado):
        thread = threading.Thread(target=enviar, name="upload")
        thread.start()
        assert validou.wait(10)
        if modo == "saida":
            servicos.sair(f.u["membro"], f.grupo)
        else:
            servicos.remover_membro(f.grupo, f.m["membro"].pk, por=f.u["admin"])
        continuar.set()
        thread.join(10)
    assert not thread.is_alive()
    assert resultado == {"resposta": 404}, resultado
    assert not DocumentoBoleto.objects.exists()
    assert list(tmp_path.iterdir()) == []


def test_rn01_upload_negado_a_usuario_externo_e_observador(f, settings, tmp_path):
    settings.PDF_SPOOL_DIR = str(tmp_path)
    assert upload(f, user="fora").status_code == 404
    assert upload(f, user="observador").status_code == 403
    assert not DocumentoBoleto.objects.exists()
    assert list(tmp_path.iterdir()) == []


def test_rn22_pdf_patch_identico_e_valor_normalizado_nao_gera_historico(f):
    from datetime import date

    from django.utils import timezone

    from apps.lancamentos.models import Historico

    conta = test_contas.nova(f.u["admin"], f.grupo)
    doc = DocumentoBoleto.objects.create(
        espaco=f.grupo,
        criado_por=f.u["admin"],
        lancamento=conta,
        vinculado_em=timezone.now(),
        estado="conferencia_manual",
        nome="a.pdf",
        tamanho=12,
    )
    Instrumento.objects.create(
        lancamento=conta, tipo="manual", beneficiario="Empresa", data_emissao=date(2026, 11, 1)
    )
    historicos = Historico.objects.filter(lancamento=conta).count()
    atualizado = conta.atualizado_em
    response = cliente(f.u["admin"]).patch(
        f"/api/lancamentos/{conta.pk}/",
        {"documento_pdf": str(doc.pk), "data_emissao": "2026-11-01", "beneficiario": "  Empresa  "},
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    conta.refresh_from_db()
    assert Historico.objects.filter(lancamento=conta).count() == historicos
    assert conta.atualizado_em == atualizado
    instrumento = Instrumento.objects.get(lancamento=conta)
    assert instrumento.beneficiario == "Empresa" and instrumento.data_emissao == date(2026, 11, 1)


def test_rn22_metadados_pdf_alterados_geram_um_historico_sem_texto(f):
    from django.utils import timezone

    from apps.lancamentos.models import Historico

    conta = test_contas.nova(f.u["admin"], f.grupo)
    doc = DocumentoBoleto.objects.create(
        espaco=f.grupo,
        criado_por=f.u["admin"],
        lancamento=conta,
        vinculado_em=timezone.now(),
        estado="conferencia_manual",
        nome="a.pdf",
        tamanho=12,
    )
    Instrumento.objects.create(lancamento=conta, tipo="manual", beneficiario="Anterior")
    resposta = cliente(f.u["admin"]).patch(
        f"/api/lancamentos/{conta.pk}/",
        {"beneficiario": "Novo", "documento_pdf": str(doc.pk)},
        content_type="application/json",
    )
    assert resposta.status_code == 200, resposta.content
    assert Instrumento.objects.get(lancamento=conta).beneficiario == "Novo"
    historico = Historico.objects.filter(lancamento=conta).last()
    assert historico.dados == {"metadados_pdf_alterados": True}


def test_rn22_metadado_ignorado_por_beneficiario_pix_nao_gera_historico(f):
    from django.utils import timezone

    from apps.lancamentos.models import Historico
    from tests.test_boletos_parser import STATIC

    conta = test_contas.nova(f.u["admin"], f.grupo)
    DocumentoBoleto.objects.create(
        espaco=f.grupo,
        criado_por=f.u["admin"],
        lancamento=conta,
        vinculado_em=timezone.now(),
        estado="conferencia_manual",
        nome="a.pdf",
        tamanho=12,
    )
    from apps.boletos.serializers import dados_instrumento, ler_entrada

    dados = dados_instrumento(ler_entrada({"codigo": STATIC}))
    Instrumento.objects.create(lancamento=conta, **dados)
    assert dados["beneficiario"]
    historicos = Historico.objects.filter(lancamento=conta).count()
    resposta = cliente(f.u["admin"]).patch(
        f"/api/lancamentos/{conta.pk}/",
        {"beneficiario": "Texto divergente"},
        content_type="application/json",
    )
    assert resposta.status_code == 200, resposta.content
    assert Instrumento.objects.get(lancamento=conta).beneficiario == dados["beneficiario"]
    assert Historico.objects.filter(lancamento=conta).count() == historicos
