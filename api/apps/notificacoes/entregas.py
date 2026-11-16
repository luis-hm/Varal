"""Durable reservations; ambiguous outcomes are never blindly retried."""

import uuid
from datetime import datetime, time, timedelta
from email.utils import parsedate_to_datetime

from django.db import transaction
from django.utils import timezone

from apps.solicitacoes.coordenacao import barreira

from . import push, transportes
from .acesso import autorizadas
from .models import (
    EntregaNotificacao,
    EntregaPushDispositivo,
    EstadoEntrega,
    InscricaoPush,
    Notificacao,
    TipoEvento,
)
from .servicos import _conta_travada_sistema, preferencias

LEMBRETES = {
    TipoEvento.BOLETO_AUSENTE,
    TipoEvento.VENCE_3,
    TipoEvento.VENCE_HOJE,
    TipoEvento.VENCEU_1,
}
TERMINAIS = {
    EstadoEntrega.ACEITA,
    EstadoEntrega.DESCARTADA,
    EstadoEntrega.FALHOU,
    EstadoEntrega.INCERTA,
}


def _contexto(notificacao_id):
    ref = (
        Notificacao.objects.filter(pk=notificacao_id)
        .values("evento__tipo", "evento__lancamento_id")
        .first()
    )
    if not ref:
        return None
    if ref["evento__tipo"] != TipoEvento.CANCELADA_RN32:
        if not ref["evento__lancamento_id"] or not _conta_travada_sistema(
            ref["evento__lancamento_id"]
        ):
            return None
    return (
        Notificacao.objects.select_for_update(of=("self",))
        .select_related("destinatario", "evento")
        .filter(pk=notificacao_id)
        .first()
    )


def _valida(n, canal):
    if not n or not autorizadas(n.destinatario).filter(pk=n.pk).exists():
        return False
    if not preferencias(n.destinatario)[canal]:
        return False
    if n.evento.tipo in LEMBRETES:
        agora = timezone.localtime()
        if not n.evento.alvo or agora.date() != n.evento.alvo or agora.hour < 7:
            return False
    return True


def _adiar_futura(obj, n):
    if not n or n.evento.tipo not in LEMBRETES or not n.evento.alvo:
        return False
    inicio = timezone.make_aware(
        datetime.combine(n.evento.alvo, time(7)), timezone.get_current_timezone()
    )
    if timezone.now() >= inicio:
        return False
    obj.estado = EstadoEntrega.PENDENTE
    obj.proxima_em = inicio
    obj.token = obj.lease_ate = None
    obj.save()
    return True


def _proxima(tentativas, retry_after):
    agora = timezone.now()
    atraso = 60 if tentativas == 1 else 300
    if retry_after:
        try:
            atraso = max(atraso, int(retry_after))
        except ValueError:
            try:
                data = parsedate_to_datetime(retry_after)
                atraso = max(atraso, int((data - agora).total_seconds()))
            except (ValueError, TypeError, OverflowError):
                pass
    if atraso > 315_360_000:
        return None
    return agora + timedelta(seconds=max(atraso, 0))


def _finalizar(obj, resultado):
    if resultado.estado == "transiente" and obj.tentativas < 3:
        obj.proxima_em = _proxima(obj.tentativas, resultado.retry_after)
        obj.estado = EstadoEntrega.PENDENTE if obj.proxima_em else EstadoEntrega.FALHOU
    else:
        obj.estado = EstadoEntrega.FALHOU if resultado.estado == "transiente" else resultado.estado
        obj.proxima_em = None
    obj.resultado = resultado.codigo
    obj.token = None
    obj.lease_ate = None
    obj.save(
        update_fields=[
            "estado",
            "proxima_em",
            "resultado",
            "token",
            "lease_ate",
            "atualizado_em" if isinstance(obj, EntregaPushDispositivo) else "atualizada_em",
        ]
    )


def _marcar_iniciada(obj, notificacao, canal):
    agora = timezone.now()
    if obj.estado == EstadoEntrega.INICIADA:
        if obj.lease_ate and obj.lease_ate <= agora:
            obj.estado, obj.resultado, obj.token, obj.lease_ate = (
                EstadoEntrega.INCERTA,
                "lease_expirado",
                None,
                None,
            )
            obj.save()
        return None
    if obj.estado in TERMINAIS or (obj.proxima_em and obj.proxima_em > agora):
        return None
    if obj.tentativas >= 3:
        obj.estado, obj.resultado = EstadoEntrega.FALHOU, "tentativas_esgotadas"
        obj.save()
        return None
    if obj.estado == EstadoEntrega.RESERVADA and obj.lease_ate and obj.lease_ate > agora:
        return None
    if _adiar_futura(obj, notificacao):
        return None
    if not _valida(notificacao, canal):
        obj.estado, obj.resultado = EstadoEntrega.DESCARTADA, "nao_elegivel"
        obj.save()
        return None
    obj.estado = EstadoEntrega.RESERVADA
    obj.token = uuid.uuid4()
    obj.lease_ate = agora + timedelta(minutes=3)
    obj.save()
    return obj.token


def _iniciar(obj, notificacao, canal, token):
    if obj.estado != EstadoEntrega.RESERVADA or obj.token != token:
        return False
    if _adiar_futura(obj, notificacao):
        return False
    if not _valida(notificacao, canal):
        obj.estado, obj.resultado = EstadoEntrega.DESCARTADA, "nao_elegivel"
        obj.save()
        return False
    obj.estado = EstadoEntrega.INICIADA
    obj.tentativas += 1
    obj.lease_ate = timezone.now() + timedelta(minutes=3)
    obj.save()
    return True


def enviar_email_entrega(pk):
    ref = EntregaNotificacao.objects.filter(pk=pk, canal="email").values("notificacao_id").first()
    if not ref:
        return
    with transaction.atomic():
        barreira()
        n = _contexto(ref["notificacao_id"])
        entrega = EntregaNotificacao.objects.select_for_update().filter(pk=pk).first()
        token = _marcar_iniciada(entrega, n, "email") if entrega else None
    if not token:
        return
    with transaction.atomic():
        barreira()
        n = _contexto(ref["notificacao_id"])
        entrega = EntregaNotificacao.objects.select_for_update().filter(pk=pk).first()
        if not entrega or not _iniciar(entrega, n, "email", token):
            return
        destinatario = n.destinatario.email
    resultado = transportes.enviar_email(destinatario)
    with transaction.atomic():
        entrega = (
            EntregaNotificacao.objects.select_for_update()
            .filter(pk=pk, estado=EstadoEntrega.INICIADA, token=token)
            .first()
        )
        if entrega:
            _finalizar(entrega, resultado)


def _concluir_push(entrega):
    estados = list(entrega.dispositivos.values_list("estado", flat=True))
    if not estados or any(estado not in TERMINAIS for estado in estados):
        return
    if EstadoEntrega.INCERTA in estados:
        entrega.estado = EstadoEntrega.INCERTA
    elif EstadoEntrega.ACEITA in estados:
        entrega.estado = EstadoEntrega.ACEITA
    elif EstadoEntrega.FALHOU in estados:
        entrega.estado = EstadoEntrega.FALHOU
    else:
        entrega.estado = EstadoEntrega.DESCARTADA
    entrega.save(update_fields=["estado", "atualizada_em"])


def enviar_push_dispositivo(pk):
    ref = (
        EntregaPushDispositivo.objects.filter(pk=pk)
        .values("entrega__notificacao_id", "entrega_id")
        .first()
    )
    if not ref:
        return
    with transaction.atomic():
        barreira()
        n = _contexto(ref["entrega__notificacao_id"])
        entrega = EntregaNotificacao.objects.select_for_update().get(pk=ref["entrega_id"])
        item = (
            EntregaPushDispositivo.objects.select_for_update(of=("self",))
            .select_related("inscricao")
            .filter(pk=pk)
            .first()
        )
        if not item:
            return
        if not item.inscricao.ativa or item.inscricao.geracao != item.geracao:
            item.estado, item.resultado = EstadoEntrega.DESCARTADA, "inscricao_revogada"
            item.save()
            _concluir_push(entrega)
            return
        token = _marcar_iniciada(item, n, "push")
        if not token:
            _concluir_push(entrega)
    if not token:
        return
    with transaction.atomic():
        barreira()
        n = _contexto(ref["entrega__notificacao_id"])
        entrega = EntregaNotificacao.objects.select_for_update().get(pk=ref["entrega_id"])
        item = (
            EntregaPushDispositivo.objects.select_for_update(of=("self",))
            .select_related("inscricao")
            .filter(pk=pk)
            .first()
        )
        if not item:
            return
        inscricao_atual = (
            InscricaoPush.objects.select_for_update().filter(pk=item.inscricao_id).first()
        )
        if (
            not inscricao_atual
            or not inscricao_atual.ativa
            or inscricao_atual.geracao != item.geracao
        ):
            item.estado, item.resultado = EstadoEntrega.DESCARTADA, "inscricao_revogada"
            item.save()
            _concluir_push(entrega)
            return
        if not _iniciar(item, n, "push", token):
            _concluir_push(entrega)
            return
        segredo = bytes(inscricao_atual.segredo)
    try:
        inscricao = push.decifrar(segredo)
        resultado = transportes.enviar_push(inscricao)
    except Exception:
        resultado = transportes.Resultado("falhou", "configuracao")
    with transaction.atomic():
        entrega = EntregaNotificacao.objects.select_for_update().get(pk=ref["entrega_id"])
        item = (
            EntregaPushDispositivo.objects.select_for_update(of=("self",))
            .filter(pk=pk, estado=EstadoEntrega.INICIADA, token=token)
            .first()
        )
        if item:
            _finalizar(item, resultado)
            if resultado.codigo == "inscricao_expirada":
                InscricaoPush.objects.filter(pk=item.inscricao_id, geracao=item.geracao).update(
                    ativa=False
                )
            _concluir_push(entrega)
