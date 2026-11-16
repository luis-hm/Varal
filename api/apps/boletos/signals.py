from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import DocumentoBoleto
from .tasks import intencao_limpeza


@receiver(pre_delete, sender=DocumentoBoleto)
def limpar_documento(sender, instance, **kwargs):
    intencao_limpeza(instance.pk)
