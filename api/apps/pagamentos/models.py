import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class Pagamento(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lancamento = models.ForeignKey(
        "lancamentos.Lancamento", on_delete=models.CASCADE, related_name="pagamentos"
    )
    pago_em = models.DateField()
    valor_pago_centavos = models.PositiveIntegerField()
    marcado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    pagador = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    desfeito_em = models.DateTimeField(null=True, blank=True)
    desfeito_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["criado_em"]
        constraints = [
            models.UniqueConstraint(
                fields=["lancamento"],
                condition=Q(desfeito_em__isnull=True),
                name="pagamento_uma_marca_ativa",
            ),
            models.CheckConstraint(
                condition=Q(valor_pago_centavos__gt=0), name="pagamento_valor_positivo"
            ),
        ]

    def __str__(self):
        return f"Pagamento {self.pk}"


class EventoPagamento(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pagamento = models.OneToOneField(Pagamento, on_delete=models.CASCADE, related_name="evento")
    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    processado_em = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Evento {self.pk}"


class EstadoComprovante(models.TextChoices):
    PENDENTE = "pendente", "Aguardando validação"
    LENDO = "lendo", "Validando"
    VALIDO = "valido", "Validado"
    INVALIDO = "invalido", "Arquivo inválido"
    ERRO = "erro", "Falha na validação"


class DocumentoComprovante(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lancamento = models.ForeignKey(
        "lancamentos.Lancamento", on_delete=models.CASCADE, related_name="documentos_comprovante"
    )
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    pagamento_alvo = models.ForeignKey(
        Pagamento, null=True, blank=True, on_delete=models.CASCADE, related_name="drafts"
    )
    pagamento = models.OneToOneField(
        Pagamento, null=True, blank=True, on_delete=models.CASCADE, related_name="comprovante"
    )
    versao = models.PositiveBigIntegerField()
    vinculado_em = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(
        max_length=16, choices=EstadoComprovante.choices, default=EstadoComprovante.PENDENTE
    )
    tentativa = models.UUIDField(null=True, blank=True)
    nome = models.CharField(max_length=200)
    tamanho = models.PositiveIntegerField()
    mime = models.CharField(max_length=32, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    lido_em = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Comprovante {self.pk}"


class LimpezaComprovante(models.Model):
    id = models.UUIDField(primary_key=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Limpeza {self.pk}"
