from django.db import transaction
from drf_spectacular.utils import extend_schema, extend_schema_field
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.boletos.serializers import InstrumentoEntradaSerializer
from apps.espacos.acesso import espaco_ou_404, pode, recorrencias_visiveis
from apps.lancamentos.models import Visibilidade
from apps.lancamentos.views import CentavosField, ContaDetalheSerializer, _detalhe

from . import servicos
from .models import Recorrencia


class OcorrenciaInicialSerializer(serializers.Serializer):
    valor_centavos = CentavosField(min_value=1, max_value=2_147_483_647)
    vencimento = serializers.DateField()
    instrumento = InstrumentoEntradaSerializer(allow_null=True, required=False)
    documento_pdf = serializers.UUIDField(allow_null=True, required=False)
    data_emissao = serializers.DateField(allow_null=True, required=False)
    beneficiario = serializers.CharField(
        max_length=200, allow_null=True, allow_blank=True, required=False
    )


class RecorrenciaEntradaSerializer(serializers.Serializer):
    descricao = serializers.CharField(max_length=150)
    dia_vencimento = serializers.IntegerField(min_value=1, max_value=31)
    valor_tipo = serializers.ChoiceField(Recorrencia.ValorTipo.choices)
    valor_centavos = CentavosField(
        min_value=1, max_value=2_147_483_647, allow_null=True, required=False
    )
    subgrupo = serializers.UUIDField(allow_null=True, required=False)
    pagador = serializers.UUIDField(allow_null=True, required=False)
    visibilidade = serializers.ChoiceField(Visibilidade.choices, required=False)
    acesso = serializers.ListField(child=serializers.UUIDField(), required=False, max_length=50)


class CriarRecorrenciaSerializer(RecorrenciaEntradaSerializer):
    chave_idempotencia = serializers.UUIDField()
    ocorrencia_inicial = OcorrenciaInicialSerializer(required=False, allow_null=True)


class RecorrenciaSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    espaco_id = serializers.UUIDField()
    descricao = serializers.CharField()
    dia_vencimento = serializers.IntegerField()
    valor_tipo = serializers.ChoiceField(Recorrencia.ValorTipo.choices)
    valor_centavos = serializers.IntegerField(allow_null=True)
    subgrupo = serializers.UUIDField(source="subgrupo_id", allow_null=True)
    pagador = serializers.UUIDField(source="pagador_id", allow_null=True)
    visibilidade = serializers.ChoiceField(Visibilidade.choices)
    acesso = serializers.SerializerMethodField()
    estado = serializers.ChoiceField(Recorrencia.Estado.choices)
    motivo_pausa = serializers.CharField(allow_blank=True)
    criado_em = serializers.DateTimeField()
    pode_editar = serializers.SerializerMethodField()
    pode_pausar = serializers.SerializerMethodField()
    pode_retomar = serializers.SerializerMethodField()
    pode_encerrar = serializers.SerializerMethodField()

    @extend_schema_field(serializers.ListField(child=serializers.UUIDField()))
    def get_acesso(self, obj):
        return list(obj.acesso.values_list("pk", flat=True))

    def _edita(self, obj):
        return pode(self.context["papel"], "editar_conta")

    def get_pode_editar(self, obj) -> bool:
        return self._edita(obj) and obj.estado != Recorrencia.Estado.ENCERRADA

    def get_pode_pausar(self, obj) -> bool:
        return self._edita(obj) and obj.estado == Recorrencia.Estado.ATIVA

    def get_pode_retomar(self, obj) -> bool:
        return self._edita(obj) and obj.estado == Recorrencia.Estado.PAUSADA

    def get_pode_encerrar(self, obj) -> bool:
        return self._edita(obj) and obj.estado != Recorrencia.Estado.ENCERRADA


class CriacaoResultadoSerializer(serializers.Serializer):
    recorrencia = RecorrenciaSerializer()
    ocorrencia = ContaDetalheSerializer(allow_null=True)


def _modelo(modelo, request):
    return RecorrenciaSerializer(
        modelo, context={"request": request, "papel": modelo.espaco.meu_papel}
    ).data


class RecorrenciasView(APIView):
    @extend_schema(
        operation_id="recorrencias_listar", responses={200: RecorrenciaSerializer(many=True)}
    )
    @transaction.atomic
    def get(self, request, espaco_id):
        espaco = espaco_ou_404(request.user, espaco_id)
        servicos.travar_espaco(request.user, espaco)
        espaco = espaco_ou_404(request.user, espaco_id)
        modelos = (
            recorrencias_visiveis(request.user, espaco)
            .select_related("espaco")
            .order_by("criado_em", "pk")
        )
        return Response(
            RecorrenciaSerializer(
                modelos, many=True, context={"request": request, "papel": espaco.meu_papel}
            ).data
        )

    @extend_schema(
        operation_id="recorrencias_criar",
        request=CriarRecorrenciaSerializer,
        responses={201: CriacaoResultadoSerializer, 200: CriacaoResultadoSerializer},
    )
    @transaction.atomic
    def post(self, request, espaco_id):
        espaco = espaco_ou_404(request.user, espaco_id, "criar_conta")
        entrada = CriarRecorrenciaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        modelo, conta, criado = servicos.criar(request.user, espaco, entrada.validated_data)
        detalhe = _detalhe(request, conta.pk, modelo.espaco).data if conta else None
        return Response(
            {"recorrencia": _modelo(modelo, request), "ocorrencia": detalhe},
            status=status.HTTP_201_CREATED if criado else status.HTTP_200_OK,
        )


class RecorrenciaView(APIView):
    @extend_schema(operation_id="recorrencias_detalhe", responses={200: RecorrenciaSerializer})
    @transaction.atomic
    def get(self, request, recorrencia_id):
        modelo = servicos.travar_modelo(request.user, recorrencia_id)
        return Response(_modelo(modelo, request))

    @extend_schema(
        operation_id="recorrencias_editar",
        request=RecorrenciaEntradaSerializer(partial=True),
        responses={200: RecorrenciaSerializer},
    )
    @transaction.atomic
    def patch(self, request, recorrencia_id):
        from apps.espacos.acesso import recorrencia_ou_404

        recorrencia_ou_404(request.user, recorrencia_id, "editar_conta")
        entrada = RecorrenciaEntradaSerializer(data=request.data, partial=True)
        entrada.is_valid(raise_exception=True)
        modelo = servicos.editar_modelo(request.user, recorrencia_id, entrada.validated_data)
        return Response(_modelo(modelo, request))


class AcaoView(APIView):
    acao = None

    @extend_schema(
        operation_id="recorrencias_transicao", request=None, responses={200: RecorrenciaSerializer}
    )
    @transaction.atomic
    def post(self, request, recorrencia_id):
        modelo = servicos.transicao(request.user, recorrencia_id, self.acao)
        return Response(_modelo(modelo, request))


class PausarView(AcaoView):
    acao = "pausar"

    @extend_schema(
        operation_id="recorrencias_pausar", request=None, responses={200: RecorrenciaSerializer}
    )
    def post(self, request, recorrencia_id):
        return super().post(request, recorrencia_id)


class RetomarView(AcaoView):
    acao = "retomar"

    @extend_schema(
        operation_id="recorrencias_retomar", request=None, responses={200: RecorrenciaSerializer}
    )
    def post(self, request, recorrencia_id):
        return super().post(request, recorrencia_id)


class EncerrarView(AcaoView):
    acao = "encerrar"

    @extend_schema(
        operation_id="recorrencias_encerrar", request=None, responses={200: RecorrenciaSerializer}
    )
    def post(self, request, recorrencia_id):
        return super().post(request, recorrencia_id)
