import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """Custom user from day one (swapping AUTH_USER_MODEL later is painful).

    Domain fields from docs/dados/modelo.md (nome, telefone, prefs_notificacao) arrive in stage 02.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
