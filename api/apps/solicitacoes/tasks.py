"""Recoverable short domain phases, separated from private object I/O."""

import uuid
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.boletos.copia import abandonar_copia, copiar_verificada, preparar_copia

from .coordenacao import barreira, travar_reserva
from .models import EstadoSolicitacao, Solicitacao
from .servicos import ativar, elegivel, encerrar_preparacao


@shared_task(time_limit=120)
def processar_solicitacao(pk):
    with transaction.atomic():
        barreira()
        reserva = travar_reserva(pk)
        if not reserva or reserva.estado != EstadoSolicitacao.PREPARANDO:
            return
        if not elegivel(reserva):
            encerrar_preparacao(reserva)
            return
        if reserva.tentativa and reserva.lease_ate and reserva.lease_ate > timezone.now():
            return
        if reserva.tentativa:
            abandonar_copia(reserva.pk, reserva.tentativa)
        if reserva.tentativas >= 3:
            encerrar_preparacao(reserva, EstadoSolicitacao.FALHOU)
            return
        documento = reserva.snapshot.get("documento")
        if not documento:
            ativar(reserva)
            return
        tentativa = uuid.uuid4()
        preparar_copia(reserva.pk, tentativa, documento["id"])
        reserva.tentativa = tentativa
        reserva.tentativas += 1
        reserva.lease_ate = timezone.now() + timedelta(minutes=3)
        reserva.save(update_fields=["tentativa", "tentativas", "lease_ate", "atualizado_em"])
    try:
        copiar_verificada(pk, tentativa)
    except Exception:
        with transaction.atomic():
            barreira()
            reserva = travar_reserva(pk)
            if reserva and reserva.tentativa == tentativa:
                abandonar_copia(pk, tentativa)
                reserva.tentativa = None
                reserva.lease_ate = None
                reserva.save(update_fields=["tentativa", "lease_ate", "atualizado_em"])
        return
    with transaction.atomic():
        barreira()
        reserva = travar_reserva(pk)
        if (
            not reserva
            or reserva.tentativa != tentativa
            or reserva.estado != EstadoSolicitacao.PREPARANDO
        ):
            abandonar_copia(pk, tentativa)
            return
        ativar(reserva)


@shared_task
def recuperar_solicitacoes():
    from apps.boletos.tasks import agendar

    for pk in (
        Solicitacao.objects.filter(estado=EstadoSolicitacao.PREPARANDO)
        .values_list("pk", flat=True)
        .iterator()
    ):
        agendar(processar_solicitacao, str(pk))
