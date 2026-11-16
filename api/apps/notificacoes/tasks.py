import uuid
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.boletos.tasks import agendar
from apps.recorrencias.tasks import gerar_recorrencias

from .entregas import enviar_email_entrega, enviar_push_dispositivo
from .models import EntregaNotificacao, EntregaPushDispositivo, EstadoEntrega, RodadaDiaria
from .servicos import consumir_fontes, varrer_lembretes


@shared_task
def consumir_eventos():
    consumir_fontes()


@shared_task
def rotina_diaria():
    agora = timezone.localtime()
    if agora.hour < 7:
        return
    dia = agora.date()
    with transaction.atomic():
        rodada, _ = RodadaDiaria.objects.select_for_update().get_or_create(dia=dia)
        if rodada.lease_ate and rodada.lease_ate > timezone.now():
            return
        token = uuid.uuid4()
        rodada.token = token
        rodada.lease_ate = timezone.now() + timedelta(minutes=15)
        rodada.save(update_fields=["token", "lease_ate", "atualizado_em"])
        precisa_gerar = not rodada.geracao_concluida
    try:
        if precisa_gerar:
            # The task calls its underlying service synchronously; no enqueued child races.
            gerar_recorrencias()
            with transaction.atomic():
                rodada = (
                    RodadaDiaria.objects.select_for_update().filter(dia=dia, token=token).first()
                )
                if not rodada:
                    return
                rodada.geracao_concluida = True
                rodada.save(update_fields=["geracao_concluida", "atualizado_em"])
        if timezone.localdate() != dia:
            return
        varrer_lembretes()
        RodadaDiaria.objects.filter(dia=dia, token=token).update(avisos_concluidos=True)
    finally:
        RodadaDiaria.objects.filter(dia=dia, token=token).update(token=None, lease_ate=None)


@shared_task(time_limit=45, soft_time_limit=35)
def entregar_email(pk):
    enviar_email_entrega(pk)


@shared_task(time_limit=45, soft_time_limit=35)
def entregar_push(pk):
    enviar_push_dispositivo(pk)


@shared_task
def despachar():
    consumir_fontes()
    agora = timezone.now()
    selecionaveis = (
        Q(estado=EstadoEntrega.PENDENTE) & (Q(proxima_em__isnull=True) | Q(proxima_em__lte=agora))
    ) | Q(estado__in=[EstadoEntrega.RESERVADA, EstadoEntrega.INICIADA], lease_ate__lte=agora)
    for pk in (
        EntregaNotificacao.objects.filter(selecionaveis, canal="email")
        .order_by("pk")
        .values_list("pk", flat=True)
        .iterator()
    ):
        agendar(entregar_email, str(pk))
    for pk in (
        EntregaPushDispositivo.objects.filter(selecionaveis)
        .order_by("pk")
        .values_list("pk", flat=True)
        .iterator()
    ):
        agendar(entregar_push, str(pk))
