"""Regressions for evidence expiry, recovery and isolated execution (Etapa 07)."""

import io
import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.db import transaction
from django.utils import timezone
from PIL import Image

from apps.pagamentos.models import DocumentoComprovante, LimpezaComprovante
from apps.pagamentos.storage import spool
from apps.pagamentos.tasks import (
    limpar_expirados,
    processar_comprovante,
    recuperar_limpeza,
    validar_isolado,
)
from tests import test_pagamentos as base
from tests.test_grupos import cliente

f = base.f
contas_fixture = base.contas_fixture
pytestmark = pytest.mark.django_db


def documento(f, conta, **campos):
    return DocumentoComprovante.objects.create(
        lancamento=conta,
        criado_por=f.u["membro"],
        versao=0,
        estado="valido",
        nome="sintetico.png",
        tamanho=10,
        mime="image/png",
        **campos,
    )


def test_rnf03_rn15_draft_expirado_nao_pode_ser_lido_assinado_ou_vinculado(f):
    conta = base.criar(f)
    doc = documento(f, conta)
    DocumentoComprovante.objects.filter(pk=doc.pk).update(
        criado_em=timezone.now() - timedelta(hours=25)
    )
    c = cliente(f.u["membro"])
    assert c.get(f"/api/comprovantes/{doc.pk}/").status_code == 404
    assert c.get(f"/api/comprovantes/{doc.pk}/arquivo/").status_code == 404
    assert base.pagar(f, conta, comprovante_id=str(doc.pk)).status_code == 409
    conta.refresh_from_db()
    assert conta.status == "pendente" and not conta.pagamentos.exists()
    doc.refresh_from_db()
    assert doc.pagamento_id is None and doc.vinculado_em is None


@pytest.mark.django_db(transaction=True)
def test_rn22_rn29_rollback_preserva_documento_e_recupera_broker_storage(f, settings, tmp_path):
    settings.PDF_SPOOL_DIR = str(tmp_path)
    conta = base.criar(f)
    doc = documento(f, conta)
    arquivo = spool(doc.pk)
    arquivo.parent.mkdir(parents=True)
    arquivo.write_bytes(b"original-sintetico")
    pk = doc.pk
    with patch(
        "apps.pagamentos.tasks.recuperar_limpeza.delay", side_effect=OSError("broker indisponivel")
    ):
        with pytest.raises(RuntimeError), transaction.atomic():
            doc.delete()
            raise RuntimeError("rollback")
        assert DocumentoComprovante.objects.filter(pk=pk).exists()
        assert not LimpezaComprovante.objects.filter(pk=pk).exists()
        assert arquivo.exists()
        DocumentoComprovante.objects.get(pk=pk).delete()
    assert LimpezaComprovante.objects.filter(pk=pk).exists()
    with patch("apps.pagamentos.tasks.armazenamento") as storage:
        storage.return_value.delete.side_effect = OSError("storage indisponivel")
        recuperar_limpeza.run()
        assert LimpezaComprovante.objects.filter(pk=pk).exists() and arquivo.exists()
        storage.return_value.delete.side_effect = None
        recuperar_limpeza.run()
        storage.return_value.delete.assert_called_with(f"comprovantes/{pk}")
    assert not LimpezaComprovante.objects.filter(pk=pk).exists() and not arquivo.exists()


def test_rnf06_tentativa_antiga_nao_sobrescreve_nova_nem_apaga_vivo(f, settings, tmp_path):
    settings.PDF_SPOOL_DIR = str(tmp_path)
    conta = base.criar(f)
    doc = DocumentoComprovante.objects.create(
        lancamento=conta, criado_por=f.u["membro"], versao=0, nome="teste.png", tamanho=10
    )
    arquivo = spool(doc.pk)
    arquivo.parent.mkdir(parents=True)
    arquivo.write_bytes(b"sintetico")
    nova = uuid.uuid4()

    def substituir(_data):
        DocumentoComprovante.objects.filter(pk=doc.pk).update(
            estado="valido", tentativa=nova, mime="image/png"
        )
        return "image/png"

    with (
        patch("apps.pagamentos.tasks.validar_isolado", side_effect=substituir),
        patch("apps.pagamentos.tasks.armazenamento") as storage,
    ):
        processar_comprovante.run(str(doc.pk))
        storage.return_value.save.assert_not_called()
    doc.refresh_from_db()
    assert doc.estado == "valido" and doc.tentativa == nova
    assert not LimpezaComprovante.objects.filter(pk=doc.pk).exists()


def test_rnf06_validacao_isolada_limita_tempo_e_memoria(settings):
    raw = io.BytesIO()
    Image.new("RGB", (32, 32), "green").save(raw, format="PNG")
    settings.PDF_EXTRACAO_TIMEOUT = 0.000001
    assert validar_isolado(raw.getvalue()) == ""
    settings.PDF_EXTRACAO_TIMEOUT = 10
    settings.PDF_EXTRACAO_MEMORIA = 1024 * 1024
    assert validar_isolado(raw.getvalue()) == ""


def test_rn29_expiracao_remove_draft_mas_nao_documento_vinculado(f):
    conta = base.criar(f)
    draft = documento(f, conta)
    assert base.pagar(f, conta).status_code == 201
    pagamento = conta.pagamentos.get()
    vinculado = documento(f, conta, pagamento=pagamento, vinculado_em=timezone.now())
    antes = timezone.now() - timedelta(hours=25)
    DocumentoComprovante.objects.filter(pk__in=[draft.pk, vinculado.pk]).update(criado_em=antes)
    with patch("apps.pagamentos.tasks.agendar"):
        limpar_expirados.run()
    assert not DocumentoComprovante.objects.filter(pk=draft.pk).exists()
    assert DocumentoComprovante.objects.filter(pk=vinculado.pk, pagamento=pagamento).exists()
    assert LimpezaComprovante.objects.filter(pk=draft.pk).exists()
    assert not LimpezaComprovante.objects.filter(pk=vinculado.pk).exists()
