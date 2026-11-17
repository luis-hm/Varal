import uuid

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models, transaction
from django.db.models.functions import Lower


class UsuarioQuerySet(models.QuerySet):
    def bulk_create(self, *args, **kwargs):
        from apps.solicitacoes.coordenacao import barreira

        with transaction.atomic():
            barreira()
            return super().bulk_create(*args, **kwargs)

    def update(self, **kwargs):
        from apps.solicitacoes.coordenacao import barreira

        if not set(kwargs).intersection(
            {"nome", "email", "telefone", "prefs_notificacao", "is_active", "password"}
        ):
            return super().update(**kwargs)
        with transaction.atomic():
            barreira()
            return super().update(**kwargs)

    def delete(self):
        from apps.privacidade.exclusao import collector_permitido, excluir_privilegiado
        from apps.solicitacoes.coordenacao import barreira

        if not collector_permitido():
            usuarios = list(self[:2])
            if len(usuarios) > 1:
                raise RuntimeError("Exclusão em lote não é permitida; exclua uma pessoa por vez")
            return excluir_privilegiado(usuarios[0]) if usuarios else (0, {})
        with transaction.atomic():
            barreira()
            return super().delete()


class UsuarioManager(UserManager.from_queryset(UsuarioQuerySet)):
    pass


class Usuario(AbstractUser):
    """Email-facing account; username remains an internal Django/admin identifier."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    nome = models.CharField(max_length=150, blank=True)
    telefone = models.CharField(max_length=30, blank=True)
    prefs_notificacao = models.JSONField(default=dict, blank=True)
    objects = UsuarioManager()

    def delete(self, *args, **kwargs):
        from apps.privacidade.exclusao import collector_permitido, excluir_privilegiado
        from apps.solicitacoes.coordenacao import barreira

        if not collector_permitido():
            return excluir_privilegiado(self)
        with transaction.atomic():
            barreira()
            return super().delete(*args, **kwargs)

    class Meta:
        constraints = [models.UniqueConstraint(Lower("email"), name="usuario_email_ci_unique")]

    def save(self, *args, **kwargs):
        # The personal space and user must never be committed separately (RN03).
        from apps.espacos.models import Espaco
        from apps.solicitacoes.coordenacao import barreira

        with transaction.atomic():
            barreira()
            self.email = self.email.lower().strip()
            super().save(*args, **kwargs)
            Espaco.objects.get_or_create(
                dono=self, tipo=Espaco.Tipo.PESSOAL, defaults={"nome": "Pessoal"}
            )


class TicketGoogle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    tentativa = models.UUIDField()
    expira_em = models.DateTimeField()
    consumido_em = models.DateTimeField(null=True)

    def __str__(self):
        return "Ticket de retorno Google"
