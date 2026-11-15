import uuid

from django.conf import settings
from django.db import models


class Espaco(models.Model):
    class Tipo(models.TextChoices):
        PESSOAL = "pessoal", "Pessoal"
        GRUPO = "grupo", "Grupo"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    nome = models.CharField(max_length=150)
    dono = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="espacos", null=True
    )
    janela_alerta_dias = models.PositiveSmallIntegerField(default=3)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["dono"], condition=models.Q(tipo="pessoal"), name="espaco_pessoal_unico"
            ),
            models.CheckConstraint(
                condition=~models.Q(tipo="pessoal") | models.Q(dono__isnull=False),
                name="espaco_pessoal_tem_dono",
            ),
        ]

    def __str__(self):
        return self.nome
