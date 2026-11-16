"""Workers never modify bills and never expose document contents in logs."""

import json
import subprocess
import sys
import tempfile
import uuid
from datetime import date, timedelta

from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import connection, transaction
from django.utils import timezone

from .models import DocumentoBoleto, LimpezaPDF
from .storage import armazenamento, chave, spool

MANUAL = {
    "estado": "conferencia_manual",
    "candidatos": [],
    "avisos": ["Não foi possível ler o PDF; confira manualmente."],
}


def _validar(value, depth=0):
    if depth > 8:
        return False
    if value is None or type(value) in (bool, int):
        return True
    if isinstance(value, str):
        try:
            return (
                len(value) <= 4096
                and "\x00" not in value
                and bool(value.encode("utf-8") or not value)
            )
        except UnicodeError:
            return False
    if isinstance(value, list):
        return len(value) <= 100 and all(_validar(v, depth + 1) for v in value)
    if isinstance(value, dict):
        return len(value) <= 30 and all(
            _validar(k, depth + 1) and _validar(v, depth + 1) for k, v in value.items()
        )
    return False


def _resultado_valido(value):
    if not isinstance(value, dict) or not _validar(value):
        return False
    if value.get("estado") not in ("lido", "conferencia_manual", "invalido"):
        return False
    if set(value) - {
        "estado",
        "candidatos",
        "valor_centavos",
        "vencimento",
        "data_emissao",
        "beneficiario",
        "valor_textual_centavos",
        "vencimento_textual",
        "avisos",
    }:
        return False

    def data_valida(v):
        if v is None:
            return True
        try:
            return isinstance(v, str) and date.fromisoformat(v).isoformat() == v
        except ValueError:
            return False

    if any(
        not data_valida(value.get(k)) for k in ("vencimento", "data_emissao", "vencimento_textual")
    ):
        return False
    if any(
        value.get(k) is not None
        and (type(value[k]) is not int or not 0 < value[k] <= 99_999_999_999)
        for k in ("valor_centavos", "valor_textual_centavos")
    ):
        return False
    beneficiario = value.get("beneficiario")
    if beneficiario is not None and (not isinstance(beneficiario, str) or len(beneficiario) > 200):
        return False
    avisos = value.get("avisos", [])
    if (
        not isinstance(avisos, list)
        or len(avisos) > 20
        or any(not isinstance(a, str) or len(a) > 500 for a in avisos)
    ):
        return False
    candidatos = value.get("candidatos", [])
    if not isinstance(candidatos, list) or len(candidatos) > 100:
        return False
    from .parser import ErroValidacao, ler

    for candidato in candidatos:
        if not isinstance(candidato, dict) or set(candidato) != {
            "tipo",
            "codigo",
            "valor_centavos",
            "vencimento",
            "vencimentos_possiveis",
            "avisos",
        }:
            return False
        try:
            parsed = ler(codigo=candidato["codigo"])
        except (ErroValidacao, TypeError, ValueError):
            return False
        if (
            parsed.tipo not in ("boleto_bancario", "boleto_arrecadacao")
            or candidato["tipo"] != parsed.tipo
            or candidato["codigo"] != parsed.codigo
            or candidato["valor_centavos"] != parsed.valor_centavos
            or candidato["vencimento"]
            != (parsed.vencimento.isoformat() if parsed.vencimento else None)
            or candidato["vencimentos_possiveis"]
            != [d.isoformat() for d in parsed.vencimentos_possiveis]
            or candidato["avisos"] != list(parsed.avisos)
        ):
            return False
    return True


def extrair_isolado(data):
    try:
        with tempfile.TemporaryFile() as output:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "apps.boletos.pdf_runner",
                    str(settings.PDF_EXTRACAO_MEMORIA),
                ],
                input=data,
                stdout=output,
                stderr=subprocess.DEVNULL,
                timeout=settings.PDF_EXTRACAO_TIMEOUT,
                check=True,
            )
            output.seek(0)
            parsed = json.loads(output.read(128 * 1024 + 1))
        if not _resultado_valido(parsed):
            return MANUAL.copy()
        return parsed
    except (subprocess.SubprocessError, ValueError, OSError):
        return MANUAL.copy()


def _travar_objeto(pk):
    # Stable operational mutex; no bill/document row is locked while doing S3 I/O.
    numero = uuid.UUID(str(pk)).int >> 64
    if numero >= 2**63:
        numero -= 2**64
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [numero])


def intencao_limpeza(pk):
    # Serialize a late PUT against cleanup completion on the same immutable key.
    with transaction.atomic():
        LimpezaPDF.objects.select_for_update().get_or_create(pk=pk)
        transaction.on_commit(lambda: agendar(recuperar_limpeza))


def agendar(task, *args):
    # The database remains the source of retry if broker publication fails.
    try:
        task.delay(*args)
    except Exception:
        pass


@shared_task(bind=True, max_retries=3, default_retry_delay=30, time_limit=90)
def processar_pdf(self, documento_id):
    with transaction.atomic():
        doc = DocumentoBoleto.objects.select_for_update().filter(pk=documento_id).first()
        if not doc or doc.estado != "pendente":
            return
        tentativa = uuid.uuid4()
        doc.tentativa = tentativa
        doc.estado = "lendo"
        doc.lido_em = timezone.now()
        doc.save(update_fields=["estado", "lido_em", "tentativa"])
    try:
        path = spool(doc.pk)
        data = path.read_bytes()
        with transaction.atomic():
            _travar_objeto(doc.pk)
            if not DocumentoBoleto.objects.filter(
                pk=doc.pk, estado="lendo", tentativa=tentativa
            ).exists():
                return
            armazenamento().save(chave(doc.pk), ContentFile(data))
        result = extrair_isolado(data)
    except Exception:
        changed = DocumentoBoleto.objects.filter(
            pk=doc.pk, estado="lendo", tentativa=tentativa
        ).update(estado="pendente")
        if not changed:
            if not DocumentoBoleto.objects.filter(pk=doc.pk).exists():
                intencao_limpeza(doc.pk)
            return
        raise self.retry(exc=None) from None
    with transaction.atomic():
        doc = (
            DocumentoBoleto.objects.select_for_update()
            .filter(pk=documento_id, estado="lendo", tentativa=tentativa)
            .first()
        )
        if not doc:
            if not DocumentoBoleto.objects.filter(pk=documento_id).exists():
                intencao_limpeza(documento_id)
            return
        doc.estado = result.pop("estado")
        doc.avisos = result.pop("avisos", [])
        doc.resultado = result
        doc.lido_em = timezone.now()
        doc.save(update_fields=["estado", "avisos", "resultado", "lido_em"])
    path.unlink(missing_ok=True)


@shared_task
def recuperar_limpeza():
    for pk in LimpezaPDF.objects.values_list("pk", flat=True).iterator():
        try:
            with transaction.atomic():
                item = LimpezaPDF.objects.select_for_update().filter(pk=pk).first()
                if not item:
                    continue
                _travar_objeto(pk)
                armazenamento().delete(chave(pk))
                spool(pk).unlink(missing_ok=True)
                item.delete()
        except Exception:
            continue


@shared_task
def limpar_pdfs_expirados():
    with transaction.atomic():
        docs = DocumentoBoleto.objects.select_for_update().filter(
            lancamento__isnull=True,
            vinculado_em__isnull=True,
            criado_em__lt=timezone.now() - timedelta(hours=24),
        )
        for doc in docs:
            LimpezaPDF.objects.get_or_create(pk=doc.pk)
            doc.delete()
        transaction.on_commit(lambda: agendar(recuperar_limpeza))
