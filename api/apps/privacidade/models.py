import uuid

from django.db import models


class RevisaoExportacao(models.Model):
    # A single transactional counter invalidates every affected export on mutation.
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    epoca = models.UUIDField(default=uuid.uuid4, editable=False)
    valor = models.PositiveBigIntegerField(default=0)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(id=1), name="revisao_unica")]

    def __str__(self):
        return "Revisão de exportação"


class Exportacao(models.Model):
    class Estado(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        PROCESSANDO = "processando", "Processando"
        PRONTO = "pronto", "Pronto"
        FALHOU = "falhou", "Falhou"
        EXPIRADO = "expirado", "Expirado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey("contas_usuario.Usuario", on_delete=models.CASCADE)
    chave = models.UUIDField()
    corpo_hash = models.CharField(max_length=64)
    criado_em = models.DateTimeField(auto_now_add=True)
    expira_em = models.DateTimeField()
    estado = models.CharField(max_length=16, choices=Estado.choices, default=Estado.PENDENTE)
    geracao = models.PositiveIntegerField(default=0)
    tentativa = models.UUIDField(null=True)
    lease_ate = models.DateTimeField(null=True)
    epoca = models.UUIDField(null=True)
    revisao = models.PositiveBigIntegerField(null=True)
    objeto_id = models.UUIDField(null=True)
    formato_interno = models.PositiveSmallIntegerField(default=0)
    artefato_sha256 = models.CharField(max_length=64, blank=True)
    manifestos = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["usuario", "chave"], name="exportacao_chave_unica")
        ]

    def __str__(self):
        return f"Exportação {self.pk}"


class IntencaoExclusao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey("contas_usuario.Usuario", on_delete=models.CASCADE)
    segredo_hash = models.CharField(max_length=64)
    sessao_hash = models.CharField(max_length=64)
    expira_em = models.DateTimeField()
    consumida_em = models.DateTimeField(null=True)

    def __str__(self):
        return f"Intenção {self.pk}"


class OperacaoExclusao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Independent of the deleted identity and never an email-derived identifier.
    owner_id = models.UUIDField(db_index=True)
    intencao_id = models.UUIDField(db_index=True, null=True)
    estado = models.CharField(max_length=16, default="preparada")
    fence = models.PositiveBigIntegerField(default=1)
    recibo_prepare = models.JSONField(null=True)
    recibo_terminal = models.JSONField(null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Operação {self.pk}"


class ParteExportacao(models.Model):
    exportacao = models.ForeignKey(Exportacao, on_delete=models.CASCADE, related_name="partes")
    tentativa = models.UUIDField()
    categoria = models.CharField(max_length=32)
    cursor = models.CharField(max_length=36)
    dados = models.JSONField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["exportacao", "tentativa", "categoria", "cursor"],
                name="exportacao_parte_unica",
            )
        ]

    def __str__(self):
        return "Parte de exportação"


class LimpezaExportacao(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    geracao = models.PositiveBigIntegerField(default=1)
    incerta = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Limpeza de exportação"


class MarcaRestauracao(models.Model):
    operation_id = models.UUIDField(primary_key=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Marca de restauração"


class ExecucaoRestauracao(models.Model):
    operation_id = models.UUIDField(primary_key=True)
    fence_id = models.UUIDField()
    journal_seq = models.PositiveBigIntegerField()
    journal_record_mac = models.CharField(max_length=64)
    target_lsn = models.CharField(max_length=32)
    prova_sha256 = models.CharField(max_length=64)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Execução de restauração"
