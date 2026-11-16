from dataclasses import asdict

from rest_framework import serializers

from .models import TipoInstrumento
from .parser import ErroValidacao, ler


class TextoPagamentoField(serializers.CharField):
    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail("invalid")
        return super().to_internal_value(data)


class InstrumentoEntradaSerializer(serializers.Serializer):
    codigo = TextoPagamentoField(max_length=4096, required=False, trim_whitespace=False)
    chave_pix = TextoPagamentoField(max_length=77, required=False, trim_whitespace=False)

    def validate(self, attrs):
        if len(attrs) != 1:
            raise serializers.ValidationError("Informe somente código ou chave Pix.")
        return attrs


class InstrumentoSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(TipoInstrumento.choices)
    codigo = serializers.CharField(allow_null=True)
    chave_pix = serializers.CharField(allow_null=True)
    beneficiario = serializers.CharField(allow_null=True)


class LeituraSerializer(serializers.Serializer):
    instrumento = InstrumentoSerializer()
    valor_centavos = serializers.IntegerField(allow_null=True)
    vencimento = serializers.DateField(allow_null=True)
    vencimentos_possiveis = serializers.ListField(child=serializers.DateField())
    avisos = serializers.ListField(child=serializers.CharField())


def ler_entrada(entrada):
    try:
        return ler(**entrada)
    except ErroValidacao as exc:
        raise serializers.ValidationError({"instrumento": [str(exc)]}) from exc


def dados_instrumento(resultado):
    return {
        k: v
        for k, v in asdict(resultado).items()
        if k in ("tipo", "codigo", "chave_pix", "beneficiario")
    }
