import hashlib
import json

from django.db import transaction
from drf_spectacular.utils import extend_schema, extend_schema_field
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.boletos.models import DocumentoBoleto, Instrumento
from apps.boletos.tasks import agendar
from apps.espacos.acesso import espaco_ou_404, lancamentos_do_usuario, pode_na
from apps.espacos.models import Espaco, Membro, Papel
from apps.espacos.servicos import Conflito, _admins_travados
from apps.lancamentos.models import Status
from apps.lancamentos.servicos import rotulo
from apps.pagamentos.servicos import conta_travada

from .coordenacao import coordenado
from .models import EstadoSolicitacao, Solicitacao, TombstoneNonce


class EntradaSerializer(serializers.Serializer):
    nonce = serializers.UUIDField()
    grupo_id = serializers.UUIDField()
    pagador_id = serializers.UUIDField()
    mensagem = serializers.CharField(max_length=500, allow_blank=True, default="")
    confirmar_compartilhamento = serializers.BooleanField()
    versao_compartilhamento = serializers.CharField(min_length=64, max_length=64)

    def validate_confirmar_compartilhamento(self, value):
        if value is not True:
            raise serializers.ValidationError("Confirme o compartilhamento.")
        return value

    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) - set(self.fields):
            raise serializers.ValidationError({"non_field_errors": ["Campos não permitidos."]})
        return super().to_internal_value(data)


class ResultadoSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    nonce = serializers.UUIDField()
    estado = serializers.ChoiceField(EstadoSolicitacao.choices)
    pode_cancelar = serializers.SerializerMethodField()
    copia_id = serializers.SerializerMethodField()

    def get_pode_cancelar(self, obj) -> bool:
        return obj.estado == EstadoSolicitacao.PREPARANDO

    @extend_schema_field(serializers.UUIDField(allow_null=True))
    def get_copia_id(self, obj):
        usuario = self.context["request"].user
        if obj.copia_id and lancamentos_do_usuario(usuario).filter(pk=obj.copia_id).exists():
            return obj.copia_id
        return None


class PessoaOpcaoSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    nome = serializers.CharField()


class GrupoOpcaoSerializer(PessoaOpcaoSerializer):
    pagadores = PessoaOpcaoSerializer(many=True)


class OpcoesView(APIView):
    @extend_schema(
        operation_id="solicitacoes_opcoes", responses={200: GrupoOpcaoSerializer(many=True)}
    )
    @transaction.atomic
    @coordenado
    def get(self, request, origem_id):
        origem = (
            lancamentos_do_usuario(request.user)
            .filter(
                pk=origem_id,
                espaco__tipo=Espaco.Tipo.PESSOAL,
                espaco__dono=request.user,
                status=Status.PENDENTE,
            )
            .first()
        )
        if not origem:
            raise NotFound()
        membros = Membro.objects.filter(
            usuario=request.user, papel__in=[Papel.ADMIN, Papel.MEMBRO]
        ).select_related("espaco")
        grupos = []
        for membro in membros:
            pagadores = list(
                Membro.objects.filter(
                    espaco=membro.espaco, papel__in=[Papel.ADMIN, Papel.MEMBRO, Papel.PAGADOR]
                )
                .select_related("usuario")
                .order_by("usuario__nome", "pk")
            )
            membros_atuais = {m.usuario_id for m in pagadores}
            grupos.append(
                {
                    "id": membro.espaco_id,
                    "nome": membro.espaco.nome,
                    "pagadores": [
                        {"id": m.usuario_id, "nome": rotulo(m.usuario, membros_atuais)}
                        for m in pagadores
                    ],
                }
            )
        return Response(GrupoOpcaoSerializer(grupos, many=True).data)


def _hash(dados):
    valor = {k: str(v) if k.endswith("_id") or k == "nonce" else v for k, v in dados.items()}
    return hashlib.sha256(
        json.dumps(valor, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _snapshot(origem, mensagem):
    instrumento = Instrumento.objects.filter(lancamento=origem).first()
    documento = DocumentoBoleto.objects.filter(lancamento=origem).first()
    return {
        "descricao": origem.descricao,
        "valor_centavos": origem.valor_centavos,
        "vencimento": origem.vencimento.isoformat(),
        "mensagem": mensagem,
        "instrumento": (
            {
                "tipo": instrumento.tipo,
                "codigo": instrumento.codigo,
                "chave_pix": instrumento.chave_pix,
                "beneficiario": instrumento.beneficiario,
                "data_emissao": instrumento.data_emissao.isoformat()
                if instrumento.data_emissao
                else None,
            }
            if instrumento
            else None
        ),
        "documento": (
            {"id": str(documento.pk), "nome": documento.nome, "tamanho": documento.tamanho}
            if documento
            else None
        ),
    }


def versao_compartilhamento(origem):
    snapshot = _snapshot(origem, "")
    return hashlib.sha256(
        json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class CriarView(APIView):
    @extend_schema(
        operation_id="solicitacoes_criar",
        request=EntradaSerializer,
        responses={202: ResultadoSerializer},
    )
    @transaction.atomic
    @coordenado
    def post(self, request, origem_id):
        entrada = EntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        dados = entrada.validated_data
        existente = Solicitacao.objects.filter(
            origem_id=origem_id, solicitante=request.user, nonce=dados["nonce"]
        ).first()
        if existente:
            origem = conta_travada(request.user, origem_id)
            if (
                origem.espaco.tipo != Espaco.Tipo.PESSOAL
                or origem.espaco.dono_id != request.user.pk
            ):
                raise NotFound()
            if existente.corpo_hash != _hash(dados):
                raise Conflito("Tentativa já usada com outros dados.")
            return Response(
                ResultadoSerializer(existente, context={"request": request}).data, status=202
            )
        grupo = espaco_ou_404(
            request.user, dados["grupo_id"], "criar_conta", tipo=Espaco.Tipo.GRUPO
        )
        if not pode_na(request.user, grupo.meu_papel, None, "criar"):
            raise PermissionDenied()  # COR-10: a category grant does not reach requests
        _admins_travados([grupo.pk])
        list(
            Membro.objects.select_for_update()
            .filter(espaco=grupo, usuario_id__in=[request.user.pk, dados["pagador_id"]])
            .order_by("pk")
        )
        origem = conta_travada(request.user, origem_id)
        if origem.espaco.tipo != Espaco.Tipo.PESSOAL or origem.espaco.dono_id != request.user.pk:
            raise NotFound()
        if TombstoneNonce.objects.filter(
            origem=origem, solicitante=request.user, nonce=dados["nonce"]
        ).exists():
            raise Conflito("Tentativa encerrada.")
        if dados["versao_compartilhamento"] != versao_compartilhamento(origem):
            raise Conflito("A cobrança mudou. Confira os dados antes de solicitar.")
        if (
            origem.status != Status.PENDENTE
            or Solicitacao.objects.filter(
                origem=origem, estado__in=["preparando", "ativa", "quitada"]
            ).exists()
        ):
            raise Conflito("Conta indisponível para solicitação.")
        if not Membro.objects.filter(
            espaco=grupo,
            usuario_id=dados["pagador_id"],
            papel__in=[Papel.ADMIN, Papel.MEMBRO, Papel.PAGADOR],
        ).exists():
            raise ValidationError({"pagador_id": ["Escolha uma pessoa elegível."]})
        snapshot = _snapshot(origem, dados["mensagem"])
        reserva = Solicitacao.objects.create(
            origem=origem,
            solicitante=request.user,
            grupo=grupo,
            pagador_inicial_id=dados["pagador_id"],
            nonce=dados["nonce"],
            corpo_hash=_hash(dados),
            snapshot=snapshot,
        )
        if snapshot["documento"]:
            from apps.boletos.copia import CopiaIndisponivel, ObjetoOcupado, fixar_fonte

            try:
                fixar_fonte(snapshot["documento"]["id"], reserva.pk)
            except (CopiaIndisponivel, ObjetoOcupado):
                raise Conflito(
                    "O arquivo está temporariamente indisponível. Tente novamente."
                ) from None
        from .tasks import processar_solicitacao

        transaction.on_commit(lambda: agendar(processar_solicitacao, str(reserva.pk)))
        return Response(
            ResultadoSerializer(reserva, context={"request": request}).data,
            status=status.HTTP_202_ACCEPTED,
        )


class RecuperarView(APIView):
    @extend_schema(
        operation_id="solicitacoes_recuperar_nonce", responses={200: ResultadoSerializer}
    )
    @transaction.atomic
    @coordenado
    def get(self, request, origem_id, nonce):
        origem = conta_travada(request.user, origem_id)
        if origem.espaco.tipo != Espaco.Tipo.PESSOAL or origem.espaco.dono_id != request.user.pk:
            raise NotFound()
        reserva = Solicitacao.objects.filter(
            origem=origem, solicitante=request.user, nonce=nonce
        ).first()
        if not reserva:
            raise NotFound()
        return Response(ResultadoSerializer(reserva, context={"request": request}).data)

    @extend_schema(operation_id="solicitacoes_abandonar_nonce", request=None, responses={204: None})
    @transaction.atomic
    @coordenado
    def delete(self, request, origem_id, nonce):
        origem = conta_travada(request.user, origem_id)
        if origem.espaco.tipo != Espaco.Tipo.PESSOAL or origem.espaco.dono_id != request.user.pk:
            raise NotFound()
        reserva = Solicitacao.objects.filter(
            origem=origem, solicitante=request.user, nonce=nonce
        ).first()
        if reserva and reserva.estado != EstadoSolicitacao.PREPARANDO:
            raise Conflito("A solicitação já foi processada.")
        TombstoneNonce.objects.get_or_create(origem=origem, solicitante=request.user, nonce=nonce)
        if reserva:
            from .servicos import encerrar_preparacao

            encerrar_preparacao(reserva)
        return Response(status=204)
