import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models, transaction
from django.db.models.functions import Lower


class Usuario(AbstractUser):
    """Email-facing account; username remains an internal Django/admin identifier."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    nome = models.CharField(max_length=150, blank=True)
    telefone = models.CharField(max_length=30, blank=True)
    prefs_notificacao = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(Lower("email"), name="usuario_email_ci_unique")]

    def save(self, *args, **kwargs):
        # The personal space and user must never be committed separately (RN03).
        from apps.espacos.models import Espaco

        with transaction.atomic():
            self.email = self.email.lower().strip()
            super().save(*args, **kwargs)
            Espaco.objects.get_or_create(
                dono=self, tipo=Espaco.Tipo.PESSOAL, defaults={"nome": "Pessoal"}
            )
