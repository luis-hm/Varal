import subprocess
import sys
import uuid
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.boletos.tasks import _travar_objeto, agendar
from apps.solicitacoes.coordenacao import barreira

from .models import DocumentoComprovante, LimpezaComprovante
from .storage import armazenamento, chave, spool


def validar_isolado(data):
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "apps.pagamentos.validar_arquivo",
                str(settings.PDF_EXTRACAO_MEMORIA),
            ],
            input=data,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=settings.PDF_EXTRACAO_TIMEOUT,
            check=True,
        )
        mime = result.stdout.decode("ascii").strip()
        return mime if mime in ("application/pdf", "image/png", "image/jpeg") else ""
    except (OSError, ValueError, subprocess.SubprocessError):
        return ""


def intencao_limpeza(pk):
    with transaction.atomic():
        item, criado = LimpezaComprovante.objects.select_for_update().get_or_create(pk=pk)
        if not criado:
            LimpezaComprovante.objects.filter(pk=item.pk).update(geracao=F("geracao") + 1)
        transaction.on_commit(lambda: agendar(recuperar_limpeza))


@shared_task(bind=True, max_retries=3, default_retry_delay=30, time_limit=90)
def processar_comprovante(self, documento_id):
    with transaction.atomic():
        barreira()
        doc = (
            DocumentoComprovante.objects.select_for_update()
            .filter(pk=documento_id, estado="pendente")
            .first()
        )
        if not doc:
            return
        tentativa = uuid.uuid4()
        doc.tentativa, doc.estado, doc.lido_em = tentativa, "lendo", timezone.now()
        doc.save(update_fields=["tentativa", "estado", "lido_em"])
    path = spool(doc.pk)
    try:
        data = path.read_bytes()
        mime = validar_isolado(data)
        if mime:
            tinha_intencao = LimpezaComprovante.objects.filter(pk=doc.pk).exists()
            intencao_limpeza(doc.pk)
            previa = LimpezaComprovante.objects.get(pk=doc.pk)
            ja_incerta = previa.incerta
            LimpezaComprovante.objects.filter(pk=doc.pk).update(incerta=True)
            with transaction.atomic():
                _travar_objeto(doc.pk)
                if not DocumentoComprovante.objects.filter(
                    pk=doc.pk, estado="lendo", tentativa=tentativa
                ).exists():
                    if not tinha_intencao and not ja_incerta:
                        LimpezaComprovante.objects.filter(
                            pk=doc.pk, geracao=previa.geracao
                        ).delete()
                    return
                content = ContentFile(data)
                content.content_type = mime
                armazenamento().save(chave(doc.pk), content)
            if not ja_incerta:
                LimpezaComprovante.objects.filter(pk=doc.pk, geracao=previa.geracao).update(
                    incerta=False
                )
                if not tinha_intencao:
                    LimpezaComprovante.objects.filter(pk=doc.pk, geracao=previa.geracao).delete()
    except Exception:
        with transaction.atomic():
            barreira()
            changed = DocumentoComprovante.objects.filter(
                pk=doc.pk, estado="lendo", tentativa=tentativa
            ).update(estado="pendente")
            esgotado = self.request.retries >= self.max_retries
            if changed and esgotado:
                DocumentoComprovante.objects.filter(
                    pk=doc.pk, estado="pendente", tentativa=tentativa
                ).update(estado="erro")
        if changed:
            if esgotado:
                return
            raise self.retry(exc=None) from None
        if not DocumentoComprovante.objects.filter(pk=doc.pk).exists():
            intencao_limpeza(doc.pk)
        return
    with transaction.atomic():
        barreira()
        doc = (
            DocumentoComprovante.objects.select_for_update()
            .filter(pk=documento_id, estado="lendo", tentativa=tentativa)
            .first()
        )
        if not doc:
            if not DocumentoComprovante.objects.filter(pk=documento_id).exists():
                intencao_limpeza(documento_id)
            return
        doc.estado, doc.mime, doc.lido_em = ("valido" if mime else "invalido"), mime, timezone.now()
        doc.save(update_fields=["estado", "mime", "lido_em"])
    path.unlink(missing_ok=True)


@shared_task
def recuperar_limpeza():
    for pk in LimpezaComprovante.objects.values_list("pk", flat=True).iterator():
        try:
            with transaction.atomic():
                _travar_objeto(pk)
                item = LimpezaComprovante.objects.filter(pk=pk).first()
                if not item or DocumentoComprovante.objects.filter(pk=pk).exists():
                    continue
                armazenamento().delete(chave(pk))
                spool(pk).unlink(missing_ok=True)
                if not item.incerta:
                    LimpezaComprovante.objects.filter(pk=pk, geracao=item.geracao).delete()
        except Exception:
            continue


@shared_task
def limpar_expirados():
    with transaction.atomic():
        barreira()
        for doc in DocumentoComprovante.objects.select_for_update().filter(
            vinculado_em__isnull=True, criado_em__lt=timezone.now() - timedelta(hours=24)
        ):
            doc.delete()


@shared_task
def recuperar_comprovantes():
    with transaction.atomic():
        barreira()
        DocumentoComprovante.objects.filter(
            estado="lendo", lido_em__lt=timezone.now() - timedelta(minutes=5)
        ).update(estado="erro")
    limpar_expirados()
    recuperar_limpeza()
    for pk in DocumentoComprovante.objects.filter(estado="pendente").values_list("pk", flat=True):
        agendar(processar_comprovante, str(pk))
