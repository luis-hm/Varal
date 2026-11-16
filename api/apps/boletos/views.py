from dataclasses import asdict

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.espacos.views import ErroSerializer

from .serializers import (
    InstrumentoEntradaSerializer,
    LeituraSerializer,
    dados_instrumento,
    ler_entrada,
)


class LerView(APIView):
    @extend_schema(
        operation_id="boletos_ler",
        summary="Conferir boleto/Pix sem gravar; não consulta URL nem titularidade (RF08/RF09)",
        request=InstrumentoEntradaSerializer,
        responses={200: LeituraSerializer, 400: ErroSerializer, 403: ErroSerializer},
        examples=[
            OpenApiExample("Chave Pix", value={"chave_pix": "+5585999999999"}, request_only=True),
            OpenApiExample(
                "Chave lida",
                value={
                    "instrumento": {
                        "tipo": "pix",
                        "codigo": None,
                        "chave_pix": "+5585999999999",
                        "beneficiario": None,
                    },
                    "valor_centavos": None,
                    "vencimento": None,
                    "vencimentos_possiveis": [],
                    "avisos": ["Chave não consultada; existência e titularidade não verificadas."],
                },
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        entrada = InstrumentoEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        resultado = ler_entrada(entrada.validated_data)
        dados = asdict(resultado)
        corpo = {
            "instrumento": dados_instrumento(resultado),
            **{
                k: dados[k]
                for k in ("valor_centavos", "vencimento", "vencimentos_possiveis", "avisos")
            },
        }
        return Response(LeituraSerializer(corpo).data)
