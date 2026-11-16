import uuid
from datetime import datetime

from django.core import signing
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.boletos.tasks import _travar_objeto
from apps.contas_usuario.models import Usuario
from apps.espacos.servicos import Conflito

from . import push
from .acesso import autorizadas, travar_contexto
from .models import InscricaoPush, TipoEvento
from .sessoes import travar_instalacao, travar_sessao


class NotificacaoSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    tipo = serializers.ChoiceField(source="evento.tipo", choices=TipoEvento.choices)
    titulo = serializers.SerializerMethodField()
    texto = serializers.SerializerMethodField()
    criado_em = serializers.DateTimeField()
    lido_em = serializers.DateTimeField(allow_null=True)
    destino = serializers.SerializerMethodField()

    def get_titulo(self, obj) -> str:
        return obj.evento.get_tipo_display()

    def get_texto(self, obj) -> str:
        evento = obj.evento
        if evento.tipo == TipoEvento.CANCELADA_RN32:
            descricao = evento.snapshot_p7.get("descricao") or "Conta cancelada automaticamente"
            referencia = evento.snapshot_p7.get("referencia", str(evento.pk))
            data = evento.snapshot_p7.get("data", "")
            try:
                data = datetime.fromisoformat(data).strftime("%d/%m/%Y")
            except (ValueError, TypeError):
                data = timezone.localtime(evento.criado_em).strftime("%d/%m/%Y")
            return (
                f"{descricao} · {data} · referência {referencia}. "
                "Ficou sem ninguém que pudesse vê-la."
            )
        return evento.lancamento.descricao if evento.lancamento_id else ""

    def get_destino(self, obj) -> str | None:
        if obj.evento.tipo == TipoEvento.CANCELADA_RN32 or not obj.evento.lancamento_id:
            return None
        return f"/contas/{obj.evento.lancamento_id}"


class ListaNotificacoesSerializer(serializers.Serializer):
    resultados = NotificacaoSerializer(many=True)
    proximo = serializers.CharField(allow_null=True)
    nao_lidas = serializers.IntegerField()


class ResumoNotificacoesSerializer(serializers.Serializer):
    nao_lidas = serializers.IntegerField()
    recentes = NotificacaoSerializer(many=True)


class LerSerializer(serializers.Serializer):
    lido_em = serializers.DateTimeField()


class LerTodasSerializer(serializers.Serializer):
    nao_lidas = serializers.IntegerField()


class PreferenciasSerializer(serializers.Serializer):
    versao = serializers.IntegerField(read_only=True, default=1)
    email = serializers.BooleanField(required=False)
    push = serializers.BooleanField(required=False)


class PreferenciasEntradaSerializer(serializers.Serializer):
    email = serializers.BooleanField(required=False)
    push = serializers.BooleanField(required=False)

    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) - {"email", "push"}:
            raise serializers.ValidationError(
                {"non_field_errors": ["Informe apenas email e push."]}
            )
        if any(type(valor) is not bool for valor in data.values()):
            raise serializers.ValidationError(
                {"non_field_errors": ["Preferências devem ser booleanas."]}
            )
        return super().to_internal_value(data)


class PushConfiguracaoSerializer(serializers.Serializer):
    habilitado = serializers.BooleanField()
    chave_publica = serializers.CharField(allow_blank=True)


class ChavesSerializer(serializers.Serializer):
    p256dh = serializers.CharField(max_length=128, write_only=True)
    auth = serializers.CharField(max_length=64, write_only=True)


class InscricaoEntradaSerializer(serializers.Serializer):
    endpoint = serializers.CharField(max_length=2048, write_only=True)
    keys = ChavesSerializer(write_only=True)
    instalacao = serializers.UUIDField(write_only=True)


class InscricaoResultadoSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    ativo = serializers.BooleanField(source="ativa")


def preferencias(usuario):
    dados = usuario.prefs_notificacao if isinstance(usuario.prefs_notificacao, dict) else {}
    return {
        "versao": 1,
        "email": dados.get("email", True) is not False,
        "push": dados.get("push", True) is not False,
    }


def _cursor(valor):
    try:
        tempo, ident = signing.loads(valor, salt="notificacoes.cursor")
        return datetime.fromisoformat(tempo), uuid.UUID(ident)
    except (signing.BadSignature, ValueError, TypeError):
        raise ValidationError({"cursor": ["Cursor inválido."]}) from None


def _base(usuario, ids):
    return (
        autorizadas(usuario)
        .filter(pk__in=ids)
        .select_related("evento", "evento__lancamento")
        .order_by("-criado_em", "-id")
    )


class NotificacoesView(APIView):
    @extend_schema(
        operation_id="notificacoes_listar",
        parameters=[OpenApiParameter("cursor", str), OpenApiParameter("limite", int)],
        responses={200: ListaNotificacoesSerializer},
    )
    @transaction.atomic
    def get(self, request):
        ids = travar_contexto(request.user)
        contas = _base(request.user, ids)
        nao_lidas = contas.filter(lido_em__isnull=True).count()
        try:
            limite = int(request.query_params.get("limite", 20))
            if not 1 <= limite <= 50:
                raise ValueError
        except ValueError:
            raise ValidationError({"limite": ["Use um número entre 1 e 50."]}) from None
        if cursor := request.query_params.get("cursor"):
            criado, pk = _cursor(cursor)
            contas = contas.filter(Q(criado_em__lt=criado) | Q(criado_em=criado, pk__lt=pk))
        itens = list(contas[: limite + 1])
        mais = len(itens) > limite
        itens = itens[:limite]
        proximo = (
            signing.dumps(
                [itens[-1].criado_em.isoformat(), str(itens[-1].pk)], salt="notificacoes.cursor"
            )
            if mais
            else None
        )
        return Response(
            {
                "resultados": NotificacaoSerializer(itens, many=True).data,
                "proximo": proximo,
                "nao_lidas": nao_lidas,
            }
        )


class ResumoView(APIView):
    @extend_schema(
        operation_id="notificacoes_resumo", responses={200: ResumoNotificacoesSerializer}
    )
    @transaction.atomic
    def get(self, request):
        ids = travar_contexto(request.user)
        contas = _base(request.user, ids)
        return Response(
            {
                "nao_lidas": contas.filter(lido_em__isnull=True).count(),
                "recentes": NotificacaoSerializer(contas[:3], many=True).data,
            }
        )


class LerView(APIView):
    @extend_schema(operation_id="notificacoes_ler", request=None, responses={200: LerSerializer})
    @transaction.atomic
    def post(self, request, notificacao_id):
        ids = travar_contexto(request.user)
        notificacao = (
            autorizadas(request.user)
            .select_for_update(of=("self",))
            .filter(pk=notificacao_id, pk__in=ids)
            .first()
        )
        if not notificacao:
            raise NotFound()
        if notificacao.lido_em is None:
            notificacao.lido_em = timezone.now()
            notificacao.save(update_fields=["lido_em"])
        return Response({"lido_em": notificacao.lido_em})


class LerTodasView(APIView):
    @extend_schema(
        operation_id="notificacoes_ler_todas", request=None, responses={200: LerTodasSerializer}
    )
    @transaction.atomic
    def post(self, request):
        ids = travar_contexto(request.user)
        autorizadas(request.user).filter(pk__in=ids, lido_em__isnull=True).update(
            lido_em=timezone.now()
        )
        return Response(
            {
                "nao_lidas": autorizadas(request.user)
                .filter(pk__in=ids, lido_em__isnull=True)
                .count()
            }
        )


class PreferenciasView(APIView):
    @extend_schema(
        operation_id="notificacoes_preferencias", responses={200: PreferenciasSerializer}
    )
    def get(self, request):
        return Response(preferencias(request.user))

    @extend_schema(
        operation_id="notificacoes_atualizar_preferencias",
        request=PreferenciasEntradaSerializer,
        responses={200: PreferenciasSerializer},
    )
    @transaction.atomic
    def patch(self, request):
        entrada = PreferenciasEntradaSerializer(data=request.data, partial=True)
        entrada.is_valid(raise_exception=True)
        from .servicos import travar_preferencias

        travar_preferencias(request.user)
        usuario = Usuario.objects.get(pk=request.user.pk)
        dados = (
            dict(usuario.prefs_notificacao) if isinstance(usuario.prefs_notificacao, dict) else {}
        )
        dados.update(entrada.validated_data)
        dados["versao"] = 1
        usuario.prefs_notificacao = dados
        usuario.save(update_fields=["prefs_notificacao"])
        from .models import EntregaNotificacao, EntregaPushDispositivo, EstadoEntrega

        for canal in ("email", "push"):
            if entrada.validated_data.get(canal) is False:
                entregas = EntregaNotificacao.objects.filter(
                    notificacao__destinatario=usuario, canal=canal
                )
                entregas.filter(
                    estado__in=[EstadoEntrega.PENDENTE, EstadoEntrega.RESERVADA]
                ).update(estado=EstadoEntrega.DESCARTADA, resultado="preferencia")
                if canal == "push":
                    EntregaPushDispositivo.objects.filter(
                        entrega__in=entregas,
                        estado__in=[EstadoEntrega.PENDENTE, EstadoEntrega.RESERVADA],
                    ).update(estado=EstadoEntrega.DESCARTADA, resultado="preferencia")
        return Response(preferencias(usuario))


class PushConfiguracaoView(APIView):
    @extend_schema(
        operation_id="notificacoes_push_configuracao", responses={200: PushConfiguracaoSerializer}
    )
    def get(self, request):
        from django.conf import settings

        return Response(
            {
                "habilitado": bool(settings.WEBPUSH_ENABLED and settings.WEBPUSH_PUBLIC_KEY),
                "chave_publica": settings.WEBPUSH_PUBLIC_KEY,
            }
        )


class InscricoesView(APIView):
    @extend_schema(
        operation_id="notificacoes_push_inscrever",
        request=InscricaoEntradaSerializer,
        responses={200: InscricaoResultadoSerializer, 201: InscricaoResultadoSerializer},
    )
    @transaction.atomic
    def post(self, request):
        from django.conf import settings

        if not settings.WEBPUSH_ENABLED or not settings.WEBPUSH_PUBLIC_KEY:
            raise push.PushIndisponivel()
        entrada = InscricaoEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        dados = entrada.validated_data
        push.validar_endpoint(dados["endpoint"])
        push.validar_chaves(**dados["keys"])
        sessao = travar_sessao(request)
        instalacao = travar_instalacao(request.user, dados["instalacao"])
        if instalacao.revogada:
            raise Conflito("Inscrição indisponível.")
        fingerprint = push.fingerprint(dados["endpoint"])
        if instalacao.fingerprint and instalacao.fingerprint != fingerprint:
            raise Conflito("Inscrição indisponível.")
        if not instalacao.fingerprint:
            instalacao.fingerprint = fingerprint
            instalacao.save(update_fields=["fingerprint"])
        _travar_objeto(uuid.UUID(fingerprint[:32]))
        inscricao = (
            InscricaoPush.objects.select_for_update().filter(fingerprint=fingerprint).first()
        )
        criado = inscricao is None
        if inscricao and inscricao.usuario_id != request.user.pk:
            raise Conflito("Inscrição indisponível.")
        if inscricao:
            if inscricao.instalacao == dados["instalacao"]:
                if (
                    not inscricao.ativa
                    or inscricao.sessao_id != sessao.pk
                    or push.decifrar(inscricao.segredo)
                    != {
                        "endpoint": dados["endpoint"],
                        "keys": dados["keys"],
                    }
                ):
                    raise Conflito("Inscrição indisponível.")
            else:
                if inscricao.ativa:
                    raise Conflito("Inscrição indisponível.")
                inscricao.instalacao = dados["instalacao"]
                inscricao.sessao = sessao
                inscricao.geracao += 1
                inscricao.segredo = push.cifrar(dados["endpoint"], **dados["keys"])
                inscricao.ativa = True
                inscricao.save(
                    update_fields=[
                        "instalacao",
                        "sessao",
                        "geracao",
                        "segredo",
                        "ativa",
                        "atualizado_em",
                    ]
                )
        else:
            inscricao = InscricaoPush.objects.create(
                usuario=request.user,
                sessao=sessao,
                fingerprint=fingerprint,
                instalacao=dados["instalacao"],
                segredo=push.cifrar(dados["endpoint"], **dados["keys"]),
            )
        request.session["varal_push_instalacao"] = {
            "id": str(inscricao.pk),
            "geracao": inscricao.geracao,
        }
        return Response(
            InscricaoResultadoSerializer(inscricao).data,
            status=status.HTTP_201_CREATED if criado else status.HTTP_200_OK,
        )


class InstalacaoView(APIView):
    @extend_schema(operation_id="notificacoes_push_revogar_instalacao", responses={204: None})
    @transaction.atomic
    def delete(self, request, instalacao_id):
        travar_sessao(request)
        instalacao = travar_instalacao(request.user, instalacao_id)
        if not instalacao.revogada:
            instalacao.revogada = True
            instalacao.save(update_fields=["revogada"])
        InscricaoPush.objects.filter(
            usuario=request.user, instalacao=instalacao_id, ativa=True
        ).update(ativa=False)
        return Response(status=status.HTTP_204_NO_CONTENT)
