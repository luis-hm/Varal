from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.espacos.acesso import espacos_do_usuario
from apps.espacos.models import Espaco
from apps.espacos.views import GrupoResumoSerializer
from apps.privacidade.views import ConfirmacaoExclusaoSerializer, ReauthRespostaSerializer


class EspacoPessoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Espaco
        fields = ["id", "tipo", "nome"]


class MeSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    nome = serializers.CharField()
    email = serializers.EmailField()
    espaco_pessoal = EspacoPessoalSerializer()
    grupos = GrupoResumoSerializer(many=True)


@extend_schema(
    methods=["GET"],
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
                "grupos": [
                    {
                        "id": "1b4e28ba-2fa1-11d2-883f-0016d3cca427",
                        "nome": "Família",
                        "papel": "admin",
                    }
                ],
            },
        )
    ],
)
@extend_schema(
    methods=["DELETE"],
    operation_id="privacidade_excluir_conta",
    request=ConfirmacaoExclusaoSerializer,
    responses={204: None, 401: ReauthRespostaSerializer},
)
@api_view(["GET", "DELETE"])
def me(request):
    if request.method == "DELETE":
        from apps.privacidade.views import excluir_me

        return excluir_me(request)
    espaco = Espaco.objects.get(dono=request.user, tipo=Espaco.Tipo.PESSOAL)
    response = Response(
        MeSerializer(
            {
                "id": request.user.id,
                "nome": request.user.nome,
                "email": request.user.email,
                "espaco_pessoal": espaco,
                # Only the user's own groups, for the space selector (RN01).
                "grupos": espacos_do_usuario(request.user)
                .filter(tipo=Espaco.Tipo.GRUPO)
                .order_by("nome"),
            }
        ).data
    )
    response["Cache-Control"] = "private, no-store"
    return response


class GoogleTicketEntradaSerializer(serializers.Serializer):
    ticket = serializers.UUIDField()
    tentativa = serializers.UUIDField()


class GoogleTicketSaidaSerializer(serializers.Serializer):
    id = serializers.UUIDField()


from rest_framework.views import APIView  # noqa: E402


class ConsumirTicketGoogleView(APIView):
    @extend_schema(
        operation_id="auth_google_consumir_ticket",
        request=GoogleTicketEntradaSerializer,
        responses={200: GoogleTicketSaidaSerializer, 409: None},
    )
    def post(self, request):
        from django.contrib.auth import HASH_SESSION_KEY, SESSION_KEY
        from django.contrib.sessions.models import Session
        from django.db import transaction
        from django.utils import timezone
        from django.utils.crypto import constant_time_compare

        from apps.contas_usuario.models import TicketGoogle, Usuario
        from apps.solicitacoes.coordenacao import barreira

        dados = GoogleTicketEntradaSerializer(data=request.data)
        dados.is_valid(raise_exception=True)
        with transaction.atomic():
            barreira()
            sessao = (
                Session.objects.select_for_update()
                .filter(session_key=request.session.session_key, expire_date__gt=timezone.now())
                .first()
            )
            user = Usuario.objects.filter(pk=request.user.pk, is_active=True).first()
            session_data = sessao.get_decoded() if sessao else {}
            if (
                not user
                or session_data.get(SESSION_KEY) != str(user.pk)
                or not constant_time_compare(
                    session_data.get(HASH_SESSION_KEY, ""), user.get_session_auth_hash()
                )
            ):
                return Response({"detail": "Retorno indisponível."}, status=409)
            ticket = (
                TicketGoogle.objects.select_for_update()
                .filter(
                    pk=dados.validated_data["ticket"],
                    usuario=user,
                    tentativa=dados.validated_data["tentativa"],
                    consumido_em__isnull=True,
                    expira_em__gt=timezone.now(),
                )
                .first()
            )
            if not ticket:
                return Response({"detail": "Retorno indisponível."}, status=409)
            ticket.consumido_em = timezone.now()
            ticket.save(update_fields=["consumido_em"])
        response = Response({"id": str(user.pk)})
        response["Cache-Control"] = "private, no-store"
        return response
