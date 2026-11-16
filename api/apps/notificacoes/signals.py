import uuid

from django.contrib.auth.signals import user_logged_out
from django.db import transaction
from django.dispatch import receiver
from django.utils.crypto import salted_hmac

from apps.boletos.tasks import _travar_objeto

from .models import InscricaoPush, SessaoPush
from .sessoes import travar_instalacao


@receiver(user_logged_out)
@transaction.atomic
def revogar_instalacao_sessao(sender, request, user, **kwargs):
    if not request or not user or not request.session.session_key:
        return
    fingerprint = salted_hmac(
        "varal.push.sessao", request.session.session_key, algorithm="sha256"
    ).hexdigest()
    _travar_objeto(uuid.UUID(fingerprint[:32]))
    sessao, _ = SessaoPush.objects.select_for_update().get_or_create(
        fingerprint=fingerprint, defaults={"usuario": user}
    )
    if sessao.usuario_id != user.pk:
        return
    sessao.revogada = True
    sessao.save(update_fields=["revogada"])
    instalacoes = list(
        InscricaoPush.objects.filter(sessao=sessao, usuario=user, ativa=True)
        .order_by("instalacao")
        .values_list("instalacao", flat=True)
    )
    for identificador in instalacoes:
        instalacao = travar_instalacao(user, identificador)
        instalacao.revogada = True
        instalacao.save(update_fields=["revogada"])
    inscricoes = InscricaoPush.objects.select_for_update().filter(
        sessao=sessao, usuario=user, ativa=True
    )
    list(inscricoes.order_by("pk").values_list("pk", flat=True))
    inscricoes.update(ativa=False)
