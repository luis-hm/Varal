import uuid

from django.utils.crypto import salted_hmac
from rest_framework.exceptions import PermissionDenied

from apps.boletos.tasks import _travar_objeto

from .models import InstalacaoPush, SessaoPush


def travar_sessao(request):
    chave = request.session.session_key
    if not chave:
        raise PermissionDenied()
    fingerprint = salted_hmac("varal.push.sessao", chave, algorithm="sha256").hexdigest()
    _travar_objeto(uuid.UUID(fingerprint[:32]))
    sessao, _ = SessaoPush.objects.select_for_update().get_or_create(
        fingerprint=fingerprint, defaults={"usuario": request.user}
    )
    if sessao.usuario_id != request.user.pk or sessao.revogada:
        raise PermissionDenied()
    return sessao


def travar_instalacao(usuario, identificador):
    token = uuid.uuid5(usuario.pk, str(identificador))
    _travar_objeto(token)
    return InstalacaoPush.objects.select_for_update().get_or_create(
        usuario=usuario, identificador=identificador
    )[0]
