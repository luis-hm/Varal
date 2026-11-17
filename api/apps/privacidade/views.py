"""Private, session-bound entry points for the RN30 operations."""

import hashlib
import secrets
from datetime import timedelta

from allauth.account.internal.flows.reauthentication import did_recently_reauthenticate
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.solicitacoes.coordenacao import barreira

from .models import Exportacao, IntencaoExclusao


class ExportacaoPedidoSerializer(serializers.Serializer):
    chave = serializers.UUIDField()

    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) != {"chave"}:
            raise serializers.ValidationError("Informe apenas a chave de idempotência.")
        return super().to_internal_value(data)


class ExportacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exportacao
        fields = ("id", "estado", "criado_em", "expira_em")


class IntencaoSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    segredo = serializers.CharField()
    expira_em = serializers.DateTimeField()


class ConfirmacaoExclusaoSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    segredo = serializers.CharField()
    confirmar = serializers.BooleanField()


class ReauthMetaSerializer(serializers.Serializer):
    is_authenticated = serializers.BooleanField()


class ReauthRespostaSerializer(serializers.Serializer):
    status = serializers.IntegerField()
    code = serializers.CharField(required=False)
    meta = ReauthMetaSerializer()


def sem_prova(request, *, travar=False):
    from importlib import import_module

    from django.conf import settings
    from django.contrib.auth import HASH_SESSION_KEY, SESSION_KEY
    from django.contrib.sessions.models import Session
    from django.utils.crypto import constant_time_compare

    from apps.contas_usuario.models import Usuario

    session_key = request.session.session_key
    sessoes = Session.objects.filter(session_key=session_key, expire_date__gt=timezone.now())
    if travar:
        sessoes = sessoes.select_for_update()
    sessao = sessoes.first()
    usuario = Usuario.objects.filter(pk=request.user.pk, is_active=True).first()
    dados = sessao.get_decoded() if sessao else {}
    if (
        not usuario
        or dados.get(SESSION_KEY) != str(usuario.pk)
        or not constant_time_compare(
            dados.get(HASH_SESSION_KEY, ""), usuario.get_session_auth_hash()
        )
    ):
        return Response({"status": 401, "meta": {"is_authenticated": False}}, status=401)
    original = request._request.session
    try:
        store = import_module(settings.SESSION_ENGINE).SessionStore
        request._request.session = store(session_key=session_key)
        if did_recently_reauthenticate(request._request):
            return None
    finally:
        request._request.session = original
    return Response(
        {"status": 401, "code": "reauth_required", "meta": {"is_authenticated": True}},
        status=status.HTTP_401_UNAUTHORIZED,
    )


def fingerprint_sessao(request):
    key = request.session.session_key
    if not key:
        return ""
    return salted_hmac("varal.exclusao.sessao", key, algorithm="sha256").hexdigest()


class ExportacoesView(APIView):
    @extend_schema(
        operation_id="privacidade_exportacao_solicitar",
        request=ExportacaoPedidoSerializer,
        responses={202: ExportacaoSerializer, 401: ReauthRespostaSerializer},
    )
    def post(self, request):
        reauth = sem_prova(request)
        if reauth:
            return reauth
        entrada = ExportacaoPedidoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        chave = entrada.validated_data["chave"]
        digest = hashlib.sha256(b"exportacao:v1").hexdigest()
        with transaction.atomic():
            barreira()
            reauth = sem_prova(request, travar=True)
            if reauth:
                return reauth
            job, created = Exportacao.objects.get_or_create(
                usuario=request.user,
                chave=chave,
                defaults={"corpo_hash": digest, "expira_em": timezone.now() + timedelta(hours=24)},
            )
            if not created and job.corpo_hash != digest:
                return Response(status=status.HTTP_409_CONFLICT)
            if created:
                from apps.boletos.tasks import agendar

                from .tasks import gerar_exportacao

                transaction.on_commit(lambda: agendar(gerar_exportacao, str(job.pk)))
        response = Response(ExportacaoSerializer(job).data, status=status.HTTP_202_ACCEPTED)
        response["Cache-Control"] = "private, no-store"
        return response


class ExportacaoView(APIView):
    @extend_schema(
        operation_id="privacidade_exportacao_estado", responses={200: ExportacaoSerializer}
    )
    def get(self, request, exportacao_id):
        from django.shortcuts import get_object_or_404

        job = get_object_or_404(Exportacao, pk=exportacao_id, usuario=request.user)
        data = dict(ExportacaoSerializer(job).data)
        if job.expira_em <= timezone.now():
            data["estado"] = Exportacao.Estado.EXPIRADO
        response = Response(data)
        response["Cache-Control"] = "private, no-store"
        return response


class IntencaoView(APIView):
    @extend_schema(
        operation_id="privacidade_exclusao_intencao",
        request=None,
        responses={201: IntencaoSerializer, 401: ReauthRespostaSerializer},
    )
    def post(self, request):
        reauth = sem_prova(request)
        if reauth:
            return reauth
        session_hash = fingerprint_sessao(request)
        if not session_hash:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        segredo = secrets.token_urlsafe(32)
        with transaction.atomic():
            barreira()
            reauth = sem_prova(request, travar=True)
            if reauth:
                return reauth
            intencao = IntencaoExclusao.objects.create(
                usuario=request.user,
                segredo_hash=hashlib.sha256(segredo.encode()).hexdigest(),
                sessao_hash=session_hash,
                expira_em=timezone.now() + timedelta(minutes=5),
            )
        response = Response(
            {"id": intencao.pk, "segredo": segredo, "expira_em": intencao.expira_em},
            status=status.HTTP_201_CREATED,
        )
        response["Cache-Control"] = "private, no-store"
        return response


def excluir_me(request):
    from django.contrib.auth.models import AnonymousUser

    from .exclusao import excluir

    reauth = sem_prova(request)
    if reauth:
        return reauth
    entrada = ConfirmacaoExclusaoSerializer(data=request.data)
    entrada.is_valid(raise_exception=True)
    if not entrada.validated_data["confirmar"]:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    excluir(
        request,
        entrada.validated_data["id"],
        entrada.validated_data["segredo"],
        fingerprint_sessao(request),
    )
    request.session.flush()
    request._request.user = AnonymousUser()
    return Response(status=status.HTTP_204_NO_CONTENT)
