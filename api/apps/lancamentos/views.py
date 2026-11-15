import calendar
from datetime import date

from django.db.models import Count, Q, Sum
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_field,
)
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.espacos.acesso import espaco_ou_404, lancamento_ou_404, lancamentos_visiveis, pode
from apps.espacos.models import Espaco
from apps.espacos.views import ErroSerializer

from . import servicos
from .models import ABERTOS, STATUS_EXIBIDOS, VENCE, VENCIDA, Historico, Lancamento, Status
from .models import Visibilidade as Vis

ESPACO_ID = "1b4e28ba-2fa1-11d2-883f-0016d3cca427"
CONTA_ID = "3f2c8d4e-7a1b-4c5d-9e8f-0a1b2c3d4e5f"
CASA_ID = "ae779d06-431b-48fc-b75e-66ff8a7a60e7"
PESSOA_ID = "6fd32f1c-6f80-4b01-b491-25aeb00a180e"
OUTRA_ID = "c4a7d1e2-9b3f-4a6c-8d2e-1f0a9b8c7d6e"


# ---- serializers ---------------------------------------------------------------------------


def _nome(usuario):
    return usuario.nome or usuario.email


class RefSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    nome = serializers.CharField()


class EspacoRefSerializer(RefSerializer):
    tipo = serializers.ChoiceField(Espaco.Tipo.choices)


class PessoaSerializer(RefSerializer):
    sou_eu = serializers.BooleanField()


class CriadorSerializer(serializers.Serializer):
    nome = serializers.CharField()
    sou_eu = serializers.BooleanField()


def _pessoa(usuario, request):
    if usuario is None:
        return None
    return {"id": usuario.pk, "nome": _nome(usuario), "sou_eu": usuario.pk == request.user.pk}


class ContaSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    espaco = EspacoRefSerializer()
    descricao = serializers.CharField()
    valor_centavos = serializers.IntegerField()
    vencimento = serializers.DateField()
    status = serializers.ChoiceField(Status.choices)
    status_exibido = serializers.ChoiceField(STATUS_EXIBIDOS)
    dias_para_vencer = serializers.SerializerMethodField()
    subgrupo = RefSerializer(allow_null=True)
    pagador = serializers.SerializerMethodField()
    visibilidade = serializers.ChoiceField(Vis.choices)
    criado_em = serializers.DateTimeField()

    def get_dias_para_vencer(self, obj) -> int:
        return (obj.vencimento - timezone.localdate()).days

    @extend_schema_field(PessoaSerializer(allow_null=True))
    def get_pagador(self, obj):
        return _pessoa(obj.pagador, self.context["request"])


class HistoricoSerializer(serializers.Serializer):
    acao = serializers.ChoiceField(Historico.Acao.choices)
    automatica = serializers.SerializerMethodField()
    autor = serializers.SerializerMethodField(help_text="null em ação automática")
    sou_eu = serializers.SerializerMethodField()
    dados = serializers.DictField()
    criado_em = serializers.DateTimeField()

    def get_automatica(self, obj) -> bool:
        return obj.acao in Historico.AUTOMATICAS

    def get_autor(self, obj) -> str | None:
        if obj.acao in Historico.AUTOMATICAS:
            return None
        return _nome(obj.usuario) if obj.usuario else "Ex-membro"  # RN30

    def get_sou_eu(self, obj) -> bool:
        return obj.usuario_id == self.context["request"].user.pk


class ContaDetalheSerializer(ContaSerializer):
    criador = serializers.SerializerMethodField()
    acesso = serializers.SerializerMethodField()
    historico = HistoricoSerializer(many=True)
    pode_editar = serializers.SerializerMethodField()

    @extend_schema_field(CriadorSerializer)
    def get_criador(self, obj):
        if obj.criador is None:
            return {"nome": "Ex-membro", "sou_eu": False}  # RN30
        return {
            "nome": _nome(obj.criador),
            "sou_eu": obj.criador_id == self.context["request"].user.pk,
        }

    @extend_schema_field(RefSerializer(many=True))
    def get_acesso(self, obj):
        return [{"id": u.pk, "nome": _nome(u)} for u in obj.acesso.all()]

    def get_pode_editar(self, obj) -> bool:
        return obj.status != Status.CANCELADA and pode(self.context["papel"], "editar_conta")


class CentavosField(serializers.IntegerField):
    """RN11: whole cents only; 10.5, "10" or true are rejected (IntegerField would coerce)."""

    def to_internal_value(self, data):
        if isinstance(data, bool) or not isinstance(data, int):
            self.fail("invalid")
        return super().to_internal_value(data)


class ContaEntradaSerializer(serializers.Serializer):
    descricao = serializers.CharField(max_length=150)
    valor_centavos = CentavosField(min_value=1, max_value=2_147_483_647)
    vencimento = serializers.DateField()
    subgrupo = serializers.UUIDField(allow_null=True, required=False)
    pagador = serializers.UUIDField(allow_null=True, required=False)
    visibilidade = serializers.ChoiceField(Vis.choices, required=False)
    acesso = serializers.ListField(
        child=serializers.UUIDField(), required=False, max_length=50, help_text="Quem vê (restrita)"
    )


class ContagensSerializer(serializers.Serializer):
    todas = serializers.IntegerField()
    a_pagar = serializers.IntegerField()
    vencidas = serializers.IntegerField()
    pagas = serializers.IntegerField()
    canceladas = serializers.IntegerField()


class OpcoesSerializer(serializers.Serializer):
    casas = RefSerializer(many=True)
    pagadores = PessoaSerializer(many=True)
    sem_pagador = serializers.BooleanField()


class ListaSerializer(serializers.Serializer):
    mes = serializers.CharField(help_text="AAAA-MM do total e das contagens")
    total_centavos = serializers.IntegerField(help_text="Não canceladas do mês, com casa/pagador")
    contagens = ContagensSerializer()
    opcoes = OpcoesSerializer(help_text="Casas e pagadores das contas visíveis do mês")
    itens = ContaSerializer(many=True)


class PorCasaSerializer(RefSerializer):
    total_centavos = serializers.IntegerField()
    qtd = serializers.IntegerField()


class ResumoSerializer(serializers.Serializer):
    mes = serializers.CharField(help_text="AAAA-MM de total_centavos, qtd e por_casa")
    janela_alerta_dias = serializers.IntegerField()
    total_centavos = serializers.IntegerField()
    qtd = serializers.IntegerField()
    vencidas_qtd = serializers.IntegerField(help_text="Em atencao (qualquer mês)")
    vence_qtd = serializers.IntegerField(help_text="Em atencao (dentro da janela)")
    atencao = ContaSerializer(many=True)
    por_casa = PorCasaSerializer(many=True)


# ---- examples ------------------------------------------------------------------------------

CONTA_EXEMPLO = {
    "id": CONTA_ID,
    "espaco": {"id": ESPACO_ID, "nome": "Família", "tipo": "grupo"},
    "descricao": "Energia",
    "valor_centavos": 28743,
    "vencimento": "2026-11-18",
    "status": "pendente",
    "status_exibido": "vence",
    "dias_para_vencer": 3,
    "subgrupo": {"id": CASA_ID, "nome": "Casa da praia"},
    "pagador": {"id": PESSOA_ID, "nome": "Ana", "sou_eu": True},
    "visibilidade": "restrita",
    "criado_em": "2026-11-15T12:00:00Z",
}
DETALHE_EXEMPLO = {
    **CONTA_EXEMPLO,
    "criador": {"nome": "Ana", "sou_eu": True},
    "acesso": [{"id": OUTRA_ID, "nome": "Bia"}],
    "historico": [
        {
            "acao": "criada",
            "automatica": False,
            "autor": "Ana",
            "sou_eu": True,
            "dados": {},
            "criado_em": "2026-11-15T12:00:00Z",
        },
        {
            "acao": "editada",
            "automatica": False,
            "autor": "Ex-membro",
            "sou_eu": False,
            "dados": {"valor_centavos": [25000, 28743]},
            "criado_em": "2026-11-15T13:00:00Z",
        },
    ],
    "pode_editar": True,
}
ENTRADA_EXEMPLO = OpenApiExample(
    "Restrita com pagador",
    value={
        "descricao": "Energia",
        "valor_centavos": 28743,
        "vencimento": "2026-11-18",
        "subgrupo": CASA_ID,
        "pagador": PESSOA_ID,
        "visibilidade": "restrita",
        "acesso": [OUTRA_ID],
    },
    request_only=True,
)
DETALHE = OpenApiExample("Conta", value=DETALHE_EXEMPLO, response_only=True)


def _erros(*codes):
    textos = {
        400: "Valor, casa, pagador ou quem vê inválidos (RN11, RF11, Q19b).",
        403: "Seu papel vê a conta, mas não pode criar, editar nem cancelar (RN05).",
        404: "Espaço ou conta fora do seu acesso; igual para inexistente e invisível (RN06).",
        409: "Conta cancelada (editar) ou já paga/cancelada (cancelar).",
    }
    return {code: OpenApiResponse(ErroSerializer, description=textos[code]) for code in codes}


# ---- views ---------------------------------------------------------------------------------

COM_DADOS = ("espaco", "subgrupo", "pagador")
FILTRO_STATUS = {
    "todas": ~Q(status=Status.CANCELADA),  # D2
    "a_pagar": Q(status__in=ABERTOS),
    "vencidas": Q(status_exibido=VENCIDA),
    "pagas": Q(status__in=(Status.PAGA, Status.CONFIRMADA)),
    "canceladas": Q(status=Status.CANCELADA),
}
NAO_CANCELADA = ~Q(status=Status.CANCELADA)


def _mes(texto):
    """'AAAA-MM' (default: this month in Fortaleza) -> (label, first day, last day)."""
    try:
        ano, mes = map(int, texto.split("-")) if texto else timezone.localdate().timetuple()[:2]
        inicio = date(ano, mes, 1)
    except ValueError as exc:
        raise ValidationError({"mes": ["Use o formato AAAA-MM."]}) from exc
    fim = inicio.replace(day=calendar.monthrange(ano, mes)[1])
    return f"{ano:04d}-{mes:02d}", inicio, fim


def _uuid(request, nome):
    valor = request.query_params.get(nome)
    if not valor:
        return None
    campo = serializers.UUIDField()
    try:
        return campo.to_internal_value(valor)
    except serializers.ValidationError as exc:
        raise ValidationError({nome: exc.detail}) from exc


def _detalhe(request, conta_id, espaco, codigo=status.HTTP_200_OK):
    """Serialize after a write too: whoever just edited themselves out still gets this answer."""
    conta = (
        Lancamento.objects.com_status(espaco.janela_alerta_dias)
        .select_related(*COM_DADOS, "criador")
        .prefetch_related("acesso", "historico__usuario")
        .get(pk=conta_id)
    )
    contexto = {"request": request, "papel": espaco.meu_papel}
    return Response(ContaDetalheSerializer(conta, context=contexto).data, status=codigo)


class LancamentosView(APIView):
    @extend_schema(
        operation_id="lancamentos_listar",
        summary="Contas do espaço por mês, com contagens dos chips (RF13; só o que você vê)",
        parameters=[
            OpenApiParameter("mes", str, description="AAAA-MM; padrão: mês atual"),
            OpenApiParameter("status", str, enum=list(FILTRO_STATUS), description="padrão: todas"),
            OpenApiParameter("subgrupo", OpenApiTypes.UUID, description="casa"),
            OpenApiParameter("pagador", str, description="id de usuário ou `nenhum`"),
        ],
        responses={200: ListaSerializer, **_erros(400, 404)},
        examples=[
            OpenApiExample(
                "Novembro",
                value={
                    "mes": "2026-11",
                    "total_centavos": 28743,
                    "contagens": {
                        "todas": 1,
                        "a_pagar": 1,
                        "vencidas": 0,
                        "pagas": 0,
                        "canceladas": 0,
                    },
                    "opcoes": {
                        "casas": [{"id": CASA_ID, "nome": "Casa da praia"}],
                        "pagadores": [{"id": PESSOA_ID, "nome": "Ana", "sou_eu": True}],
                        "sem_pagador": False,
                    },
                    "itens": [CONTA_EXEMPLO],
                },
            )
        ],
    )
    def get(self, request, espaco_id):
        espaco = espaco_ou_404(request.user, espaco_id)
        rotulo, inicio, fim = _mes(request.query_params.get("mes"))
        filtro = request.query_params.get("status") or "todas"
        if filtro not in FILTRO_STATUS:
            raise ValidationError({"status": [f"Use um de: {', '.join(FILTRO_STATUS)}."]})
        do_mes = lancamentos_visiveis(request.user, espaco).filter(vencimento__range=(inicio, fim))
        contas = do_mes
        if casa := _uuid(request, "subgrupo"):
            contas = contas.filter(subgrupo_id=casa)
        if request.query_params.get("pagador") == "nenhum":
            contas = contas.filter(pagador__isnull=True)
        elif pagador := _uuid(request, "pagador"):
            contas = contas.filter(pagador_id=pagador)
        numeros = contas.aggregate(
            total=Sum("valor_centavos", filter=NAO_CANCELADA, default=0),
            **{nome: Count("pk", filter=q) for nome, q in FILTRO_STATUS.items()},
        )
        itens = contas.filter(FILTRO_STATUS[filtro]).select_related(*COM_DADOS)
        com_casa = do_mes.filter(subgrupo__isnull=False).select_related("subgrupo")
        com_pagador = do_mes.filter(pagador__isnull=False).select_related("pagador")
        casas = {c.subgrupo for c in com_casa}
        pagadores = {c.pagador for c in com_pagador}
        corpo = {
            "mes": rotulo,
            "total_centavos": numeros.pop("total"),
            "contagens": numeros,
            "opcoes": {
                "casas": [{"id": c.pk, "nome": c.nome} for c in sorted(casas, key=str)],
                "pagadores": [_pessoa(u, request) for u in sorted(pagadores, key=_nome)],
                "sem_pagador": do_mes.filter(pagador__isnull=True).exists(),
            },
            "itens": itens.order_by("vencimento", "criado_em"),
        }
        return Response(ListaSerializer(corpo, context={"request": request}).data)

    @extend_schema(
        operation_id="lancamentos_criar",
        summary="Nova conta manual; nasce pendente (RF10, RF11, RN11; dono, admin, membro)",
        request=ContaEntradaSerializer,
        responses={201: ContaDetalheSerializer, **_erros(400, 403, 404)},
        examples=[ENTRADA_EXEMPLO, DETALHE],
    )
    def post(self, request, espaco_id):
        espaco = espaco_ou_404(request.user, espaco_id, "criar_conta")
        entrada = ContaEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        conta = servicos.criar(request.user, espaco, entrada.validated_data)
        return _detalhe(request, conta.pk, espaco, status.HTTP_201_CREATED)


class ResumoView(APIView):
    @extend_schema(
        operation_id="lancamentos_resumo",
        summary="Início: total do mês, Precisa de atenção e Por casa (só o que você vê)",
        responses={200: ResumoSerializer, **_erros(404)},
        examples=[
            OpenApiExample(
                "Grupo",
                value={
                    "mes": "2026-11",
                    "janela_alerta_dias": 3,
                    "total_centavos": 28743,
                    "qtd": 1,
                    "vencidas_qtd": 0,
                    "vence_qtd": 1,
                    "atencao": [CONTA_EXEMPLO],
                    "por_casa": [
                        {"id": CASA_ID, "nome": "Casa da praia", "total_centavos": 28743, "qtd": 1}
                    ],
                },
            )
        ],
    )
    def get(self, request, espaco_id):
        espaco = espaco_ou_404(request.user, espaco_id)
        rotulo, inicio, fim = _mes(None)
        visiveis = lancamentos_visiveis(request.user, espaco)
        do_mes = visiveis.filter(NAO_CANCELADA, vencimento__range=(inicio, fim))
        numeros = do_mes.aggregate(total=Sum("valor_centavos", default=0), qtd=Count("pk"))
        # Q9: overdue from any month plus due within the window; never cancelled (D2).
        atencao = list(
            visiveis.filter(status_exibido__in=(VENCIDA, VENCE))
            .select_related(*COM_DADOS)
            .order_by("vencimento", "criado_em")
        )
        por_casa = []
        if espaco.tipo == Espaco.Tipo.GRUPO:
            por_casa = [
                {"id": c["subgrupo"], "nome": c["subgrupo__nome"], **c}
                for c in do_mes.filter(subgrupo__isnull=False)
                .values("subgrupo", "subgrupo__nome")
                .annotate(total_centavos=Sum("valor_centavos"), qtd=Count("pk"))
                .order_by("subgrupo__nome")
            ]
        corpo = {
            "mes": rotulo,
            "janela_alerta_dias": espaco.janela_alerta_dias,
            "total_centavos": numeros["total"],
            "qtd": numeros["qtd"],
            "vencidas_qtd": sum(c.status_exibido == VENCIDA for c in atencao),
            "vence_qtd": sum(c.status_exibido == VENCE for c in atencao),
            "atencao": atencao,
            "por_casa": por_casa,
        }
        return Response(ResumoSerializer(corpo, context={"request": request}).data)


class LancamentoView(APIView):
    @extend_schema(
        operation_id="lancamentos_detalhe",
        summary="Detalhe da conta com histórico (404 se você não a vê)",
        responses={200: ContaDetalheSerializer, **_erros(404)},
        examples=[DETALHE],
    )
    def get(self, request, lancamento_id):
        conta = lancamento_ou_404(request.user, lancamento_id)
        return _detalhe(request, conta.pk, conta.espaco)

    @extend_schema(
        operation_id="lancamentos_editar",
        summary="Editar conta (dono, admin, membro); histórico só do que mudou (RF12, RN22)",
        request=ContaEntradaSerializer(partial=True),
        responses={200: ContaDetalheSerializer, **_erros(400, 403, 404, 409)},
        examples=[
            OpenApiExample("Novo valor", value={"valor_centavos": 30000}, request_only=True),
            DETALHE,
        ],
    )
    def patch(self, request, lancamento_id):
        lancamento_ou_404(request.user, lancamento_id, "editar_conta")  # 404/403 before 400
        entrada = ContaEntradaSerializer(data=request.data, partial=True)
        entrada.is_valid(raise_exception=True)
        conta = servicos.editar(request.user, lancamento_id, entrada.validated_data)
        return _detalhe(request, conta.pk, conta.espaco)


class CancelarView(APIView):
    @extend_schema(
        operation_id="lancamentos_cancelar",
        summary="Cancelar conta aguardando ou pendente; nada é apagado (RN22, D2)",
        request=None,
        responses={200: ContaDetalheSerializer, **_erros(403, 404, 409)},
        examples=[DETALHE],
    )
    def post(self, request, lancamento_id):
        conta = servicos.cancelar(request.user, lancamento_id)
        return _detalhe(request, conta.pk, conta.espaco)
