from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.boletos.models import DocumentoBoleto
from apps.boletos.tasks import agendar, limpar_pdfs_expirados, processar_pdf, recuperar_limpeza


class Command(BaseCommand):
    help = "Recover expired drafts, cleanup and pending processing."

    def handle(self, *args, **options):
        DocumentoBoleto.objects.filter(
            estado="lendo", lido_em__lt=timezone.now() - timedelta(minutes=5)
        ).update(estado="pendente")
        limpar_pdfs_expirados()
        recuperar_limpeza()
        for pk in DocumentoBoleto.objects.filter(estado="pendente").values_list("pk", flat=True):
            agendar(processar_pdf, str(pk))
