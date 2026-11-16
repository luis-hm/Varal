"""Synthetic PDFs and private object lifecycle for CA04/CA05."""

import hashlib
import io
import threading
import uuid
from unittest.mock import patch

import pytest
from django.db import transaction

from apps.boletos.copia import (
    CopiaIndisponivel,
    abandonar_copia,
    copiar_verificada,
    fixar_fonte,
    liberar_fonte,
    preparar_copia,
    publicar_copia,
)
from apps.boletos.models import DocumentoBoleto, LimpezaPDF, PinPDF
from apps.boletos.storage import chave
from apps.boletos.tasks import recuperar_limpeza
from apps.espacos.models import Espaco

pytestmark = pytest.mark.django_db(transaction=True)
PDF = b"%PDF-1.4\nsynthetic\n%%EOF"


class Objetos:
    def __init__(self):
        self.data = {}

    def open(self, key, mode):
        return io.BytesIO(self.data[key])

    def put_object(self, *, Bucket, Key, Body, ContentType):
        self.data[Key] = Body

    def delete(self, key):
        self.data.pop(key, None)


@pytest.fixture
def fonte():
    espaco = Espaco.objects.create(tipo="grupo", nome="Sintético")
    return DocumentoBoleto.objects.create(
        espaco=espaco, estado="lido", nome="teste.pdf", tamanho=len(PDF)
    )


def test_ca04_pin_sobrevive_exclusao_e_copia_integra(fonte, settings, tmp_path):
    settings.PDF_SPOOL_DIR = str(tmp_path)
    fonte_id = fonte.pk
    objetos = Objetos()
    objetos.data[chave(fonte_id)] = PDF
    reserva, tentativa = uuid.uuid4(), uuid.uuid4()
    with (
        patch("apps.boletos.tasks.agendar"),
        patch("apps.boletos.tasks.armazenamento", return_value=objetos),
        patch("apps.boletos.copia.armazenamento", return_value=objetos),
        patch("apps.boletos.copia.cliente", return_value=objetos),
    ):
        with transaction.atomic():
            fixar_fonte(fonte_id, reserva)
            destino = preparar_copia(reserva, tentativa, fonte_id)
        fonte.espaco.delete()
        recuperar_limpeza.run()
        assert objetos.data[chave(fonte_id)] == PDF
        assert LimpezaPDF.objects.filter(pk=fonte_id).exists()
        copia = copiar_verificada(reserva, tentativa)
        assert (copia.documento_id, copia.tamanho, copia.sha256) == (
            destino,
            len(PDF),
            hashlib.sha256(PDF).hexdigest(),
        )
        with transaction.atomic():
            assert publicar_copia(reserva, tentativa) == destino
            grupo = Espaco.objects.create(tipo="grupo", nome="Destino")
            DocumentoBoleto.objects.create(
                id=destino,
                espaco=grupo,
                estado="lido",
                nome="teste.pdf",
                tamanho=len(PDF),
            )
            liberar_fonte(reserva)
        recuperar_limpeza.run()
        assert chave(fonte_id) not in objetos.data
        assert objetos.data[chave(destino)] == PDF


def test_ca05_rollback_e_token_abandonado_nao_publica(fonte):
    reserva, tentativa = uuid.uuid4(), uuid.uuid4()
    with patch("apps.boletos.tasks.agendar"):
        with pytest.raises(ValueError), transaction.atomic():
            fixar_fonte(fonte.pk, reserva)
            raise ValueError()
        assert not PinPDF.objects.filter(reserva_id=reserva).exists()
        with transaction.atomic():
            fixar_fonte(fonte.pk, reserva)
            preparar_copia(reserva, tentativa, fonte.pk)
            abandonar_copia(reserva, tentativa)
        with pytest.raises(CopiaIndisponivel):
            copiar_verificada(reserva, tentativa)
        with pytest.raises(CopiaIndisponivel), transaction.atomic():
            publicar_copia(reserva, tentativa)


def test_ca04_pin_ocupado_reverte_reserva(fonte):
    from apps.boletos.copia import ObjetoOcupado

    reserva = uuid.uuid4()
    with patch("apps.boletos.copia._try_travar_objeto", return_value=False):
        with pytest.raises(ObjetoOcupado), transaction.atomic():
            fixar_fonte(fonte.pk, reserva)
    assert not PinPDF.objects.filter(reserva_id=reserva).exists()


def test_ca04_mutex_real_recusa_reserva_sem_esperar(fonte):
    from django.db import close_old_connections

    from apps.boletos.copia import ObjetoOcupado
    from apps.boletos.tasks import _travar_objeto

    bloqueado, liberar = threading.Event(), threading.Event()

    def segurar():
        close_old_connections()
        try:
            with transaction.atomic():
                _travar_objeto(fonte.pk)
                bloqueado.set()
                assert liberar.wait(5)
        finally:
            close_old_connections()

    worker = threading.Thread(target=segurar)
    worker.start()
    try:
        assert bloqueado.wait(5)
        with pytest.raises(ObjetoOcupado), transaction.atomic():
            fixar_fonte(fonte.pk, uuid.uuid4())
    finally:
        liberar.set()
        worker.join(timeout=5)
    assert not worker.is_alive()


def test_ca05_cancelamento_durante_put_conserva_tombstone(fonte, settings, tmp_path):
    from django.db import close_old_connections

    settings.PDF_SPOOL_DIR = str(tmp_path)
    reserva, tentativa = uuid.uuid4(), uuid.uuid4()
    objetos = Objetos()
    objetos.data[chave(fonte.pk)] = PDF
    erros = []

    def put_cancelado(**kwargs):
        def cancelar():
            close_old_connections()
            try:
                with transaction.atomic():
                    abandonar_copia(reserva, tentativa)
            except Exception as erro:
                erros.append(erro)
            finally:
                close_old_connections()

        worker = threading.Thread(target=cancelar)
        worker.start()
        worker.join(timeout=5)
        assert not worker.is_alive()
        assert not erros
        objetos.data[kwargs["Key"]] = kwargs["Body"]

    objetos.put_object = put_cancelado
    with (
        patch("apps.boletos.tasks.agendar"),
        patch("apps.boletos.tasks.armazenamento", return_value=objetos),
        patch("apps.boletos.copia.armazenamento", return_value=objetos),
        patch("apps.boletos.copia.cliente", return_value=objetos),
    ):
        with transaction.atomic():
            fixar_fonte(fonte.pk, reserva)
            destino = preparar_copia(reserva, tentativa, fonte.pk)
        with pytest.raises(CopiaIndisponivel):
            copiar_verificada(reserva, tentativa)
        recuperar_limpeza.run()
        assert chave(destino) not in objetos.data
        assert LimpezaPDF.objects.filter(pk=destino).exists()


def test_ca05_limpeza_nao_descarta_intencao_renovada(fonte, settings, tmp_path):
    from apps.boletos.tasks import intencao_limpeza

    settings.PDF_SPOOL_DIR = str(tmp_path)
    fonte_id = fonte.pk
    with patch("apps.boletos.tasks.agendar"):
        fonte.delete()
        antes = LimpezaPDF.objects.get(pk=fonte_id).geracao
        objetos = Objetos()
        original = objetos.delete

        def renovada(key):
            original(key)
            intencao_limpeza(fonte_id)

        objetos.delete = renovada
        with patch("apps.boletos.tasks.armazenamento", return_value=objetos):
            recuperar_limpeza.run()
        assert LimpezaPDF.objects.get(pk=fonte_id).geracao > antes


def test_ca05_clientes_s3_escrita_sem_retry_automatico():
    from django.core.files.storage import storages

    from apps.boletos.storage import cliente

    # Config after botocore normalizes the number of retries, with no S3 request.
    assert cliente().meta.config.retries["total_max_attempts"] == 1
    for alias in ("pdf", "comprovantes"):
        storage = storages[alias]
        assert storage.connection.meta.client.meta.config.retries["total_max_attempts"] == 1
        # PDF uploads (maximum 5 MiB) take the single-PUT path in s3transfer.
        if alias == "pdf":
            assert storage.transfer_config.multipart_threshold > 5 * 1024 * 1024
