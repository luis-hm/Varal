from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.boletos.tasks import agendar
from apps.pagamentos.models import DocumentoComprovante
from apps.pagamentos.tasks import limpar_expirados, processar_comprovante, recuperar_limpeza
from apps.solicitacoes.coordenacao import barreira


class Command(BaseCommand):
    help = "Recover evidence processing and cleanup."

    def handle(self, *args, **options):
        with transaction.atomic():
            barreira()
            DocumentoComprovante.objects.filter(
                estado="lendo", lido_em__lt=timezone.now() - timedelta(minutes=5)
            ).update(estado="erro")
        limpar_expirados()
        recuperar_limpeza()
        for pk in DocumentoComprovante.objects.filter(estado="pendente").values_list(
            "pk", flat=True
        ):
            agendar(processar_comprovante, str(pk))
