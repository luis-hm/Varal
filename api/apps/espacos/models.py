import uuid

from django.conf import settings
from django.db import models, transaction


class EspacoQuerySet(models.QuerySet):
    def delete(self):
        from apps.solicitacoes.coordenacao import barreira

        with transaction.atomic():
            barreira()
            return super().delete()


class Espaco(models.Model):
    class Tipo(models.TextChoices):
        PESSOAL = "pessoal", "Pessoal"
        GRUPO = "grupo", "Grupo"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    nome = models.CharField(max_length=150)
    # Only the personal space has an owner; groups are run by Membro(papel=admin) (RN04).
    dono = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="espacos", null=True
    )
    janela_alerta_dias = models.PositiveSmallIntegerField(default=3)
    objects = EspacoQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["dono"], condition=models.Q(tipo="pessoal"), name="espaco_pessoal_unico"
            ),
            models.CheckConstraint(
                condition=~models.Q(tipo="pessoal") | models.Q(dono__isnull=False),
                name="espaco_pessoal_tem_dono",
            ),
            models.CheckConstraint(
                condition=~models.Q(tipo="grupo") | models.Q(dono__isnull=True),
                name="espaco_grupo_sem_dono",
            ),
            models.CheckConstraint(  # RN13
                condition=models.Q(janela_alerta_dias__gte=1, janela_alerta_dias__lte=7),
                name="espaco_janela_alerta_1_a_7",
            ),
        ]

    def __str__(self):
        return self.nome

    def delete(self, *args, **kwargs):
        from apps.solicitacoes.coordenacao import barreira

        with transaction.atomic():
            barreira()
            return super().delete(*args, **kwargs)


class Papel(models.TextChoices):
    ADMIN = "admin", "Admin"
    MEMBRO = "membro", "Membro"
    PAGADOR = "pagador", "Pagador"
    OBSERVADOR = "observador", "Observador"


class Membro(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    espaco = models.ForeignKey(Espaco, on_delete=models.CASCADE, related_name="membros")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="participacoes"
    )
    papel = models.CharField(max_length=10, choices=Papel.choices)
    criado_em = models.DateTimeField(auto_now_add=True)

    objects = EspacoQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["espaco", "usuario"], name="membro_unico_por_espaco")
        ]

    def __str__(self):
        return f"{self.usuario} em {self.espaco} ({self.papel})"

    def delete(self, *args, **kwargs):
        from apps.solicitacoes.coordenacao import barreira

        with transaction.atomic():
            barreira()
            return super().delete(*args, **kwargs)


class Convite(models.Model):
    """RN24/RN31: bearer link. Only the SHA-256 of the token is stored."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    espaco = models.ForeignKey(Espaco, on_delete=models.CASCADE, related_name="convites")
    papel = models.CharField(max_length=10, choices=Papel.choices)
    token_hash = models.CharField(max_length=64, unique=True)
    expira_em = models.DateTimeField()
    usado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    usado_em = models.DateTimeField(null=True)
    revogado_em = models.DateTimeField(null=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Convite {self.papel} para {self.espaco}"


class Subgrupo(models.Model):
    """A "casa" of a group (CU04)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    espaco = models.ForeignKey(Espaco, on_delete=models.CASCADE, related_name="subgrupos")
    nome = models.CharField(max_length=150)
    arquivado = models.BooleanField(default=False)

    def __str__(self):
        return self.nome
