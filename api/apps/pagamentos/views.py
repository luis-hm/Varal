import os
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.boletos.storage import cliente
from apps.boletos.tasks import agendar
from apps.espacos.acesso import lancamento_ou_404
from apps.espacos.servicos import Conflito
from apps.lancamentos.models import Status
from apps.lancamentos.views import CentavosField, ContaDetalheSerializer, _detalhe
from apps.solicitacoes.coordenacao import barreira, coordenado

from . import servicos
from .models import DocumentoComprovante
from .storage import chave, spool
from .tasks import processar_comprovante


class MarcarSerializer(serializers.Serializer):
    pago_em = serializers.DateField()
    valor_centavos_esperado = CentavosField(min_value=1)
    comprovante_id = serializers.UUIDField(required=False, allow_null=True)


class UploadSerializer(serializers.Serializer):
    arquivo = serializers.FileField()
    pagamento_id = serializers.UUIDField(required=False, allow_null=True)


class AnexarSerializer(serializers.Serializer):
    comprovante_id = serializers.UUIDField()


class DocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentoComprovante
        fields = ["id", "estado", "nome", "tamanho", "mime", "criado_em"]


class URLSerializer(serializers.Serializer):
    url = serializers.URLField()
    expira_em = serializers.DateTimeField()


class MarcarView(APIView):
    @extend_schema(
        operation_id="pagamentos_marcar",
        request=MarcarSerializer,
        responses={201: ContaDetalheSerializer},
        summary="Registra uma declaração integral",
    )
    @transaction.atomic
    @coordenado
    def post(self, request, lancamento_id):
        conta = lancamento_ou_404(request.user, lancamento_id)
        servicos.exigir_pagar(request.user, conta)
        entrada = MarcarSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        conta, _ = servicos.marcar(request.user, lancamento_id, entrada.validated_data)
        return _detalhe(request, conta.pk, conta.espaco, status.HTTP_201_CREATED)


class DesfazerView(APIView):
    @extend_schema(
        operation_id="pagamentos_desfazer", request=None, responses={200: ContaDetalheSerializer}
    )
    @transaction.atomic
    @coordenado
    def post(self, request, lancamento_id, pagamento_id):
        conta = servicos.desfazer(request.user, lancamento_id, pagamento_id)
        return _detalhe(request, conta.pk, conta.espaco)


class AnexarView(APIView):
    @extend_schema(
        operation_id="pagamentos_anexar_comprovante",
        request=AnexarSerializer,
        responses={200: ContaDetalheSerializer},
    )
    @transaction.atomic
    @coordenado
    def post(self, request, lancamento_id, pagamento_id):
        conta = lancamento_ou_404(request.user, lancamento_id)
        servicos.exigir_pagar(request.user, conta)
        entrada = AnexarSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        conta = servicos.anexar(
            request.user, lancamento_id, pagamento_id, entrada.validated_data["comprovante_id"]
        )
        return _detalhe(request, conta.pk, conta.espaco)


class UploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        operation_id="comprovantes_upload",
        request=UploadSerializer,
        responses={202: DocumentoSerializer},
    )
    def post(self, request, lancamento_id):
        conta = lancamento_ou_404(request.user, lancamento_id)
        servicos.exigir_pagar(request.user, conta)
        entrada = UploadSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        arquivo = entrada.validated_data["arquivo"]
        if not 0 < arquivo.size <= 5 * 1024 * 1024:
            raise ValidationError({"arquivo": ["Envie arquivo de até 5 MiB."]})
        pk = uuid.uuid4()
        path = spool(pk)
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(path.parent, 0o700)
        nome = (
            "".join(
                c for c in os.path.basename(arquivo.name) if c.isprintable() and c not in "/\\"
            )[:200]
            or "comprovante"
        )
        try:
            with path.open("xb") as out:
                os.chmod(path, 0o600)
                for chunk in arquivo.chunks():
                    out.write(chunk)
            with transaction.atomic():
                barreira()
                conta = servicos.conta_travada(request.user, lancamento_id)
                servicos.exigir_pagar(request.user, conta)
                alvo_id = entrada.validated_data.get("pagamento_id")
                if alvo_id:
                    pagamento = servicos.pagamento_alvo(conta, alvo_id)
                    from apps.solicitacoes.models import ParPagamento

                    if ParPagamento.objects.filter(derivada=pagamento).exists():
                        raise Conflito("Comprovante deve ser registrado no grupo.")
                    if not servicos.pode_desfazer(request.user, conta, pagamento):
                        raise PermissionDenied()
                    if (
                        pagamento.desfeito_em
                        or conta.status != Status.PAGA
                        or not servicos.pode_anexar(request.user, conta, pagamento)
                    ):
                        raise Conflito("Pagamento não aceita comprovante.")
                elif conta.status != Status.PENDENTE:
                    raise Conflito("Só conta pendente aceita comprovante inicial.")
                doc = DocumentoComprovante.objects.create(
                    id=pk,
                    lancamento=conta,
                    criado_por=request.user,
                    pagamento_alvo_id=alvo_id,
                    versao=conta.versao_pagamento,
                    nome=nome,
                    tamanho=arquivo.size,
                )
                transaction.on_commit(lambda: agendar(processar_comprovante, str(pk)))
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return Response(DocumentoSerializer(doc).data, status=202)


class DocumentoView(APIView):
    @extend_schema(operation_id="comprovantes_detalhe", responses={200: DocumentoSerializer})
    @transaction.atomic
    @coordenado
    def get(self, request, documento_id):
        return Response(
            DocumentoSerializer(servicos.documento_ou_404(request.user, documento_id)).data
        )


class ArquivoView(APIView):
    @extend_schema(operation_id="comprovantes_arquivo", responses={200: URLSerializer})
    @transaction.atomic
    @coordenado
    def get(self, request, documento_id):
        doc = servicos.documento_ou_404(request.user, documento_id)
        if doc.estado != "valido":
            raise NotFound()
        url = cliente(publico=True).generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.S3_BUCKET_NAME,
                "Key": chave(doc.pk),
                "ResponseContentType": doc.mime,
                "ResponseContentDisposition": "inline",
            },
            ExpiresIn=60,
        )
        return Response({"url": url, "expira_em": timezone.now() + timedelta(seconds=60)})
