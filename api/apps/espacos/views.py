from django.conf import settings
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_field,
)
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from . import servicos
from .acesso import espaco_ou_404, espacos_do_usuario, pode
from .models import Espaco, Membro, Papel, Subgrupo

GRUPO_ID = "1b4e28ba-2fa1-11d2-883f-0016d3cca427"
MEMBRO_ID = "6fd32f1c-6f80-4b01-b491-25aeb00a180e"
CASA_ID = "ae779d06-431b-48fc-b75e-66ff8a7a60e7"
CONVITE_ID = "9a1f7c2e-5b3d-4e8a-9c6f-0d2b4a7e1f35"
EXPIRA = "2026-11-21T12:00:00Z"


# ---- serializers ---------------------------------------------------------------------------


class ErroSerializer(serializers.Serializer):
    detail = serializers.CharField()


class GrupoResumoSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    nome = serializers.CharField()
    papel = serializers.ChoiceField(Papel.choices, source="meu_papel")


class GrupoListaSerializer(GrupoResumoSerializer):
    membros_qtd = serializers.IntegerField(allow_null=True)
    casas_qtd = serializers.IntegerField(allow_null=True)

    def to_representation(self, obj):
        data = super().to_representation(obj)
        if not pode(obj.meu_papel, "ver_grupo"):  # the payer sees only the name (RN07)
            data["membros_qtd"] = data["casas_qtd"] = None
        return data


class CriarGrupoSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=150)
    casas = serializers.ListField(
        child=serializers.CharField(max_length=150), required=False, default=list, max_length=20
    )


class MembroSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(source="usuario.nome", read_only=True)
    email = serializers.EmailField(source="usuario.email", read_only=True)
    sou_eu = serializers.SerializerMethodField()

    class Meta:
        model = Membro
        fields = ["id", "nome", "email", "papel", "sou_eu"]

    def get_sou_eu(self, obj) -> bool:
        return obj.usuario_id == self.context["request"].user.pk


class CasaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subgrupo
        fields = ["id", "nome", "arquivado"]


class GrupoDetalheSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    nome = serializers.CharField()
    meu_papel = serializers.ChoiceField(Papel.choices)
    membros = serializers.SerializerMethodField()
    casas = serializers.SerializerMethodField()

    @extend_schema_field(MembroSerializer(many=True))
    def get_membros(self, grupo):
        membros = grupo.membros.select_related("usuario").order_by("criado_em")
        return MembroSerializer(membros, many=True, context=self.context).data

    @extend_schema_field(CasaSerializer(many=True))
    def get_casas(self, grupo):
        return CasaSerializer(
            grupo.subgrupos.filter(arquivado=False).order_by("nome"), many=True
        ).data


class PapelSerializer(serializers.Serializer):
    papel = serializers.ChoiceField(Papel.choices)


class ConviteCriadoSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    url = serializers.URLField()
    expira_em = serializers.DateTimeField()
    papel = serializers.ChoiceField(Papel.choices)


class ConvitePendenteSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    papel = serializers.ChoiceField(Papel.choices)
    criado_em = serializers.DateTimeField()
    expira_em = serializers.DateTimeField()
    criado_por_nome = serializers.SerializerMethodField()

    def get_criado_por_nome(self, obj) -> str | None:
        return obj.criado_por and (obj.criado_por.nome or obj.criado_por.email)


class ConvitePublicoSerializer(serializers.Serializer):
    grupo_nome = serializers.CharField(source="espaco.nome")
    papel = serializers.ChoiceField(Papel.choices)
    expira_em = serializers.DateTimeField()


class AceiteSerializer(serializers.Serializer):
    grupo_id = serializers.UUIDField(source="espaco_id")
    papel = serializers.ChoiceField(Papel.choices)


# ---- views ---------------------------------------------------------------------------------


def _grupo(request, grupo_id, acao=None):
    return espaco_ou_404(request.user, grupo_id, acao, tipo=Espaco.Tipo.GRUPO)


def _erros(*codes):
    textos = {
        403: "Seu papel não permite esta ação.",
        404: "Grupo, membro, casa ou convite fora do seu acesso.",
        409: "Regra de negócio (ex.: RN04, o grupo ficaria sem admin).",
        410: "Convite inexistente, expirado, usado ou revogado.",
        429: "Limite de tentativas de aceite (10 por hora).",
    }
    return {code: OpenApiResponse(ErroSerializer, description=textos[code]) for code in codes}


DETALHE_EXEMPLO = OpenApiExample(
    "Grupo visto pelo admin",
    value={
        "id": GRUPO_ID,
        "nome": "Família Martins",
        "meu_papel": "admin",
        "membros": [
            {
                "id": MEMBRO_ID,
                "nome": "Ana",
                "email": "ana@example.com",
                "papel": "admin",
                "sou_eu": True,
            }
        ],
        "casas": [{"id": CASA_ID, "nome": "Casa da praia", "arquivado": False}],
    },
    response_only=True,
)


class GruposView(APIView):
    @extend_schema(
        operation_id="grupos_listar",
        summary="Grupos do usuário (RN01)",
        responses={200: GrupoListaSerializer(many=True)},
        examples=[
            OpenApiExample(
                "Admin e pagador",
                value=[
                    {
                        "id": GRUPO_ID,
                        "nome": "Família",
                        "papel": "admin",
                        "membros_qtd": 4,
                        "casas_qtd": 2,
                    },
                    {
                        "id": CASA_ID,
                        "nome": "Condomínio",
                        "papel": "pagador",
                        "membros_qtd": None,
                        "casas_qtd": None,
                    },
                ],
            )
        ],
    )
    def get(self, request):
        grupos = (
            espacos_do_usuario(request.user)
            .filter(tipo=Espaco.Tipo.GRUPO)
            .annotate(
                membros_qtd=Count("membros", distinct=True),
                casas_qtd=Count("subgrupos", filter=Q(subgrupos__arquivado=False), distinct=True),
            )
            .order_by("nome")
        )
        return Response(GrupoListaSerializer(grupos, many=True).data)

    @extend_schema(
        operation_id="grupos_criar",
        summary="Criar grupo; o criador vira o único admin (RF04, RN04)",
        request=CriarGrupoSerializer,
        responses={201: GrupoDetalheSerializer, 400: OpenApiResponse(description="Nome vazio")},
        examples=[
            OpenApiExample(
                "Com casas",
                value={"nome": "Família Martins", "casas": ["Casa da praia"]},
                request_only=True,
            ),
            DETALHE_EXEMPLO,
        ],
    )
    def post(self, request):
        entrada = CriarGrupoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        grupo = servicos.criar_grupo(request.user, **entrada.validated_data)
        grupo = _grupo(request, grupo.pk)
        data = GrupoDetalheSerializer(grupo, context={"request": request}).data
        return Response(data, status=status.HTTP_201_CREATED)


class GrupoView(APIView):
    @extend_schema(
        operation_id="grupos_detalhe",
        summary="Página do grupo: admin, membro e observador (pagador recebe 403)",
        responses={200: GrupoDetalheSerializer, **_erros(403, 404)},
        examples=[DETALHE_EXEMPLO],
    )
    def get(self, request, grupo_id):
        grupo = _grupo(request, grupo_id, "ver_grupo")
        return Response(GrupoDetalheSerializer(grupo, context={"request": request}).data)


class SairView(APIView):
    @extend_schema(
        operation_id="grupos_sair",
        summary="Sair do grupo (qualquer papel; RN04, RN21)",
        request=None,
        responses={204: None, **_erros(404, 409)},
    )
    def post(self, request, grupo_id):
        servicos.sair(request.user, _grupo(request, grupo_id))
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConvitesView(APIView):
    @extend_schema(
        operation_id="grupos_convites_listar",
        summary="Convites pendentes (admin)",
        responses={200: ConvitePendenteSerializer(many=True), **_erros(403, 404)},
        examples=[
            OpenApiExample(
                "Um pendente",
                value=[
                    {
                        "id": CONVITE_ID,
                        "papel": "pagador",
                        "criado_em": "2026-11-14T12:00:00Z",
                        "expira_em": EXPIRA,
                        "criado_por_nome": "Ana",
                    }
                ],
            )
        ],
    )
    def get(self, request, grupo_id):
        grupo = _grupo(request, grupo_id, "gerenciar_grupo")
        convites = servicos.convites_pendentes(grupo).select_related("criado_por")
        return Response(ConvitePendenteSerializer(convites.order_by("-criado_em"), many=True).data)

    @extend_schema(
        operation_id="grupos_convites_criar",
        summary="Gerar link de convite (admin; RN24, RN31). O link só aparece nesta resposta.",
        request=PapelSerializer,
        responses={201: ConviteCriadoSerializer, **_erros(403, 404)},
        examples=[
            OpenApiExample("Pagador", value={"papel": "pagador"}, request_only=True),
            OpenApiExample(
                "Link gerado",
                value={
                    "id": CONVITE_ID,
                    "url": "https://varal.app/c/9fKq2mXbExemploDeTokenNaoReal0000000000R4dT",
                    "expira_em": EXPIRA,
                    "papel": "pagador",
                },
                response_only=True,
            ),
        ],
    )
    def post(self, request, grupo_id):
        grupo = _grupo(request, grupo_id, "gerenciar_grupo")
        entrada = PapelSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        convite, token = servicos.gerar_convite(
            request.user, grupo, entrada.validated_data["papel"]
        )
        data = {
            "id": convite.id,
            "url": f"{settings.FRONTEND_URL}/c/{token}",
            "expira_em": convite.expira_em,
            "papel": convite.papel,
        }
        return Response(ConviteCriadoSerializer(data).data, status=status.HTTP_201_CREATED)


class ConviteView(APIView):
    @extend_schema(
        operation_id="grupos_convites_revogar",
        summary="Revogar convite pendente (admin; RN31)",
        responses={204: None, **_erros(403, 404)},
    )
    def delete(self, request, grupo_id, convite_id):
        servicos.revogar_convite(_grupo(request, grupo_id, "gerenciar_grupo"), convite_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConvitePublicoView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="convites_ver",
        summary="Abrir link de convite (sem sessão)",
        responses={200: ConvitePublicoSerializer, **_erros(410)},
        examples=[
            OpenApiExample(
                "Válido",
                value={"grupo_nome": "Família Martins", "papel": "pagador", "expira_em": EXPIRA},
            )
        ],
    )
    def get(self, request, token):
        return Response(ConvitePublicoSerializer(servicos.convite_valido(token)).data)


class AceitarConviteView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "convite_aceite"  # RN31: 10/hour per user, every attempt counts

    @extend_schema(
        operation_id="convites_aceitar",
        summary="Aceitar convite (exige sessão; uso único; 10 tentativas por hora)",
        request=None,
        responses={201: AceiteSerializer, **_erros(409, 410, 429)},
        examples=[OpenApiExample("Aceito", value={"grupo_id": GRUPO_ID, "papel": "pagador"})],
    )
    def post(self, request, token):
        membro = servicos.aceitar_convite(request.user, token)
        return Response(AceiteSerializer(membro).data, status=status.HTTP_201_CREATED)


class MembroView(APIView):
    @extend_schema(
        operation_id="grupos_membros_alterar_papel",
        summary="Alterar papel de um membro (admin; RN04)",
        request=PapelSerializer,
        responses={200: MembroSerializer, **_erros(403, 404, 409)},
        examples=[OpenApiExample("Virar admin", value={"papel": "admin"}, request_only=True)],
    )
    def patch(self, request, grupo_id, membro_id):
        grupo = _grupo(request, grupo_id, "gerenciar_grupo")
        entrada = PapelSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        membro = servicos.alterar_papel(grupo, membro_id, entrada.validated_data["papel"])
        return Response(MembroSerializer(membro, context={"request": request}).data)

    @extend_schema(
        operation_id="grupos_membros_remover",
        summary="Remover membro (admin; RN04, RN21)",
        responses={204: None, **_erros(403, 404, 409)},
    )
    def delete(self, request, grupo_id, membro_id):
        servicos.remover_membro(_grupo(request, grupo_id, "gerenciar_grupo"), membro_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubgruposView(APIView):
    @extend_schema(
        operation_id="grupos_casas_criar",
        summary="Criar casa (admin; CU04)",
        request=CasaSerializer,
        responses={201: CasaSerializer, **_erros(403, 404)},
        examples=[
            OpenApiExample("Nova casa", value={"nome": "Casa da praia"}, request_only=True),
            OpenApiExample(
                "Criada",
                value={"id": CASA_ID, "nome": "Casa da praia", "arquivado": False},
                response_only=True,
            ),
        ],
    )
    def post(self, request, grupo_id):
        grupo = _grupo(request, grupo_id, "gerenciar_grupo")
        entrada = CasaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        entrada.save(espaco=grupo)
        return Response(entrada.data, status=status.HTTP_201_CREATED)


class SubgrupoView(APIView):
    @extend_schema(
        operation_id="grupos_casas_alterar",
        summary="Renomear ou arquivar casa (admin; CU04). Arquivada sai da lista e fica no banco.",
        request=CasaSerializer(partial=True),
        responses={200: CasaSerializer, **_erros(403, 404)},
        examples=[OpenApiExample("Arquivar", value={"arquivado": True}, request_only=True)],
    )
    def patch(self, request, grupo_id, casa_id):
        grupo = _grupo(request, grupo_id, "gerenciar_grupo")
        casa = get_object_or_404(Subgrupo, espaco=grupo, pk=casa_id)
        entrada = CasaSerializer(casa, data=request.data, partial=True)
        entrada.is_valid(raise_exception=True)
        entrada.save()
        return Response(entrada.data)
