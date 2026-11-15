from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.espacos.models import Espaco


class EspacoPessoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Espaco
        fields = ["id", "tipo", "nome"]


class MeSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    nome = serializers.CharField()
    email = serializers.EmailField()
    espaco_pessoal = EspacoPessoalSerializer()


@extend_schema(
    responses=MeSerializer,
    examples=[
        OpenApiExample(
            "Dados próprios",
            value={
                "id": "6fd32f1c-6f80-4b01-b491-25aeb00a180e",
                "nome": "Ana",
                "email": "ana@example.com",
                "espaco_pessoal": {
                    "id": "ae779d06-431b-48fc-b75e-66ff8a7a60e7",
                    "tipo": "pessoal",
                    "nome": "Pessoal",
                },
            },
        )
    ],
)
@api_view(["GET"])
def me(request):
    espaco = Espaco.objects.get(dono=request.user, tipo=Espaco.Tipo.PESSOAL)
    response = Response(
        MeSerializer(
            {
                "id": request.user.id,
                "nome": request.user.nome,
                "email": request.user.email,
                "espaco_pessoal": espaco,
            }
        ).data
    )
    response["Cache-Control"] = "private, no-store"
    return response
