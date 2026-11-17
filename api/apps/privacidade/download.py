"""Draft: bounded RN30 download, to integrate after the frozen test run."""

import copy
import hashlib
import json
import tempfile
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.http import FileResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.boletos.storage import chave as chave_pdf
from apps.boletos.storage import cliente
from apps.pagamentos.storage import chave as chave_comprovante
from apps.solicitacoes.coordenacao import barreira

from .models import Exportacao, ParteExportacao, RevisaoExportacao
from .tasks import DOCUMENTOS, LOTE, MAGIC, _fontes, chave_objeto, linha_manifesto
from .views import ReauthRespostaSerializer, sem_prova


class DownloadInvalido(Exception):
    pass


def _estado(job, captura):
    return bool(
        job
        and job.estado == "pronto"
        and job.expira_em > timezone.now()
        and job.tentativa == captura["tentativa"]
        and job.geracao == captura["geracao"]
        and job.objeto_id == captura["objeto_id"]
        and job.formato_interno == 2
        and job.artefato_sha256 == captura["artefato_sha256"]
        and job.manifestos == captura["manifestos"]
        and (job.epoca, job.revisao) == captura["revisao"]
    )


def _revisao():
    return RevisaoExportacao.objects.values_list("epoca", "valor").get(pk=1)


def _copiar_s3(job, s3):
    arquivo = tempfile.TemporaryFile(mode="w+b")
    body = None
    try:
        body = s3.get_object(Bucket=settings.S3_BUCKET_NAME, Key=chave_objeto(job.objeto_id))[
            "Body"
        ]
        digest = hashlib.sha256()
        while bloco := body.read(65536):
            digest.update(bloco)
            arquivo.write(bloco)
        if digest.hexdigest() != job.artefato_sha256:
            raise DownloadInvalido()
        total = arquivo.tell()
        if total <= len(MAGIC):
            raise DownloadInvalido()
        arquivo.seek(0)
        if arquivo.read(len(MAGIC)) != MAGIC:
            raise DownloadInvalido()
        arquivo.seek(-1, 2)
        if arquivo.read(1) != b"}":
            raise DownloadInvalido()
        arquivo.seek(len(MAGIC))
        return arquivo, total - len(MAGIC) - 1
    except Exception:
        arquivo.close()
        raise
    finally:
        if body is not None:
            body.close()


def _manifesto(request, job, captura, categoria):
    arquivo = tempfile.TemporaryFile(mode="w+b")
    digest, contagem, anterior, prazo_min = hashlib.sha256(), 0, -1, None
    try:
        partes = ParteExportacao.objects.filter(
            exportacao_id=job.pk, tentativa=captura["tentativa"], categoria=categoria
        ).order_by("cursor")
        for parte in partes.iterator():
            lote = parte.dados
            if not isinstance(lote, list) or not lote or len(lote) > LOTE:
                raise DownloadInvalido()
            ids = []
            for item in lote:
                if not isinstance(item, dict):
                    raise DownloadInvalido()
                pk = uuid.UUID(item["id"])
                if str(pk) != item["id"] or pk.int <= anterior:
                    raise DownloadInvalido()
                anterior = pk.int
                ids.append(pk)
                if not item.get("vinculado_em"):
                    criado = parse_datetime(item.get("criado_em", ""))
                    if not criado or timezone.is_naive(criado):
                        raise DownloadInvalido()
                    prazo = criado + timedelta(hours=24)
                    prazo_min = min(prazo_min, prazo) if prazo_min else prazo
            with transaction.atomic():
                barreira()
                atual = Exportacao.objects.filter(pk=job.pk, usuario=request.user).first()
                if not _estado(atual, captura) or _revisao() != captura["revisao"]:
                    raise DownloadInvalido()
                fonte, _ = _fontes(request.user, categoria)
                if set(fonte.filter(pk__in=ids).values_list("pk", flat=True)) != set(ids):
                    raise DownloadInvalido()
                if _revisao() != captura["revisao"]:
                    raise DownloadInvalido()
            # No file operation under B.
            for item in lote:
                linha = linha_manifesto(item)
                digest.update(linha)
                arquivo.write(linha)
                contagem += 1
        esperado = captura["manifestos"].get(categoria)
        if esperado != {"count": contagem, "sha256": digest.hexdigest()}:
            raise DownloadInvalido()
        arquivo.seek(0)
        return arquivo, prazo_min
    except Exception:
        arquivo.close()
        raise


class ExportacaoDownloadView(APIView):
    @extend_schema(
        operation_id="privacidade_exportacao_baixar",
        responses={200: OpenApiTypes.BINARY, 401: ReauthRespostaSerializer},
    )
    def get(self, request, exportacao_id):
        reauth = sem_prova(request)
        if reauth:
            return reauth
        job = Exportacao.objects.filter(pk=exportacao_id, usuario=request.user).first()
        if not job:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if job.expira_em <= timezone.now():
            return Response(status=status.HTTP_410_GONE)
        if job.estado != "pronto" or job.formato_interno != 2 or not job.objeto_id:
            return Response(status=status.HTTP_409_CONFLICT)
        captura = {
            "tentativa": job.tentativa,
            "geracao": job.geracao,
            "objeto_id": job.objeto_id,
            "revisao": (job.epoca, job.revisao),
            "artefato_sha256": job.artefato_sha256,
            "manifestos": copy.deepcopy(job.manifestos),
        }
        if not isinstance(job.manifestos, dict) or set(job.manifestos) != set(DOCUMENTOS):
            return Response(status=status.HTTP_409_CONFLICT)
        fontes = []
        corpo = None
        final = None
        try:
            # Construction and credentials refresh are both outside B.
            s3, publico = cliente(), cliente(publico=True)
            corpo, restantes = _copiar_s3(job, s3)
            prazos = []
            for categoria in DOCUMENTOS:
                arquivo, prazo = _manifesto(request, job, captura, categoria)
                fontes.append((categoria, arquivo))
                if prazo:
                    prazos.append(prazo)
            with transaction.atomic():
                barreira()
                atual = (
                    Exportacao.objects.select_for_update()
                    .filter(pk=job.pk, usuario=request.user)
                    .first()
                )
                reauth = sem_prova(request, travar=True)
                if reauth:
                    return reauth
                if not _estado(atual, captura) or (prazos and min(prazos) <= timezone.now()):
                    raise DownloadInvalido()
                # Final authorization point: no subsequent domain reads in this transaction.
                if _revisao() != captura["revisao"]:
                    raise DownloadInvalido()
            final = tempfile.TemporaryFile(mode="w+b")
            while restantes:
                bloco = corpo.read(min(65536, restantes))
                if not bloco:
                    raise DownloadInvalido()
                final.write(bloco)
                restantes -= len(bloco)
            for categoria, arquivo in fontes:
                final.write(b"," + json.dumps(categoria).encode() + b":[")
                primeira = True
                for linha in arquivo:
                    item = json.loads(linha)
                    obter_chave = chave_pdf if categoria == "documentos_pdf" else chave_comprovante
                    item["url"] = publico.generate_presigned_url(
                        "get_object",
                        Params={
                            "Bucket": settings.S3_BUCKET_NAME,
                            "Key": obter_chave(item["id"]),
                        },
                        ExpiresIn=60,
                    )
                    item["url_validade_segundos"] = 60
                    if not primeira:
                        final.write(b",")
                    final.write(json.dumps(item, ensure_ascii=True, separators=(",", ":")).encode())
                    primeira = False
                final.write(b"]")
            final.write(b"}")
            final.seek(0)
            response = FileResponse(
                final,
                as_attachment=True,
                filename="varal-dados.json",
                content_type="application/json",
            )
            response["Cache-Control"] = "private, no-store"
            final = None  # FileResponse owns and closes it.
            return response
        except (DownloadInvalido, ValueError, KeyError, TypeError):
            return Response(status=status.HTTP_409_CONFLICT)
        except Exception:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        finally:
            if corpo is not None:
                corpo.close()
            for _, arquivo in fontes:
                arquivo.close()
            if final is not None:
                final.close()
