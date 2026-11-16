import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Case, F, Q, Value, When
from django.utils import timezone


class Status(models.TextChoices):
    """Stored statuses (RN12). "vence" and "vencida" are computed, never stored."""

    AGUARDANDO = "aguardando", "Aguardando boleto"
    PENDENTE = "pendente", "Pendente"
    PAGA = "paga", "Paga"
    CONFIRMADA = "confirmada", "Confirmada"
    CANCELADA = "cancelada", "Cancelada"


ABERTOS = (Status.AGUARDANDO, Status.PENDENTE)
VENCE, VENCIDA = "vence", "vencida"
STATUS_EXIBIDOS = [*Status.values, VENCE, VENCIDA]


class Visibilidade(models.TextChoices):
    GRUPO = "grupo", "Todo o grupo"
    RESTRITA = "restrita", "Só algumas pessoas"


class LancamentoQuerySet(models.QuerySet):
    def com_status(self, janela, hoje=None):
        """Annotate `status_exibido` (RN12/RN13) so filters and counts run in SQL. Only
        `pendente` turns into `vencida`/`vence`; `hoje` is the civil date in Fortaleza."""
        hoje = hoje or timezone.localdate()
        return self.annotate(
            status_exibido=Case(
                When(status=Status.PENDENTE, vencimento__lt=hoje, then=Value(VENCIDA)),
                When(
                    status=Status.PENDENTE,
                    vencimento__lte=hoje + timedelta(days=janela),
                    then=Value(VENCE),
                ),
                default=F("status"),
                output_field=models.CharField(),
            )
        )


class Lancamento(models.Model):
    """A bill (conta). Never deleted: cancelling sets `cancelada` (RN22)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    espaco = models.ForeignKey(
        "espacos.Espaco", on_delete=models.CASCADE, related_name="lancamentos"
    )
    subgrupo = models.ForeignKey(
        "espacos.Subgrupo",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="lancamentos",
    )
    # RN30: bills outlive their author and payer; shown as "Ex-membro" / no payer.
    criador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="lancamentos_criados",
    )
    pagador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lancamentos_a_pagar",
    )
    descricao = models.CharField(max_length=150)
    valor_centavos = models.PositiveIntegerField(null=True, blank=True)
    vencimento = models.DateField()
    recorrencia = models.ForeignKey(
        "recorrencias.Recorrencia",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="lancamentos",
    )
    competencia = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDENTE)
    visibilidade = models.CharField(
        max_length=10, choices=Visibilidade.choices, default=Visibilidade.GRUPO
    )
    # RN06: who sees a restricted bill besides its author and payer.
    acesso = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        db_table="lancamento_acesso",
        related_name="lancamentos_com_acesso",
    )
    versao_pagamento = models.PositiveBigIntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    objects = LancamentoQuerySet.as_manager()

    class Meta:
        indexes = [models.Index(fields=["espaco", "vencimento"])]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(valor_centavos__isnull=False, valor_centavos__gt=0)
                    | Q(
                        valor_centavos__isnull=True,
                        status__in=(Status.AGUARDANDO, Status.CANCELADA),
                    )
                ),
                name="lancamento_valor_positivo",
            ),
            models.CheckConstraint(
                condition=Q(status__in=Status.values), name="lancamento_status_valido"
            ),
            models.CheckConstraint(
                condition=(
                    Q(recorrencia__isnull=True, competencia__isnull=True)
                    | Q(recorrencia__isnull=False, competencia__isnull=False, competencia__day=1)
                ),
                name="lancamento_competencia_pareada",
            ),
            models.UniqueConstraint(
                fields=["recorrencia", "competencia"],
                condition=Q(recorrencia__isnull=False),
                name="lancamento_competencia_unica",
            ),
            models.CheckConstraint(
                condition=Q(visibilidade__in=Visibilidade.values),
                name="lancamento_visibilidade_valida",
            ),
        ]

    def __str__(self):
        return self.descricao


class Acao(models.TextChoices):
    CRIADA = "criada", "Criou"
    EDITADA = "editada", "Editou"
    CANCELADA = "cancelada", "Cancelou"
    PAGADOR_REMOVIDO = "pagador_removido", "Ficou sem pagador"
    ACESSO_REMOVIDO = "acesso_removido", "Saiu de quem vê"
    CANCELADA_AUTOMATICAMENTE = "cancelada_automaticamente", "Cancelada automaticamente"
    ACESSO_PRESERVADO = "acesso_preservado", "Acesso preservado"
    PAGA = "paga", "Marcou como paga"
    PAGAMENTO_DESFEITO = "pagamento_desfeito", "Desfez pagamento"
    COMPROVANTE_ANEXADO = "comprovante_anexado", "Anexou comprovante"


class Historico(models.Model):
    """RN22: every change to a bill, with author and date."""

    Acao = Acao

    # Done by the system (RN21/RN32/ADR 0008): no author, never shown as "Ex-membro".
    AUTOMATICAS = frozenset(
        {
            Acao.PAGADOR_REMOVIDO,
            Acao.ACESSO_REMOVIDO,
            Acao.CANCELADA_AUTOMATICAMENTE,
            Acao.ACESSO_PRESERVADO,
        }
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lancamento = models.ForeignKey(Lancamento, on_delete=models.CASCADE, related_name="historico")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    acao = models.CharField(max_length=30, choices=Acao.choices)
    dados = models.JSONField(default=dict, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["criado_em"]
        constraints = [
            models.CheckConstraint(condition=Q(acao__in=Acao.values), name="historico_acao_valida")
        ]

    def __str__(self):
        return f"{self.acao} em {self.lancamento}"

    @property
    def automatica(self):
        # Recurrence creation is system-authored and records the server-generated competence.
        # A deleted author of an ordinary creation is still an ex-member, not the system.
        return self.acao in self.AUTOMATICAS or (
            self.acao == Acao.CRIADA and self.usuario_id is None and "competencia" in self.dados
        )
