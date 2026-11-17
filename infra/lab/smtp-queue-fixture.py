"""Create one synthetic local SMTP delivery through the actual Celery dispatcher."""
import json
import os
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection, transaction

from apps.notificacoes.models import EventoNotificacao
from apps.notificacoes.servicos import criar_notificacao
from apps.notificacoes.tasks import despachar
from apps.solicitacoes.coordenacao import barreira

if (
    os.environ.get("VARAL_LAB_FIXTURE") != "isolated"
    or not os.environ.get("VARAL_LAB_DB")
    or connection.settings_dict["NAME"] != os.environ.get("VARAL_LAB_DB")
    or settings.VARAL_RESTORE_MODE
):
    raise RuntimeError("Dedicated active lab required")
suffix = uuid.uuid4().hex
email = f"ca17-smtp-{suffix}@example.invalid"
user = get_user_model().objects.create_user(
    username="ca17-smtp-" + suffix,
    email=email,
    prefs_notificacao={"email": True, "push": False},
)
event = EventoNotificacao.objects.create(chave="ca17-smtp-" + suffix, tipo="cancelada_rn32")
with transaction.atomic():
    barreira()
    notice = criar_notificacao(event, user)
delivery = notice.entregas.get(canal="email")
despachar.delay()
print(json.dumps({"delivery": str(delivery.pk), "email": email}, sort_keys=True))
