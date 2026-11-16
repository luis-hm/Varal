from django.db import models
from django.db.models import Q


class TipoInstrumento(models.TextChoices):
    BOLETO_BANCARIO = "boleto_bancario", "Boleto bancário"
    BOLETO_ARRECADACAO = "boleto_arrecadacao", "Boleto de arrecadação"
    PIX = "pix", "Pix"


class Instrumento(models.Model):
    """Payment payload owned by one bill; read access always comes from that bill."""

    lancamento = models.OneToOneField(
        "lancamentos.Lancamento",
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="instrumento",
    )
    tipo = models.CharField(max_length=20, choices=TipoInstrumento.choices)
    # NULL is the sole representation of an absent payload; the XOR constraint forbids "".
    codigo = models.CharField(max_length=4096, null=True, blank=True)  # noqa: DJ001
    chave_pix = models.CharField(max_length=77, null=True, blank=True)  # noqa: DJ001
    beneficiario = models.CharField(max_length=25, null=True, blank=True)  # noqa: DJ001

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="instrumento_tipo_conteudo_valido",
                condition=(
                    Q(
                        tipo=TipoInstrumento.BOLETO_BANCARIO,
                        codigo__regex=r"^[0-9]{47}$",
                        codigo__isnull=False,
                        chave_pix__isnull=True,
                    )
                    | Q(
                        tipo=TipoInstrumento.BOLETO_ARRECADACAO,
                        codigo__regex=r"^8[0-9]{47}$",
                        codigo__isnull=False,
                        chave_pix__isnull=True,
                    )
                    | (
                        Q(tipo=TipoInstrumento.PIX)
                        & (
                            (Q(codigo__isnull=False, chave_pix__isnull=True) & ~Q(codigo=""))
                            | (Q(codigo__isnull=True, chave_pix__isnull=False) & ~Q(chave_pix=""))
                        )
                    )
                ),
            )
        ]

    def __str__(self):
        # Never put the payload/key into cascade previews or incidental logs.
        return f"Instrumento ({self.get_tipo_display()})"
