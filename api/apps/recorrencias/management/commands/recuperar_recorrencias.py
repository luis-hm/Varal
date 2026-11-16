from django.core.management.base import BaseCommand

from apps.recorrencias.tasks import gerar_recorrencias


class Command(BaseCommand):
    help = "Materialize and recover due recurrence months."

    def handle(self, *args, **options):
        gerar_recorrencias()
