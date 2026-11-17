from django.apps import AppConfig
from django.db.models.signals import post_migrate


def _assegurar_revisao(sender, using, **kwargs):
    # Administrative migration/flush recreates a missing row with a fresh epoch.
    # Ordinary runtime writes still fail closed if the row disappears.
    from .models import RevisaoExportacao

    RevisaoExportacao.objects.using(using).get_or_create(pk=1)


class PrivacidadeConfig(AppConfig):
    name = "apps.privacidade"

    def ready(self):
        post_migrate.connect(_assegurar_revisao, sender=self, dispatch_uid="privacidade.revisao")
