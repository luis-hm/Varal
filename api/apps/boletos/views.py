from dataclasses import asdict

from django.db import transaction
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.espacos.views import ErroSerializer

from .serializers import (
    DocumentoPDFSerializer,
    InstrumentoEntradaSerializer,
    LeituraSerializer,
    UploadPDFSerializer,
    URLPDFSerializer,
    dados_instrumento,
    ler_entrada,
)


class LerView(APIView):
    @extend_schema(
        operation_id="boletos_ler",
        summary="Conferir boleto/Pix sem gravar; não consulta URL nem titularidade (RF08/RF09)",
        request=InstrumentoEntradaSerializer,
        responses={200: LeituraSerializer, 400: ErroSerializer, 403: ErroSerializer},
        examples=[
            OpenApiExample("Chave Pix", value={"chave_pix": "+5585999999999"}, request_only=True),
            OpenApiExample(
                "Chave lida",
                value={
                    "instrumento": {
                        "tipo": "pix",
                        "codigo": None,
                        "chave_pix": "+5585999999999",
                        "beneficiario": None,
                    },
                    "valor_centavos": None,
                    "vencimento": None,
                    "vencimentos_possiveis": [],
                    "avisos": ["Chave não consultada; existência e titularidade não verificadas."],
                },
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        entrada = InstrumentoEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        resultado = ler_entrada(entrada.validated_data)
        dados = asdict(resultado)
        corpo = {
            "instrumento": dados_instrumento(resultado),
            **{
                k: dados[k]
                for k in ("valor_centavos", "vencimento", "vencimentos_possiveis", "avisos")
            },
        }
        return Response(LeituraSerializer(corpo).data)


class UploadPDFView(APIView):
    from rest_framework.parsers import FormParser, MultiPartParser

    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        operation_id="boletos_pdf_upload",
        request=UploadPDFSerializer,
        responses={202: DocumentoPDFSerializer},
    )
    def post(self, request, espaco_id):
        import os
        import uuid

        from django.db import transaction
        from rest_framework.exceptions import ValidationError

        from apps.espacos.acesso import espaco_ou_404, lancamento_ou_404
        from apps.espacos.servicos import Conflito
        from apps.lancamentos.models import ABERTOS

        from .models import DocumentoBoleto
        from .storage import spool
        from .tasks import agendar, processar_pdf

        entrada = UploadPDFSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        destino_id = entrada.validated_data.get("lancamento_id")
        if destino_id:
            conta = lancamento_ou_404(request.user, destino_id, "editar_conta")
            if str(conta.espaco_id) != str(espaco_id):
                from rest_framework.exceptions import NotFound

                raise NotFound()
            if conta.status not in ABERTOS:
                raise Conflito("Só contas abertas podem receber PDF.")
            espaco = conta.espaco
        else:
            espaco = espaco_ou_404(request.user, espaco_id, "criar_conta")
        arquivo = entrada.validated_data["arquivo"]
        if (
            arquivo.content_type != "application/pdf"
            or not 0 < arquivo.size <= 5 * 1024 * 1024
            or arquivo.read(5) != b"%PDF-"
        ):
            raise ValidationError({"arquivo": ["Envie um PDF válido de até 5 MiB."]})
        arquivo.seek(0)
        pk = uuid.uuid4()
        path = spool(pk)
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(path.parent, 0o700)
        nome = (
            "".join(
                c for c in os.path.basename(arquivo.name) if c.isprintable() and c not in "/\\"
            )[:200]
            or "boleto.pdf"
        )
        try:
            with path.open("xb") as out:
                os.chmod(path, 0o600)
                for chunk in arquivo.chunks():
                    out.write(chunk)
            with transaction.atomic():
                from apps.espacos.models import Espaco, Membro
                from apps.espacos.servicos import _admins_travados
                from apps.solicitacoes.coordenacao import barreira

                barreira()
                if espaco.tipo == Espaco.Tipo.GRUPO:
                    _admins_travados([espaco.pk])
                    list(
                        Membro.objects.select_for_update(of=("self",))
                        .filter(espaco=espaco, usuario=request.user)
                        .values_list("pk", flat=True)
                    )
                else:
                    list(Espaco.objects.select_for_update().filter(pk=espaco.pk).values("pk"))
                if destino_id:
                    conta = lancamento_ou_404(request.user, destino_id, "editar_conta", travar=True)
                    if conta.espaco_id != espaco.pk or conta.status not in ABERTOS:
                        raise Conflito("Só contas abertas podem receber PDF.")
                else:
                    espaco_ou_404(request.user, espaco.pk, "criar_conta")
                doc = DocumentoBoleto.objects.create(
                    id=pk,
                    espaco=espaco,
                    criado_por=request.user,
                    destino_id=destino_id,
                    nome=nome,
                    tamanho=arquivo.size,
                )
                transaction.on_commit(lambda: agendar(processar_pdf, str(pk)))
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return Response(DocumentoPDFSerializer(doc).data, status=202)


class DocumentoPDFView(APIView):
    @extend_schema(operation_id="boletos_pdf_detalhe", responses={200: DocumentoPDFSerializer})
    @transaction.atomic
    def get(self, request, documento_id):
        from apps.solicitacoes.coordenacao import barreira

        from .pdf_servicos import documento_ou_404

        barreira()
        return Response(DocumentoPDFSerializer(documento_ou_404(request.user, documento_id)).data)


def _url_pdf(doc):
    from datetime import timedelta

    from django.conf import settings
    from django.utils import timezone
    from rest_framework.exceptions import NotFound

    from .storage import chave, cliente

    if doc.estado not in ("lido", "conferencia_manual"):
        raise NotFound()
    url = cliente(publico=True).generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.S3_BUCKET_NAME,
            "Key": chave(doc.pk),
            "ResponseContentType": "application/pdf",
            "ResponseContentDisposition": "inline",
        },
        ExpiresIn=60,
    )
    return Response({"url": url, "expira_em": timezone.now() + timedelta(seconds=60)})


class ArquivoPDFView(APIView):
    @extend_schema(operation_id="boletos_pdf_arquivo", responses={200: URLPDFSerializer})
    @transaction.atomic
    def get(self, request, documento_id):
        from apps.solicitacoes.coordenacao import barreira

        from .pdf_servicos import documento_ou_404

        barreira()
        return _url_pdf(documento_ou_404(request.user, documento_id))


class ContaPDFView(APIView):
    @extend_schema(operation_id="lancamentos_pdf_arquivo", responses={200: URLPDFSerializer})
    @transaction.atomic
    def get(self, request, lancamento_id):
        from rest_framework.exceptions import NotFound

        from apps.espacos.acesso import lancamento_ou_404
        from apps.solicitacoes.coordenacao import barreira

        from .models import DocumentoBoleto

        barreira()
        conta = lancamento_ou_404(request.user, lancamento_id, travar=True)
        doc = DocumentoBoleto.objects.filter(lancamento=conta).first()
        if not doc:
            raise NotFound()
        return _url_pdf(doc)
