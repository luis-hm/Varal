"""Validate payment data and prepare atomic instrument changes for bill services."""

from dataclasses import dataclass

from rest_framework.exceptions import ValidationError

from apps.espacos.servicos import Conflito
from apps.lancamentos.models import ABERTOS

from .models import Instrumento
from .serializers import dados_instrumento, ler_entrada

AUSENTE = object()


@dataclass(frozen=True)
class AlteracaoInstrumento:
    dados: dict | None
    mudou: bool
    tipo_anterior: str

    @property
    def historico(self):
        if not self.mudou:
            return {}
        return {
            "instrumento": [self.tipo_anterior, self.dados["tipo"] if self.dados else "manual"],
            "codigo_alterado": True,
        }


def preparar(dados, conta=None):
    """Reparse both new and preserved instruments; never trust preview-derived fields.

    Mutates only the local input dict. Persistence is done after the bill's validations and
    under the caller's row lock/transaction, so invalid input never leaves a partial change.
    """
    entrada = dados.pop("instrumento", AUSENTE)
    atual = Instrumento.objects.filter(lancamento=conta).first() if conta else None
    anterior = (
        {campo: getattr(atual, campo) for campo in ("tipo", "codigo", "chave_pix", "beneficiario")}
        if atual
        else None
    )
    tipo_anterior = atual.tipo if atual else "manual"
    if (entrada is AUSENTE and atual is None) or entrada is None:
        alteracao = AlteracaoInstrumento(None, atual is not None, tipo_anterior)
    else:
        if entrada is AUSENTE:
            entrada = {"codigo": atual.codigo} if atual.codigo else {"chave_pix": atual.chave_pix}
        resultado = ler_entrada(entrada)
        novo = dados_instrumento(resultado)
        mudou = novo != anterior
        if resultado.valor_centavos is not None:
            if not 0 < resultado.valor_centavos <= 2**31 - 1:
                raise ValidationError({"valor_centavos": ["Valor fora do limite da conta."]})
            if "valor_centavos" in dados and dados["valor_centavos"] != resultado.valor_centavos:
                raise ValidationError({"valor_centavos": ["Valor diferente do código informado."]})
            dados["valor_centavos"] = resultado.valor_centavos
        possiveis = resultado.vencimentos_possiveis
        if possiveis:
            if mudou and len(possiveis) == 1 and "vencimento" not in dados:
                dados["vencimento"] = resultado.vencimento
            vencimento = dados.get("vencimento", conta.vencimento if conta else None)
            if len(possiveis) > 1 and mudou and "vencimento" not in dados:
                raise ValidationError({"vencimento": ["Confira e informe o vencimento do boleto."]})
            if vencimento is None:
                dados["vencimento"] = resultado.vencimento
            elif vencimento not in possiveis:
                raise ValidationError({"vencimento": ["Vencimento diferente do código informado."]})
        alteracao = AlteracaoInstrumento(novo, mudou, tipo_anterior)
    if alteracao.mudou and conta and conta.status not in ABERTOS:
        raise Conflito("Só conta aguardando boleto ou pendente pode trocar o código de pagamento.")
    return alteracao


def aplicar(conta, alteracao):
    if not alteracao.mudou:
        return
    if alteracao.dados is None:
        Instrumento.objects.filter(lancamento=conta).delete()
    else:
        Instrumento.objects.update_or_create(lancamento=conta, defaults=alteracao.dados)
