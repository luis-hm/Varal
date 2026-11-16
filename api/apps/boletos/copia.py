"""Private PDF retention and copy primitives; caller owns domain authorization."""

import hashlib
import uuid
from dataclasses import dataclass

from django.conf import settings
from django.db import connection, transaction

from .models import DocumentoBoleto, PinPDF, TentativaCopiaPDF
from .storage import armazenamento, chave, cliente
from .tasks import _travar_objeto, intencao_limpeza

LIMITE = 5 * 1024 * 1024


class ObjetoOcupado(Exception):
    """Retry the whole domain transaction without waiting for storage I/O."""


class CopiaIndisponivel(Exception):
    """The capability is absent, revoked, incomplete, or the object is invalid."""


@dataclass(frozen=True)
class CopiaVerificada:
    documento_id: uuid.UUID
    tamanho: int
    sha256: str


def _try_travar_objeto(pk):
    numero = uuid.UUID(str(pk)).int >> 64
    if numero >= 2**63:
        numero -= 2**64
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_try_advisory_xact_lock(%s)", [numero])
        return cursor.fetchone()[0]


def _exigir_atomic():
    if not connection.in_atomic_block:
        raise RuntimeError("A domain transaction is required")


def fixar_fonte(documento_id, reserva_id):
    _exigir_atomic()
    # Caller locks and validates domain rows before this terminal operational lock.
    if not _try_travar_objeto(documento_id):
        raise ObjetoOcupado()
    doc = DocumentoBoleto.objects.filter(
        pk=documento_id, estado__in=("lido", "conferencia_manual")
    ).first()
    if not doc:
        raise CopiaIndisponivel()
    pin, created = PinPDF.objects.get_or_create(
        reserva_id=reserva_id, defaults={"documento_id": documento_id, "tamanho": doc.tamanho}
    )
    if not created and str(pin.documento_id) != str(documento_id):
        raise CopiaIndisponivel()
    return pin.documento_id


def liberar_fonte(reserva_id):
    _exigir_atomic()
    pin = PinPDF.objects.filter(reserva_id=reserva_id).first()
    if pin:
        pin.delete()
        intencao_limpeza(pin.documento_id)


def preparar_copia(reserva_id, tentativa_id, documento_id):
    _exigir_atomic()
    if not PinPDF.objects.filter(reserva_id=reserva_id, documento_id=documento_id).exists():
        raise CopiaIndisponivel()
    tentativa, created = TentativaCopiaPDF.objects.get_or_create(
        pk=tentativa_id, defaults={"reserva_id": reserva_id, "fonte_id": documento_id}
    )
    if not created and (
        str(tentativa.reserva_id) != str(reserva_id)
        or str(tentativa.fonte_id) != str(documento_id)
        or tentativa.estado != "ativa"
    ):
        raise CopiaIndisponivel()
    if created:
        intencao_limpeza(tentativa.destino_id)
    return tentativa.destino_id


def _ler_limitado(arquivo):
    data = arquivo.read(LIMITE + 1)
    if not data or len(data) > LIMITE or not data.startswith(b"%PDF-"):
        raise CopiaIndisponivel()
    return data


def copiar_verificada(reserva_id, tentativa_id):
    if connection.in_atomic_block:
        raise RuntimeError("Copy must run outside any transaction")
    tentativa = TentativaCopiaPDF.objects.filter(
        pk=tentativa_id, reserva_id=reserva_id, estado="ativa"
    ).first()
    pin = (
        PinPDF.objects.filter(reserva_id=reserva_id, documento_id=tentativa.fonte_id).first()
        if tentativa
        else None
    )
    if not tentativa or not pin:
        raise CopiaIndisponivel()
    if not TentativaCopiaPDF.objects.filter(
        pk=tentativa_id, reserva_id=reserva_id, estado="ativa"
    ).update(estado="copiando"):
        raise CopiaIndisponivel()
    with armazenamento().open(chave(tentativa.fonte_id), "rb") as origem:
        data = _ler_limitado(origem)
    if len(data) != pin.tamanho:
        raise CopiaIndisponivel()
    digest = hashlib.sha256(data).hexdigest()
    with transaction.atomic():
        _travar_objeto(tentativa.destino_id)
        if not TentativaCopiaPDF.objects.filter(
            pk=tentativa_id, reserva_id=reserva_id, estado="copiando"
        ).exists():
            raise CopiaIndisponivel()
        cliente().put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=chave(tentativa.destino_id),
            Body=data,
            ContentType="application/pdf",
        )
        with armazenamento().open(chave(tentativa.destino_id), "rb") as destino:
            recebido = _ler_limitado(destino)
        if len(recebido) != len(data) or hashlib.sha256(recebido).hexdigest() != digest:
            raise CopiaIndisponivel()
    # The mutex has fully left the outer transaction before any domain publication.
    updated = TentativaCopiaPDF.objects.filter(
        pk=tentativa_id, reserva_id=reserva_id, estado="copiando"
    ).update(estado="verificada", tamanho=len(data), sha256=digest, incerta=False)
    if not updated:
        raise CopiaIndisponivel()
    return CopiaVerificada(tentativa.destino_id, len(data), digest)


def publicar_copia(reserva_id, tentativa_id):
    _exigir_atomic()
    tentativa = TentativaCopiaPDF.objects.filter(
        pk=tentativa_id, reserva_id=reserva_id, estado="verificada"
    ).first()
    if not tentativa or not TentativaCopiaPDF.objects.filter(
        pk=tentativa_id, reserva_id=reserva_id, estado="verificada"
    ).update(estado="publicada"):
        raise CopiaIndisponivel()
    return tentativa.destino_id


def abandonar_copia(reserva_id, tentativa_id):
    _exigir_atomic()
    tentativa = TentativaCopiaPDF.objects.filter(
        pk=tentativa_id, reserva_id=reserva_id, estado__in=("ativa", "copiando", "verificada")
    ).first()
    if tentativa and TentativaCopiaPDF.objects.filter(
        pk=tentativa_id, reserva_id=reserva_id, estado__in=("ativa", "copiando", "verificada")
    ).update(estado="abandonada"):
        intencao_limpeza(tentativa.destino_id)
