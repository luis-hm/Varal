from celery import shared_task

from .models import Recorrencia
from .servicos import processar_recorrencia


@shared_task
def gerar_recorrencias():
    for pk in Recorrencia.objects.order_by("pk").values_list("pk", flat=True).iterator():
        processar_recorrencia(pk)
