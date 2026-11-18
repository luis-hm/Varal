import calendar
from datetime import date, timedelta

from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_field,
)
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.boletos.serializers import (
    DocumentoPDFSerializer,
    InstrumentoDetalheSerializer,
    InstrumentoEntradaSerializer,
)
from apps.contas_usuario.models import Usuario
from apps.espacos.acesso import (
    categorias_visiveis,
    espaco_ou_404,
    lancamento_ou_404,
    lancamentos_do_usuario,
    lancamentos_visiveis,
    membros_ids,
    pode_na,
    quem_ve,
)
from apps.espacos.models import Espaco
from apps.espacos.views import ErroSerializer
from apps.recorrencias.models import Recorrencia
from apps.solicitacoes.coordenacao import coordenado

from . import servicos
from .models import ABERTOS, STATUS_EXIBIDOS, Historico, Lancamento, Status
from .models import Visibilidade as Vis

ESPACO_ID = "1b4e28ba-2fa1-11d2-883f-0016d3cca427"
CONTA_ID = "3f2c8d4e-7a1b-4c5d-9e8f-0a1b2c3d4e5f"
CASA_ID = "ae779d06-431b-48fc-b75e-66ff8a7a60e7"
PESSOA_ID = "6fd32f1c-6f80-4b01-b491-25aeb00a180e"
OUTRA_ID = "c4a7d1e2-9b3f-4a6c-8d2e-1f0a9b8c7d6e"


# ---- serializers ---------------------------------------------------------------------------


class RefSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    nome = serializers.CharField()


class CategoriaRefSerializer(RefSerializer):
    icone = serializers.CharField()


class EspacoRefSerializer(RefSerializer):
    tipo = serializers.ChoiceField(Espaco.Tipo.choices)


class PessoaSerializer(RefSerializer):
    sou_eu = serializers.BooleanField()


class CriadorSerializer(serializers.Serializer):
    nome = serializers.CharField()
    sou_eu = serializers.BooleanField()


def _nome(usuario, contexto):
    """Decision 23, live data: `contexto["membros"]` holds the space's current member ids."""
    return servicos.rotulo(usuario, contexto["membros"])


def _pessoa(usuario, contexto):
    if usuario is None:
        return None
    eu = usuario.pk == contexto["request"].user.pk
    return {"id": usuario.pk, "nome": _nome(usuario, contexto), "sou_eu": eu}


class ContaSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    espaco = EspacoRefSerializer()
    descricao = serializers.CharField()
    valor_centavos = serializers.IntegerField(allow_null=True)
    vencimento = serializers.DateField()
    status = serializers.ChoiceField(Status.choices)
    status_exibido = serializers.ChoiceField(STATUS_EXIBIDOS)
    dias_para_vencer = serializers.SerializerMethodField()
    subgrupo = CategoriaRefSerializer(allow_null=True)
    pagador = serializers.SerializerMethodField()
    visibilidade = serializers.ChoiceField(Vis.choices)
    criado_em = serializers.DateTimeField()

    def get_dias_para_vencer(self, obj) -> int:
        return (obj.vencimento - timezone.localdate()).days

    @extend_schema_field(PessoaSerializer(allow_null=True))
    def get_pagador(self, obj):
        return _pessoa(obj.pagador, self.context)


class HistoricoSerializer(serializers.Serializer):
    acao = serializers.ChoiceField(Historico.Acao.choices)
    automatica = serializers.SerializerMethodField()
    autor = serializers.SerializerMethodField(help_text="null em ação automática")
    sou_eu = serializers.SerializerMethodField()
    dados = serializers.DictField(source="dados_exibidos", help_text="Pessoas já como nomes")
    criado_em = serializers.DateTimeField()

    def get_automatica(self, obj) -> bool:
        return obj.automatica

    def get_autor(self, obj) -> str | None:
        if obj.automatica:
            return None
        # RN30 / decision 23: "Ex-membro" or "Pessoa sem nome"; never the e-mail.
        return servicos.rotulo(obj.usuario, self.context["membros"], historico=True)

    def get_sou_eu(self, obj) -> bool:
        return obj.usuario_id == self.context["request"].user.pk


class PagamentoSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    pago_em = serializers.DateField()
    valor_pago_centavos = serializers.IntegerField()
    criado_em = serializers.DateTimeField()
    desfeito_em = serializers.DateTimeField(allow_null=True)
    marcado_por = serializers.SerializerMethodField()
    comprovante_id = serializers.SerializerMethodField()
    derivado = serializers.SerializerMethodField()

    def get_marcado_por(self, obj) -> str:
        if self.get_derivado(obj):
            return "Sistema"
        return servicos.rotulo(obj.marcado_por, self.context["membros"], historico=True)

    def get_derivado(self, obj) -> bool:
        from apps.solicitacoes.models import ParPagamento

        return ParPagamento.objects.filter(derivada=obj).exists()

    @extend_schema_field(serializers.UUIDField(allow_null=True))
    def get_comprovante_id(self, obj):
        from apps.pagamentos.models import DocumentoComprovante

        return (
            DocumentoComprovante.objects.filter(pagamento=obj).values_list("pk", flat=True).first()
        )


class SolicitacaoResumoSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    nonce = serializers.UUIDField()
    estado = serializers.ChoiceField(["preparando", "ativa", "quitada", "encerrada", "falhou"])
    pode_cancelar = serializers.BooleanField()
    copia_id = serializers.UUIDField(allow_null=True)


class ContaDetalheSerializer(ContaSerializer):
    versao_compartilhamento = serializers.SerializerMethodField()
    mensagem_solicitacao = serializers.SerializerMethodField()
    solicitacao_ativa = serializers.SerializerMethodField()
    pode_solicitar = serializers.SerializerMethodField()
    documento_pdf = DocumentoPDFSerializer(allow_null=True, read_only=True)
    instrumento = InstrumentoDetalheSerializer(allow_null=True, read_only=True)
    criador = serializers.SerializerMethodField()
    acesso = serializers.SerializerMethodField()
    quem_ve = serializers.SerializerMethodField(
        help_text="Acesso efetivo da restrita: criador, pagador e escolhidos; vazio nas demais."
    )
    historico = HistoricoSerializer(many=True)
    pode_editar = serializers.SerializerMethodField()
    recorrente = serializers.SerializerMethodField()
    recorrencia_id = serializers.SerializerMethodField()
    competencia = serializers.DateField(allow_null=True)
    pode_ver_recorrencia = serializers.SerializerMethodField()
    pagamento_ativo = serializers.SerializerMethodField()
    pagamentos = PagamentoSerializer(many=True)
    pode_pagar = serializers.SerializerMethodField()
    pode_desfazer_pagamento = serializers.SerializerMethodField()
    pode_anexar_comprovante = serializers.SerializerMethodField()

    @extend_schema_field(SolicitacaoResumoSerializer(allow_null=True))
    def get_solicitacao_ativa(self, obj):
        if (
            obj.espaco.tipo != Espaco.Tipo.PESSOAL
            or obj.espaco.dono_id != self.context["request"].user.pk
        ):
            return None
        from apps.solicitacoes.models import Solicitacao
        from apps.solicitacoes.views import ResultadoSerializer

        reserva = Solicitacao.objects.filter(
            origem=obj, estado__in=["preparando", "ativa", "quitada"]
        ).first()
        return ResultadoSerializer(reserva, context=self.context).data if reserva else None

    def get_pode_solicitar(self, obj) -> bool:
        return bool(
            obj.status == Status.PENDENTE
            and obj.espaco.tipo == Espaco.Tipo.PESSOAL
            and obj.espaco.dono_id == self.context["request"].user.pk
            and not self.get_solicitacao_ativa(obj)
        )

    def get_versao_compartilhamento(self, obj) -> str | None:
        if (
            obj.espaco.tipo != Espaco.Tipo.PESSOAL
            or obj.espaco.dono_id != self.context["request"].user.pk
            or obj.status != Status.PENDENTE
        ):
            return None
        from apps.solicitacoes.views import versao_compartilhamento

        return versao_compartilhamento(obj)

    def get_mensagem_solicitacao(self, obj) -> str | None:
        from apps.solicitacoes.models import Solicitacao

        reserva = Solicitacao.objects.filter(copia=obj).only("snapshot").first()
        return reserva.snapshot.get("mensagem") if reserva else None

    def get_recorrente(self, obj) -> bool:
        return obj.recorrencia_id is not None

    def get_pode_ver_recorrencia(self, obj) -> bool:
        from apps.espacos.acesso import recorrencias_do_usuario

        return bool(
            obj.recorrencia_id
            and recorrencias_do_usuario(self.context["request"].user)
            .filter(pk=obj.recorrencia_id)
            .exists()
        )

    @extend_schema_field(serializers.UUIDField(allow_null=True))
    def get_recorrencia_id(self, obj):
        return obj.recorrencia_id if self.get_pode_ver_recorrencia(obj) else None

    def _ativo(self, obj):
        return next((p for p in obj.pagamentos.all() if p.desfeito_em is None), None)

    @extend_schema_field(PagamentoSerializer(allow_null=True))
    def get_pagamento_ativo(self, obj):
        pagamento = self._ativo(obj)
        return PagamentoSerializer(pagamento, context=self.context).data if pagamento else None

    def get_pode_pagar(self, obj) -> bool:
        from apps.pagamentos.servicos import pode_pagar

        return obj.status == Status.PENDENTE and pode_pagar(self.context["request"].user, obj)

    def get_pode_desfazer_pagamento(self, obj) -> bool:
        from apps.pagamentos.servicos import pode_desfazer
        from apps.solicitacoes.models import ParPagamento

        usuario = self.context["request"].user
        pagamento = self._ativo(obj)
        if not pode_desfazer(usuario, obj, pagamento):
            return False
        par = ParPagamento.objects.filter(derivada=pagamento).select_related("copia").first()
        if not par:
            return True
        if not par.copia_id:
            return False
        try:
            copia = lancamento_ou_404(usuario, par.copia.lancamento_id)
        except NotFound:
            return False
        return pode_desfazer(usuario, copia, par.copia)

    def get_pode_anexar_comprovante(self, obj) -> bool:
        from apps.pagamentos.servicos import pode_anexar

        return pode_anexar(self.context["request"].user, obj, self._ativo(obj))

    @extend_schema_field(CriadorSerializer)
    def get_criador(self, obj):
        return {
            "nome": _nome(obj.criador, self.context),  # RN30: deleted or gone -> "Ex-membro"
            "sou_eu": obj.criador_id == self.context["request"].user.pk,
        }

    @extend_schema_field(RefSerializer(many=True))
    def get_acesso(self, obj):
        return [{"id": u.pk, "nome": _nome(u, self.context)} for u in obj.acesso.all()]

    @extend_schema_field(RefSerializer(many=True))
    def get_quem_ve(self, obj):
        if obj.espaco.tipo != Espaco.Tipo.GRUPO or obj.visibilidade != Vis.RESTRITA:
            return []
        pessoas = Usuario.objects.filter(pk__in=quem_ve(obj))
        return sorted(
            ({"id": u.pk, "nome": _nome(u, self.context)} for u in pessoas),
            key=lambda p: (p["nome"].casefold(), str(p["id"])),
        )

    def get_pode_editar(self, obj) -> bool:
        return obj.status != Status.CANCELADA and pode_na(
            self.context["request"].user, self.context["papel"], obj.subgrupo_id, "editar_conta"
        )


class ContaSimplesSerializer(ContaSerializer):
    instrumento = InstrumentoDetalheSerializer(allow_null=True, read_only=True)
    documento_pdf = DocumentoPDFSerializer(allow_null=True, read_only=True)
    pode_pagar = serializers.SerializerMethodField()

    def get_pode_pagar(self, obj) -> bool:
        from apps.pagamentos.servicos import pode_pagar

        return obj.status == Status.PENDENTE and pode_pagar(self.context["request"].user, obj)


class ListaSimplesSerializer(serializers.Serializer):
    abertas_qtd = serializers.IntegerField()
    pagas_mes_qtd = serializers.IntegerField()
    itens = ContaSimplesSerializer(many=True)


class ListaSimplesView(APIView):
    @extend_schema(
        operation_id="lancamentos_modo_simples",
        parameters=[OpenApiParameter("pagas", bool, description="Pagas no mês civil atual")],
        responses={200: ListaSimplesSerializer},
    )
    @transaction.atomic
    @coordenado
    def get(self, request, espaco_id):
        from apps.recorrencias.servicos import travar_espaco

        espaco = espaco_ou_404(request.user, espaco_id)
        travar_espaco(request.user, espaco)
        espaco = espaco_ou_404(request.user, espaco_id)
        hoje = timezone.localdate()
        inicio = hoje.replace(day=1)
        fim = hoje.replace(day=calendar.monthrange(hoje.year, hoje.month)[1])
        contas = lancamentos_visiveis(request.user, espaco)
        abertas = contas.filter(status__in=ABERTOS)
        pagas = contas.filter(
            status__in=(Status.PAGA, Status.CONFIRMADA), vencimento__range=(inicio, fim)
        )
        itens = pagas if request.query_params.get("pagas") == "true" else abertas
        itens = itens.select_related(*COM_DADOS, "instrumento", "documento_pdf").order_by(
            "vencimento", "id"
        )
        for conta in itens:
            conta.espaco.meu_papel = espaco.meu_papel
        dados = {"abertas_qtd": abertas.count(), "pagas_mes_qtd": pagas.count(), "itens": itens}
        return Response(
            ListaSimplesSerializer(
                dados, context={"request": request, "membros": membros_ids(espaco)}
            ).data
        )


class CentavosField(serializers.IntegerField):
    """RN11: whole cents only; 10.5, "10" or true are rejected (IntegerField would coerce)."""

    def to_internal_value(self, data):
        if isinstance(data, bool) or not isinstance(data, int):
            self.fail("invalid")
        return super().to_internal_value(data)


class ContaEntradaSerializer(serializers.Serializer):
    escopo = serializers.ChoiceField(["mes", "proximos"], required=False)
    confirmar_chegada = serializers.BooleanField(required=False)
    valor_tipo = serializers.ChoiceField(Recorrencia.ValorTipo.choices, required=False)
    documento_pdf = serializers.UUIDField(allow_null=True, required=False)
    data_emissao = serializers.DateField(allow_null=True, required=False)
    beneficiario = serializers.CharField(
        max_length=200, allow_null=True, allow_blank=True, required=False
    )
    instrumento = InstrumentoEntradaSerializer(allow_null=True, required=False)
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
    vencidas = serializers.IntegerField(
        help_text="Abertas vencidas pela data, inclusive aguardando"
    )
    pagas = serializers.IntegerField()
    canceladas = serializers.IntegerField()


class OpcoesSerializer(serializers.Serializer):
    casas = CategoriaRefSerializer(many=True, help_text="Categorias ativas do grupo")
    sem_categoria = serializers.BooleanField(help_text="Há conta visível sem categoria")
    pagadores = PessoaSerializer(many=True)
    sem_pagador = serializers.BooleanField()
    ex_membro = serializers.BooleanField()


class ListaSerializer(serializers.Serializer):
    mes = serializers.CharField(
        allow_null=True, help_text="AAAA-MM do recorte; null = todos os períodos (COR-02)"
    )
    total_centavos = serializers.IntegerField(help_text="Valor conhecido não cancelado do recorte")
    valores_indefinidos_qtd = serializers.IntegerField()
    contagens = ContagensSerializer()
    opcoes = OpcoesSerializer(help_text="Categorias e pagadores; não dependem do mês (COR-07)")
    itens = ContaSerializer(many=True)


class PorCasaSerializer(serializers.Serializer):
    id = serializers.UUIDField(allow_null=True, help_text="null = Sem categoria (COR-07)")
    nome = serializers.CharField()
    icone = serializers.CharField(allow_null=True)
    abertas_qtd = serializers.IntegerField(help_text="A pagar em qualquer mês")
    total_centavos = serializers.IntegerField()
    qtd = serializers.IntegerField()
    pagas_qtd = serializers.IntegerField()
    valores_indefinidos_qtd = serializers.IntegerField()


class ResumoSerializer(serializers.Serializer):
    mes = serializers.CharField(help_text="AAAA-MM de total_centavos, qtd e por_casa")
    janela_alerta_dias = serializers.IntegerField()
    total_centavos = serializers.IntegerField()
    qtd = serializers.IntegerField()
    pagas_qtd = serializers.IntegerField()
    valores_indefinidos_qtd = serializers.IntegerField()
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
    "instrumento": None,
    "acesso": [{"id": OUTRA_ID, "nome": "Bia"}],
    "quem_ve": [{"id": PESSOA_ID, "nome": "Ana"}, {"id": OUTRA_ID, "nome": "Bia"}],
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
FILTRO_STATUS = ("todas", "a_pagar", "vencidas", "pagas", "canceladas")
NAO_CANCELADA = ~Q(status=Status.CANCELADA)


def _filtros_status():
    # Q04-35: overdue is temporal; awaiting bills keep their badge. Resolve today per request,
    # never at module import, so a long-lived worker also crosses midnight in Fortaleza.
    return {
        "todas": NAO_CANCELADA,
        "a_pagar": Q(status__in=ABERTOS),
        "vencidas": Q(status__in=ABERTOS, vencimento__lt=timezone.localdate()),
        "pagas": Q(status__in=(Status.PAGA, Status.CONFIRMADA)),
        "canceladas": Q(status=Status.CANCELADA),
    }


def _mes(texto, opcional=False):
    """'AAAA-MM' (default: this month in Fortaleza) -> (label, first day, last day).
    `opcional`: no month means every period (COR-02) -> (None, None, None)."""
    if opcional and not texto:
        return None, None, None
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


@transaction.atomic
@coordenado
def _detalhe(request, conta_id, espaco, codigo=status.HTTP_200_OK, apos_escrita=False):
    """Authorize the actual read and hold the bill through prefetch and serialization.

    A write keeps its outer transaction and row locks until this response is built. Only
    that path may acknowledge the actor who just edited themselves out (approved exception).
    """
    # Acquire the lock separately: if we wait for an edit, its access changes must be read
    # from a fresh statement snapshot, not from EXISTS evaluated before that wait.
    list(Lancamento.objects.select_for_update().filter(pk=conta_id).values("pk"))
    consulta = Lancamento.objects if apos_escrita else lancamentos_do_usuario(request.user)
    try:
        conta = (
            consulta.com_status(espaco.janela_alerta_dias)
            .select_related(*COM_DADOS, "criador")
            .select_related("instrumento")
            .prefetch_related("acesso", "historico__usuario", "pagamentos__marcado_por")
            .get(pk=conta_id)
        )
    except Lancamento.DoesNotExist as exc:
        raise NotFound() from exc
    membros = membros_ids(espaco)
    servicos.resolver_pessoas(conta.historico.all(), membros)
    contexto = {
        "request": request,
        "papel": getattr(conta, "meu_papel", espaco.meu_papel),
        "membros": membros,
    }
    conta.espaco.meu_papel = contexto["papel"]
    return Response(ContaDetalheSerializer(conta, context=contexto).data, status=codigo)


class LancamentosView(APIView):
    @extend_schema(
        operation_id="lancamentos_listar",
        summary="Contas do espaço, com mês opcional e contagens dos chips (RF13, COR-02)",
        parameters=[
            OpenApiParameter("mes", str, description="AAAA-MM; sem mês = todos os períodos"),
            OpenApiParameter(
                "status",
                str,
                enum=list(FILTRO_STATUS),
                description="Padrão: todas; vencidas inclui abertas aguardando pela data.",
            ),
            OpenApiParameter("subgrupo", str, description="id da categoria ou `nenhum`"),
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
        rotulo, inicio, fim = _mes(request.query_params.get("mes"), opcional=True)
        filtros = _filtros_status()
        filtro = request.query_params.get("status") or "todas"
        if filtro not in FILTRO_STATUS:
            raise ValidationError({"status": [f"Use um de: {', '.join(FILTRO_STATUS)}."]})
        visiveis = lancamentos_visiveis(request.user, espaco)
        contas = visiveis.filter(vencimento__range=(inicio, fim)) if rotulo else visiveis
        if request.query_params.get("subgrupo") == "nenhum":
            contas = contas.filter(subgrupo__isnull=True)
        elif casa := _uuid(request, "subgrupo"):
            contas = contas.filter(subgrupo_id=casa)
        membros_atuais = membros_ids(espaco)
        if request.query_params.get("pagador") == "ex_membro":
            contas = contas.filter(pagador__isnull=False).exclude(pagador_id__in=membros_atuais)
        elif request.query_params.get("pagador") == "nenhum":
            contas = contas.filter(pagador__isnull=True)
        elif pagador := _uuid(request, "pagador"):
            contas = contas.filter(pagador_id=pagador)
        numeros = contas.aggregate(
            total=Sum("valor_centavos", filter=NAO_CANCELADA, default=0),
            indefinidos=Count("pk", filter=NAO_CANCELADA & Q(valor_centavos__isnull=True)),
            **{nome: Count("pk", filter=q) for nome, q in filtros.items()},
        )
        # ponytail: no pagination; a household has hundreds of bills, not thousands. Add a cursor
        # (vencimento, id) when one space passes ~1000 visible bills.
        itens = contas.filter(filtros[filtro]).select_related(*COM_DADOS)
        # COR-07: options never depend on the month, so an active filter can always be undone.
        categorias = (
            categorias_visiveis(request.user, espaco, espaco.meu_papel)
            .filter(arquivado=False)
            .order_by("nome")
        )
        com_pagador = visiveis.filter(pagador__isnull=False).select_related("pagador")
        pagadores = {c.pagador for c in com_pagador if c.pagador_id in membros_atuais}
        contexto = {"request": request, "membros": membros_atuais}
        corpo = {
            "mes": rotulo,
            "total_centavos": numeros.pop("total"),
            "valores_indefinidos_qtd": numeros.pop("indefinidos"),
            "contagens": numeros,
            "opcoes": {
                "casas": [{"id": c.pk, "nome": c.nome, "icone": c.icone} for c in categorias],
                "sem_categoria": espaco.tipo == Espaco.Tipo.GRUPO
                and visiveis.filter(subgrupo__isnull=True).exists(),
                "pagadores": sorted(
                    (_pessoa(u, contexto) for u in pagadores), key=lambda p: p["nome"]
                ),
                "sem_pagador": visiveis.filter(pagador__isnull=True).exists(),
                "ex_membro": visiveis.filter(pagador__isnull=False)
                .exclude(pagador_id__in=membros_atuais)
                .exists(),
            },
            "itens": itens.order_by("vencimento", "criado_em"),
        }
        return Response(ListaSerializer(corpo, context=contexto).data)

    @extend_schema(
        operation_id="lancamentos_criar",
        summary="Nova conta manual; nasce pendente (RF10, RF11, RN11; dono, admin, membro)",
        request=ContaEntradaSerializer,
        responses={201: ContaDetalheSerializer, **_erros(400, 403, 404)},
        examples=[ENTRADA_EXEMPLO, DETALHE],
    )
    @transaction.atomic
    @coordenado
    def post(self, request, espaco_id):
        espaco = espaco_ou_404(request.user, espaco_id, "criar_conta")
        entrada = ContaEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        conta = servicos.criar(request.user, espaco, entrada.validated_data)
        return _detalhe(request, conta.pk, conta.espaco, status.HTTP_201_CREATED, apos_escrita=True)


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
        numeros = do_mes.aggregate(
            total=Sum("valor_centavos", default=0),
            qtd=Count("pk"),
            valores_indefinidos_qtd=Count("pk", filter=Q(valor_centavos__isnull=True)),
            pagas_qtd=Count("pk", filter=Q(status__in=(Status.PAGA, Status.CONFIRMADA))),
        )
        # Q9 / decision 26: every open bill (pendente or aguardando) overdue from any month or
        # due within the window, by date; the badge keeps the real status. Never cancelled (D2).
        hoje = timezone.localdate()
        atencao = list(
            visiveis.filter(
                status__in=ABERTOS,
                vencimento__lte=hoje + timedelta(days=espaco.janela_alerta_dias),
            )
            .select_related(*COM_DADOS)
            .order_by("vencimento", "criado_em")
        )
        por_casa = []
        if espaco.tipo == Espaco.Tipo.GRUPO:
            # COR-07: every category (even empty) plus "Sem categoria" when it holds bills, so no
            # part of the total disappears from the cards.
            numeros_casa = {
                c["subgrupo"]: c
                for c in do_mes.values("subgrupo").annotate(
                    total_centavos=Sum("valor_centavos", default=0),
                    qtd=Count("pk"),
                    valores_indefinidos_qtd=Count("pk", filter=Q(valor_centavos__isnull=True)),
                    pagas_qtd=Count("pk", filter=Q(status__in=(Status.PAGA, Status.CONFIRMADA))),
                )
            }
            abertas = dict(
                visiveis.filter(status__in=ABERTOS)
                .values("subgrupo")
                .annotate(n=Count("pk"))
                .values_list("subgrupo", "n")
            )
            vazio = {"total_centavos": 0, "qtd": 0, "valores_indefinidos_qtd": 0, "pagas_qtd": 0}

            def linha(id_, nome, icone):
                numeros_ = {k: numeros_casa.get(id_, vazio)[k] for k in vazio}
                return {
                    "id": id_,
                    "nome": nome,
                    "icone": icone,
                    **numeros_,
                    "abertas_qtd": abertas.get(id_, 0),
                }

            por_casa = [
                linha(c.pk, c.nome, c.icone)
                for c in categorias_visiveis(request.user, espaco, espaco.meu_papel)
                .filter(arquivado=False)
                .order_by("nome")
            ]
            # Archived categories keep their paid bills: still counted, after the active ones.
            vistas = {c["id"] for c in por_casa}
            sobras = (set(numeros_casa) | set(abertas)) - vistas - {None}
            por_casa += [
                linha(c.pk, c.nome, c.icone)
                for c in espaco.subgrupos.filter(pk__in=sobras).order_by("nome")
            ]
            if None in numeros_casa or None in abertas:
                por_casa.append(linha(None, "Sem categoria", None))
        corpo = {
            "mes": rotulo,
            "janela_alerta_dias": espaco.janela_alerta_dias,
            "total_centavos": numeros["total"],
            "qtd": numeros["qtd"],
            "pagas_qtd": numeros["pagas_qtd"],
            "valores_indefinidos_qtd": numeros["valores_indefinidos_qtd"],
            "vencidas_qtd": sum(c.vencimento < hoje for c in atencao),
            "vence_qtd": sum(c.vencimento >= hoje for c in atencao),
            "atencao": atencao,
            "por_casa": por_casa,
        }
        contexto = {"request": request, "membros": membros_ids(espaco)}
        return Response(ResumoSerializer(corpo, context=contexto).data)


class LancamentoView(APIView):
    @extend_schema(
        operation_id="lancamentos_detalhe",
        summary="Detalhe da conta com histórico (404 se você não a vê)",
        responses={200: ContaDetalheSerializer, **_erros(404)},
        examples=[DETALHE],
    )
    @transaction.atomic
    @coordenado
    def get(self, request, lancamento_id):
        from apps.pagamentos.servicos import conta_travada

        conta = conta_travada(request.user, lancamento_id)
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
    @transaction.atomic
    @coordenado
    def patch(self, request, lancamento_id):
        lancamento_ou_404(request.user, lancamento_id, "editar_conta")  # 404/403 before 400
        entrada = ContaEntradaSerializer(data=request.data, partial=True)
        entrada.is_valid(raise_exception=True)
        conta = servicos.editar(request.user, lancamento_id, entrada.validated_data)
        return _detalhe(request, conta.pk, conta.espaco, apos_escrita=True)


class CancelarEntradaSerializer(serializers.Serializer):
    escopo = serializers.ChoiceField(["mes", "proximos"], required=False)


class CancelarView(APIView):
    @extend_schema(
        operation_id="lancamentos_cancelar",
        summary="Cancelar conta aguardando ou pendente; nada é apagado (RN22, D2)",
        request=CancelarEntradaSerializer,
        responses={200: ContaDetalheSerializer, **_erros(403, 404, 409)},
        examples=[DETALHE],
    )
    @transaction.atomic
    @coordenado
    def post(self, request, lancamento_id):
        entrada = CancelarEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        conta = servicos.cancelar(
            request.user, lancamento_id, entrada.validated_data.get("escopo", "mes")
        )
        return _detalhe(request, conta.pk, conta.espaco, apos_escrita=True)
