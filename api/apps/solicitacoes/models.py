import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class EstadoSolicitacao(models.TextChoices):
    PREPARANDO = "preparando", "Preparando"
    ATIVA = "ativa", "Ativa"
    QUITADA = "quitada", "Quitada"
    ENCERRADA = "encerrada", "Encerrada"
    FALHOU = "falhou", "Falhou"


class Solicitacao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    origem = models.ForeignKey(
        "lancamentos.Lancamento",
        null=True,
        on_delete=models.SET_NULL,
        related_name="solicitacoes_origem",
    )
    copia = models.OneToOneField(
        "lancamentos.Lancamento",
        null=True,
        on_delete=models.SET_NULL,
        related_name="solicitacao_copia",
    )
    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="solicitacoes"
    )
    grupo = models.ForeignKey(
        "espacos.Espaco", on_delete=models.CASCADE, related_name="solicitacoes"
    )
    pagador_inicial = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="solicitacoes_recebidas",
    )
    nonce = models.UUIDField()
    corpo_hash = models.CharField(max_length=64)
    snapshot = models.JSONField(default=dict)
    estado = models.CharField(
        max_length=16, choices=EstadoSolicitacao.choices, default=EstadoSolicitacao.PREPARANDO
    )
    tentativa = models.UUIDField(null=True)
    tentativas = models.PositiveSmallIntegerField(default=0)
    lease_ate = models.DateTimeField(null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["origem"],
                condition=Q(origem__isnull=False, estado__in=["preparando", "ativa", "quitada"]),
                name="solicitacao_uma_viva_origem",
            ),
            models.UniqueConstraint(
                fields=["solicitante", "origem", "nonce"], name="solicitacao_nonce_origem"
            ),
            models.CheckConstraint(
                condition=Q(estado__in=EstadoSolicitacao.values), name="solicitacao_estado_valido"
            ),
        ]

    def __str__(self):
        return f"Solicitação {self.pk}"


class TombstoneNonce(models.Model):
    solicitante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    origem = models.ForeignKey("lancamentos.Lancamento", on_delete=models.CASCADE)
    nonce = models.UUIDField()
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["solicitante", "origem", "nonce"], name="solicitacao_tombstone_unico"
            )
        ]

    def __str__(self):
        return "Tentativa encerrada"


class ParPagamento(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    solicitacao = models.ForeignKey(Solicitacao, on_delete=models.PROTECT, related_name="pares")
    copia = models.OneToOneField(
        "pagamentos.Pagamento", null=True, on_delete=models.SET_NULL, related_name="par_copia"
    )
    derivada = models.OneToOneField(
        "pagamentos.Pagamento", null=True, on_delete=models.SET_NULL, related_name="par_derivada"
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Par {self.pk}"


class EventoSolicitacao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    solicitacao = models.OneToOneField(Solicitacao, on_delete=models.CASCADE, related_name="evento")
    destinatario = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    processado_em = models.DateTimeField(null=True)
    resultado = models.CharField(max_length=32, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evento {self.pk}"
