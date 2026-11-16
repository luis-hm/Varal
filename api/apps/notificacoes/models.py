import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class TipoEvento(models.TextChoices):
    BOLETO_AUSENTE = "boleto_ausente", "Boleto a definir"
    VENCE_3 = "vence_3", "Vence em três dias"
    VENCE_HOJE = "vence_hoje", "Vence hoje"
    VENCEU_1 = "venceu_1", "Venceu ontem"
    PAGAMENTO = "pagamento", "Pagamento registrado"
    PAGADOR_REMOVIDO = "pagador_removido", "Pagador removido"
    CANCELADA_RN32 = "cancelada_rn32", "Conta cancelada automaticamente"


class EventoNotificacao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chave = models.CharField(max_length=128, unique=True)
    tipo = models.CharField(max_length=30, choices=TipoEvento.choices)
    lancamento = models.ForeignKey(
        "lancamentos.Lancamento", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    pagamento = models.ForeignKey(
        "pagamentos.Pagamento", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    historico = models.ForeignKey(
        "lancamentos.Historico", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    alvo = models.DateField(null=True, blank=True)
    snapshot_p7 = models.JSONField(default=dict, blank=True)
    canais_permitidos = models.BooleanField(default=True)
    materializado_em = models.DateTimeField(null=True, blank=True)
    resultado = models.CharField(max_length=32, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evento {self.pk}"


class Notificacao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evento = models.ForeignKey(
        EventoNotificacao, on_delete=models.CASCADE, related_name="notificacoes"
    )
    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notificacoes"
    )
    lido_em = models.DateTimeField(null=True, blank=True)
    revogado_em = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["evento", "destinatario"], name="notificacao_evento_destinatario_unico"
            )
        ]
        indexes = [models.Index(fields=["destinatario", "-criado_em", "-id"])]

    def __str__(self):
        return f"Notificação {self.pk}"


class EstadoEntrega(models.TextChoices):
    PENDENTE = "pendente", "Pendente"
    RESERVADA = "reservada", "Reservada"
    INICIADA = "iniciada", "Iniciada"
    ACEITA = "aceita", "Aceita"
    DESCARTADA = "descartada", "Descartada"
    FALHOU = "falhou", "Falhou"
    INCERTA = "incerta", "Incerta"


class EntregaNotificacao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notificacao = models.ForeignKey(Notificacao, on_delete=models.CASCADE, related_name="entregas")
    canal = models.CharField(max_length=8, choices=[("email", "E-mail"), ("push", "Push")])
    estado = models.CharField(
        max_length=12, choices=EstadoEntrega.choices, default=EstadoEntrega.PENDENTE
    )
    tentativas = models.PositiveSmallIntegerField(default=0)
    proxima_em = models.DateTimeField(null=True, blank=True)
    lease_ate = models.DateTimeField(null=True, blank=True)
    token = models.UUIDField(null=True, blank=True)
    resultado = models.CharField(max_length=32, blank=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["notificacao", "canal"], name="entrega_unica_por_canal"
            ),
            models.CheckConstraint(condition=Q(tentativas__lte=3), name="entrega_max_tentativas"),
        ]

    def __str__(self):
        return f"Entrega {self.pk}"


class SessaoPush(models.Model):
    fingerprint = models.CharField(primary_key=True, max_length=64)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+"
    )
    revogada = models.BooleanField(default=False)
    criada_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Sessão push"


class InstalacaoPush(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+"
    )
    identificador = models.UUIDField()
    fingerprint = models.CharField(max_length=64, blank=True)
    revogada = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "identificador"], name="instalacao_push_unica"
            )
        ]

    def __str__(self):
        return f"Instalação {self.pk}"


class InscricaoPush(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="inscricoes_push"
    )
    fingerprint = models.CharField(max_length=64, unique=True)
    sessao = models.ForeignKey(
        SessaoPush, null=True, blank=True, on_delete=models.SET_NULL, related_name="inscricoes"
    )
    segredo = models.BinaryField()
    instalacao = models.UUIDField()
    geracao = models.PositiveIntegerField(default=1)
    ativa = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Inscrição {self.pk}"


class EntregaPushDispositivo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entrega = models.ForeignKey(
        EntregaNotificacao, on_delete=models.CASCADE, related_name="dispositivos"
    )
    inscricao = models.ForeignKey(InscricaoPush, on_delete=models.CASCADE, related_name="+")
    geracao = models.PositiveIntegerField()
    estado = models.CharField(
        max_length=12, choices=EstadoEntrega.choices, default=EstadoEntrega.PENDENTE
    )
    tentativas = models.PositiveSmallIntegerField(default=0)
    proxima_em = models.DateTimeField(null=True, blank=True)
    lease_ate = models.DateTimeField(null=True, blank=True)
    token = models.UUIDField(null=True, blank=True)
    resultado = models.CharField(max_length=32, blank=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["entrega", "inscricao", "geracao"], name="entrega_push_dispositivo_unico"
            ),
            models.CheckConstraint(condition=Q(tentativas__lte=3), name="push_max_tentativas"),
        ]

    def __str__(self):
        return f"Dispositivo {self.pk}"


class ControleNotificacoes(models.Model):
    chave = models.CharField(max_length=32, primary_key=True)
    ativado_em = models.DateTimeField()

    def __str__(self):
        return f"Controle {self.pk}"


class RodadaDiaria(models.Model):
    dia = models.DateField(primary_key=True)
    geracao_concluida = models.BooleanField(default=False)
    avisos_concluidos = models.BooleanField(default=False)
    lease_ate = models.DateTimeField(null=True, blank=True)
    token = models.UUIDField(null=True, blank=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Rodada {self.pk}"
