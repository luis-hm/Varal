import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.lancamentos.models import Visibilidade


class Recorrencia(models.Model):
    class Estado(models.TextChoices):
        ATIVA = "ativa", "Ativa"
        PAUSADA = "pausada", "Pausada"
        ENCERRADA = "encerrada", "Encerrada"

    class ValorTipo(models.TextChoices):
        FIXO = "fixo", "Fixo"
        VARIAVEL = "variavel", "Variável"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    espaco = models.ForeignKey(
        "espacos.Espaco", on_delete=models.CASCADE, related_name="recorrencias"
    )
    criador = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    descricao = models.CharField(max_length=150)
    dia_vencimento = models.PositiveSmallIntegerField()
    valor_tipo = models.CharField(max_length=10, choices=ValorTipo.choices)
    valor_centavos = models.PositiveIntegerField(null=True, blank=True)
    subgrupo = models.ForeignKey(
        "espacos.Subgrupo",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="recorrencias",
    )
    pagador = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    visibilidade = models.CharField(
        max_length=10,
        choices=Visibilidade.choices,
        default="grupo",
    )
    acesso = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="recorrencias_com_acesso", blank=True
    )
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.ATIVA)
    motivo_pausa = models.CharField(max_length=30, blank=True)
    cursor = models.DateField()
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(dia_vencimento__gte=1, dia_vencimento__lte=31),
                name="recorrencia_dia_valido",
            ),
            models.CheckConstraint(
                condition=(
                    Q(valor_tipo="fixo", valor_centavos__isnull=False, valor_centavos__gt=0)
                    | Q(valor_tipo="variavel", valor_centavos__isnull=True)
                ),
                name="recorrencia_tipo_valor_valido",
            ),
            models.CheckConstraint(
                condition=Q(estado__in=["ativa", "pausada", "encerrada"]),
                name="recorrencia_estado_valido",
            ),
            models.CheckConstraint(
                condition=Q(visibilidade__in=["grupo", "restrita"]),
                name="recorrencia_visibilidade_valida",
            ),
        ]

    def __str__(self):
        return f"Recorrência {self.pk}"


class RevisaoRecorrencia(models.Model):
    recorrencia = models.ForeignKey(Recorrencia, on_delete=models.CASCADE, related_name="revisoes")
    competencia_inicio = models.DateField()
    alteracoes = models.JSONField(default=dict)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Revisão {self.pk}"


class CompetenciaDevida(models.Model):
    recorrencia = models.ForeignKey(
        Recorrencia, on_delete=models.CASCADE, related_name="competencias"
    )
    competencia = models.DateField()
    estado = models.CharField(
        max_length=12,
        choices=[("pendente", "Pendente"), ("bloqueada", "Bloqueada"), ("gerada", "Gerada")],
        default="pendente",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recorrencia", "competencia"], name="competencia_devida_unica"
            ),
            models.CheckConstraint(
                condition=Q(competencia__day=1), name="competencia_devida_primeiro_dia"
            ),
        ]

    def __str__(self):
        return f"Competência {self.pk}"


class OperacaoRecorrencia(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+"
    )
    chave = models.UUIDField()
    hash_entrada = models.CharField(max_length=64)
    recorrencia = models.OneToOneField(
        Recorrencia, on_delete=models.CASCADE, related_name="operacao_criacao"
    )
    competencia = models.DateField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["usuario", "chave"], name="recorrencia_operacao_unica")
        ]

    def __str__(self):
        return f"Operação {self.pk}"
