"""Inventory immutable object references in the isolated restored database."""

import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.boletos.models import DocumentoBoleto, PinPDF, TentativaCopiaPDF
from apps.boletos.storage import chave as chave_pdf
from apps.pagamentos.models import DocumentoComprovante
from apps.pagamentos.storage import chave as chave_comprovante
from apps.privacidade.models import Exportacao, MarcaRestauracao
from apps.privacidade.tasks import chave_objeto


class Command(BaseCommand):
    help = "Emit the immutable storage inventory of a marked isolated restore."

    def add_arguments(self, parser):
        parser.add_argument("--operacao", required=True)
        parser.add_argument("--isolado", action="store_true")

    def handle(self, *args, operacao, isolado, **kwargs):
        if not settings.VARAL_RESTORE_MODE or not isolado:
            raise CommandError("Restore isolado e VARAL_RESTORE_MODE=1 são obrigatórios.")
        try:
            marker = MarcaRestauracao.objects.filter(operation_id=operacao).exists()
        except (ValueError, TypeError):
            marker = False
        if not marker:
            raise CommandError("Marcador de operação ausente.")
        if (
            DocumentoBoleto.objects.filter(estado__in=("pendente", "lendo")).exists()
            or DocumentoComprovante.objects.filter(estado__in=("pendente", "lendo")).exists()
            or TentativaCopiaPDF.objects.filter(estado__in=("ativa", "copiando")).exists()
            or Exportacao.objects.filter(estado="processando").exists()
        ):
            raise CommandError("Há arquivos ou cópias ainda em processamento.")
        objects = []
        for pk, tamanho in DocumentoBoleto.objects.values_list("pk", "tamanho").iterator():
            objects.append({"key": chave_pdf(pk), "size": tamanho, "sha256": None})
        for pk, tamanho in (
            DocumentoComprovante.objects.filter(estado="valido")
            .values_list("pk", "tamanho")
            .iterator()
        ):
            objects.append({"key": chave_comprovante(pk), "size": tamanho, "sha256": None})
        pins = []
        for reserva, documento, tamanho in PinPDF.objects.values_list(
            "reserva_id", "documento_id", "tamanho"
        ).iterator():
            pins.append({"reserva_id": str(reserva), "key": chave_pdf(documento), "size": tamanho})
            objects.append({"key": chave_pdf(documento), "size": tamanho, "sha256": None})
        for dest, tamanho, digest in (
            TentativaCopiaPDF.objects.filter(estado="verificada")
            .values_list("destino_id", "tamanho", "sha256")
            .iterator()
        ):
            if not tamanho or len(digest) != 64:
                raise CommandError("Cópia verificada sem hash ou tamanho.")
            objects.append({"key": chave_pdf(dest), "size": tamanho, "sha256": digest})
        for pk, digest in (
            Exportacao.objects.filter(estado="pronto")
            .values_list("objeto_id", "artefato_sha256")
            .iterator()
        ):
            if not pk or len(digest) != 64:
                raise CommandError("Exportação pronta sem objeto ou hash.")
            objects.append({"key": chave_objeto(pk), "size": None, "sha256": digest})
        result = {
            "version": 1,
            "operation_id": str(operacao),
            "bucket": settings.S3_BUCKET_NAME,
            "objects": sorted(objects, key=lambda item: (item["key"], item["sha256"] or "")),
            "pins": sorted(pins, key=lambda item: item["reserva_id"]),
        }
        self.stdout.write(
            json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        )
