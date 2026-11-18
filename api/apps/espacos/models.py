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


class Icone(models.TextChoices):
    """COR-04: a category picks one of these; names match web/src/components/ui/icon.tsx."""

    CASA = "casa", "Casa"
    LUZ = "luz", "Luz"
    AGUA = "agua", "Água"
    INTERNET = "internet", "Internet"
    TELEFONE = "telefone", "Telefone"
    CARRO = "carro", "Carro"
    MERCADO = "mercado", "Mercado"
    SAUDE = "saude", "Saúde"
    EDUCACAO = "educacao", "Educação"
    CARTAO = "cartao", "Cartão"
    TRABALHO = "trabalho", "Trabalho"
    LAZER = "lazer", "Lazer"
    PET = "pet", "Pet"
    CONTAS = "contas", "Outras"


class Subgrupo(models.Model):
    """A category ("categoria", formerly "casa") of a group (CU04, COR-04); table name kept."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    espaco = models.ForeignKey(Espaco, on_delete=models.CASCADE, related_name="subgrupos")
    nome = models.CharField(max_length=150)
    icone = models.CharField(max_length=20, choices=Icone.choices, default=Icone.CASA)
    arquivado = models.BooleanField(default=False)
    # COR-10 / ADR 0017: False = each role's default (the rule before COR-10); True = the
    # admin's per-member grants in PermissaoCategoria. `versao` detects concurrent edits.
    personalizada = models.BooleanField(default=False)
    versao = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.nome


class PermissaoCategoria(models.Model):
    """What one member (membro/observador) may do in a personalised category (ADR 0017)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subgrupo = models.ForeignKey(Subgrupo, on_delete=models.CASCADE, related_name="permissoes")
    membro = models.ForeignKey(
        Membro, on_delete=models.CASCADE, related_name="permissoes_categoria"
    )
    ver = models.BooleanField(default=False)
    criar = models.BooleanField(default=False)
    editar = models.BooleanField(default=False)
    pagar = models.BooleanField(default=False)
    recorrencias = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["subgrupo", "membro"], name="permissao_categoria_unica"
            ),
            models.CheckConstraint(
                condition=models.Q(ver=True)
                | models.Q(criar=False, editar=False, pagar=False, recorrencias=False),
                name="permissao_categoria_exige_ver",
            ),
        ]

    def __str__(self):
        return f"Permissões de {self.membro_id} em {self.subgrupo_id}"


class HistoricoPermissao(models.Model):
    """Who changed a category's permissions, when, and the before/after (ADR 0017)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subgrupo = models.ForeignKey(Subgrupo, on_delete=models.CASCADE, related_name="+")
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    antes = models.JSONField()
    depois = models.JSONField()

    def __str__(self):
        return f"Permissões de {self.subgrupo_id} em {self.criado_em}"
