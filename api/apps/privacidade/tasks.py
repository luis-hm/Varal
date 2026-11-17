"""RN30 snapshot generation, fenced publication and durable object cleanup."""

import hashlib
import json
import tempfile
import uuid
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.boletos.models import DocumentoBoleto, Instrumento
from apps.boletos.storage import cliente
from apps.boletos.tasks import _travar_objeto, agendar
from apps.espacos.models import Membro
from apps.lancamentos.models import Historico, Lancamento
from apps.notificacoes.acesso import autorizadas
from apps.notificacoes.views import NotificacaoSerializer, preferencias
from apps.pagamentos.models import DocumentoComprovante, Pagamento
from apps.recorrencias.models import Recorrencia
from apps.solicitacoes.coordenacao import barreira

from .models import Exportacao, LimpezaExportacao, ParteExportacao, RevisaoExportacao

LOTE = 500
LEASE = timedelta(minutes=10)
MAGIC = b"VARAL-EXPORT-2\n"
DOCUMENTOS = ("documentos_pdf", "documentos_comprovante")
CATEGORIAS = (
    "contas_pessoais",
    "instrumentos",
    "pagamentos",
    "historicos",
    "recorrencias_pessoais",
    "participacoes",
    "avisos",
    "documentos_pdf",
    "documentos_comprovante",
)


class TentativaInvalida(Exception):
    pass


def chave_objeto(pk):
    return f"exportacoes/{pk}.json"


def _revisao():
    return RevisaoExportacao.objects.values_list("epoca", "valor").get(pk=1)


def _valida(job, tentativa, revisao):
    return bool(
        job
        and job.estado == Exportacao.Estado.PROCESSANDO
        and job.tentativa == tentativa
        and job.expira_em > timezone.now()
        and job.lease_ate
        and job.lease_ate > timezone.now()
        and _revisao() == revisao
    )


def _fontes(user, categoria):
    pessoal = user.espacos.filter(tipo="pessoal")
    contas = Lancamento.objects.filter(espaco__in=pessoal)
    if categoria == "contas_pessoais":
        return contas, (
            "id",
            "descricao",
            "valor_centavos",
            "vencimento",
            "status",
            "competencia",
            "recorrencia_id",
            "criado_em",
            "atualizado_em",
        )
    if categoria == "instrumentos":
        return Instrumento.objects.filter(lancamento__in=contas), (
            "lancamento_id",
            "tipo",
            "codigo",
            "chave_pix",
            "beneficiario",
            "data_emissao",
        )
    if categoria == "pagamentos":
        return Pagamento.objects.filter(lancamento__in=contas), (
            "id",
            "lancamento_id",
            "pago_em",
            "valor_pago_centavos",
            "criado_em",
            "desfeito_em",
        )
    if categoria == "historicos":
        return Historico.objects.filter(lancamento__in=contas), (
            "id",
            "lancamento_id",
            "acao",
            "criado_em",
        )
    if categoria == "recorrencias_pessoais":
        return Recorrencia.objects.filter(espaco__in=pessoal), (
            "id",
            "descricao",
            "dia_vencimento",
            "valor_tipo",
            "valor_centavos",
            "estado",
            "motivo_pausa",
            "cursor",
            "criado_em",
            "atualizado_em",
        )
    if categoria == "participacoes":
        return Membro.objects.filter(usuario=user).select_related("espaco"), (
            "id",
            "espaco_id",
            "papel",
            "criado_em",
        )
    if categoria == "avisos":
        return autorizadas(user).select_related("evento", "evento__lancamento"), None
    if categoria == "documentos_pdf":
        return DocumentoBoleto.objects.filter(
            Q(vinculado_em__isnull=False)
            | Q(criado_por=user, criado_em__gt=timezone.now() - timedelta(hours=24)),
            espaco__in=pessoal,
            estado__in=("lido", "conferencia_manual"),
        ), (
            "id",
            "nome",
            "tamanho",
            "criado_em",
            "lancamento_id",
            "destino_id",
            "vinculado_em",
        )
    if categoria == "documentos_comprovante":
        return DocumentoComprovante.objects.filter(
            Q(vinculado_em__isnull=False)
            | Q(criado_por=user, criado_em__gt=timezone.now() - timedelta(hours=24)),
            lancamento__in=contas,
            estado="valido",
        ), (
            "id",
            "nome",
            "tamanho",
            "mime",
            "criado_em",
            "lancamento_id",
            "pagamento_id",
            "pagamento_alvo_id",
            "vinculado_em",
        )
    raise ValueError("Unknown export category")


def _json(value):
    return json.loads(json.dumps(value, cls=DjangoJSONEncoder))


def _lote(job_id, token, revisao, categoria, cursor):
    with transaction.atomic():
        barreira()
        job = (
            Exportacao.objects.select_for_update()
            .select_related("usuario")
            .filter(pk=job_id)
            .first()
        )
        if not _valida(job, token, revisao):
            raise TentativaInvalida()
        fontes, campos = _fontes(job.usuario, categoria)
        if cursor is not None:
            fontes = fontes.filter(pk__gt=cursor)
        objetos = list(fontes.order_by("pk")[:LOTE])
        if campos is None:
            dados = [NotificacaoSerializer(obj).data for obj in objetos]
        else:
            dados = [{campo: getattr(obj, campo) for campo in campos} for obj in objetos]
            if categoria == "participacoes":
                for linha, objeto in zip(dados, objetos, strict=True):
                    linha["grupo_nome"] = objeto.espaco.nome
            if categoria == "historicos":
                permitidas = {
                    "descricao",
                    "valor_centavos",
                    "vencimento",
                    "motivo",
                    "competencia",
                }
                for linha, objeto in zip(dados, objetos, strict=True):
                    linha["dados"] = {k: v for k, v in objeto.dados.items() if k in permitidas}
        if _revisao() != revisao:
            raise TentativaInvalida()
        if objetos:
            ParteExportacao.objects.create(
                exportacao=job,
                tentativa=token,
                categoria=categoria,
                cursor=str(objetos[-1].pk),
                dados=_json(dados),
            )
        job.lease_ate = timezone.now() + LEASE
        job.save(update_fields=["lease_ate"])
        return objetos[-1].pk if objetos else None


def _montar(job, token, perfil):
    # The file is private and temporary; no network or parser runs under the barrier.
    arquivo = tempfile.TemporaryFile(mode="w+b")
    arquivo.write(MAGIC + b'{"schema_version":1,"gerado_em":')
    arquivo.write(json.dumps(timezone.now(), cls=DjangoJSONEncoder).encode())
    arquivo.write(b',"perfil":')
    arquivo.write(json.dumps(perfil, cls=DjangoJSONEncoder).encode())
    for categoria in CATEGORIAS:
        if categoria in DOCUMENTOS:
            continue
        arquivo.write(b"," + json.dumps(categoria).encode() + b":[")
        primeiro = True
        partes = ParteExportacao.objects.filter(
            exportacao=job, tentativa=token, categoria=categoria
        ).order_by("cursor")
        for parte in partes.iterator():
            for dado in parte.dados:
                if not primeiro:
                    arquivo.write(b",")
                arquivo.write(
                    json.dumps(dado, cls=DjangoJSONEncoder, separators=(",", ":")).encode()
                )
                primeiro = False
        arquivo.write(b"]")
    arquivo.write(b"}")
    arquivo.seek(0)
    return arquivo


def linha_manifesto(item):
    return (
        json.dumps(item, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode() + b"\n"
    )


def gerar_manifestos(job_id, token):
    manifestos = {}
    for categoria in DOCUMENTOS:
        digest = hashlib.sha256()
        quantidade = 0
        partes = ParteExportacao.objects.filter(
            exportacao_id=job_id, tentativa=token, categoria=categoria
        ).order_by("cursor")
        for parte in partes.iterator():
            if not isinstance(parte.dados, list) or len(parte.dados) > LOTE:
                raise TentativaInvalida()
            for item in parte.dados:
                digest.update(linha_manifesto(item))
                quantidade += 1
        manifestos[categoria] = {"count": quantidade, "sha256": digest.hexdigest()}
    return manifestos


@shared_task
def gerar_exportacao(job_id):
    token, objeto = uuid.uuid4(), uuid.uuid4()
    with transaction.atomic():
        barreira()
        job = (
            Exportacao.objects.select_for_update()
            .select_related("usuario")
            .filter(pk=job_id)
            .first()
        )
        if (
            not job
            or job.expira_em <= timezone.now()
            or job.estado not in ("pendente", "processando")
        ):
            return
        if job.estado == "processando" and job.lease_ate and job.lease_ate > timezone.now():
            return
        revisao = _revisao()
        perfil = {
            "id": str(job.usuario_id),
            "nome": job.usuario.nome,
            "email": job.usuario.email,
            "telefone": job.usuario.telefone,
            "preferencias": preferencias(job.usuario),
        }
        job.estado, job.tentativa, job.objeto_id = "processando", token, objeto
        job.geracao += 1
        job.lease_ate = timezone.now() + LEASE
        job.epoca, job.revisao = revisao
        job.save(
            update_fields=[
                "estado",
                "tentativa",
                "objeto_id",
                "geracao",
                "lease_ate",
                "epoca",
                "revisao",
            ]
        )
        LimpezaExportacao.objects.create(pk=objeto)
    try:
        for categoria in CATEGORIAS:
            cursor = None
            while True:
                cursor = _lote(job_id, token, revisao, categoria, cursor)
                if cursor is None:
                    break
        manifestos = gerar_manifestos(job_id, token)
        with _montar(job_id, token, perfil) as arquivo:
            sha = hashlib.sha256()
            while bloco := arquivo.read(65536):
                sha.update(bloco)
            artefato_sha256 = sha.hexdigest()
            arquivo.seek(0)
            with transaction.atomic():
                _travar_objeto(objeto)
                if not Exportacao.objects.filter(
                    pk=job_id, tentativa=token, estado="processando"
                ).exists():
                    raise TentativaInvalida()
                cliente().put_object(
                    Bucket=settings.S3_BUCKET_NAME,
                    Key=chave_objeto(objeto),
                    Body=arquivo,
                    ContentType="application/octet-stream",
                )
            LimpezaExportacao.objects.filter(pk=objeto).update(incerta=False)
        with transaction.atomic():
            barreira()
            job = Exportacao.objects.select_for_update().filter(pk=job_id).first()
            if not _valida(job, token, revisao):
                raise TentativaInvalida()
            if job.objeto_id != objeto:
                raise TentativaInvalida()
            job.estado = "pronto"
            job.formato_interno = 2
            job.artefato_sha256 = artefato_sha256
            job.manifestos = manifestos
            job.save(
                update_fields=[
                    "estado",
                    "formato_interno",
                    "artefato_sha256",
                    "manifestos",
                ]
            )
    except Exception:
        Exportacao.objects.filter(pk=job_id, tentativa=token, estado="processando").update(
            estado="falhou"
        )
    finally:
        agendar(recuperar_exportacoes)


@shared_task
def recuperar_exportacoes():
    agora = timezone.now()
    Exportacao.objects.filter(expira_em__lte=agora).exclude(estado="expirado").update(
        estado="expirado"
    )
    ParteExportacao.objects.filter(exportacao__expira_em__lte=agora).delete()
    for pk in LimpezaExportacao.objects.values_list("pk", flat=True).iterator():
        try:
            with transaction.atomic():
                _travar_objeto(pk)
                item = LimpezaExportacao.objects.filter(pk=pk).first()
                if (
                    not item
                    or Exportacao.objects.filter(
                        objeto_id=pk,
                        estado__in=("processando", "pronto"),
                        expira_em__gt=agora,
                    ).exists()
                ):
                    continue
                cliente().delete_object(Bucket=settings.S3_BUCKET_NAME, Key=chave_objeto(pk))
                if not item.incerta:
                    LimpezaExportacao.objects.filter(pk=pk, geracao=item.geracao).delete()
        except Exception:
            continue
    for pk in (
        Exportacao.objects.filter(estado="pendente", expira_em__gt=agora)
        .values_list("pk", flat=True)
        .iterator()
    ):
        agendar(gerar_exportacao, str(pk))
    for pk in (
        Exportacao.objects.filter(estado="processando", lease_ate__lt=agora, expira_em__gt=agora)
        .values_list("pk", flat=True)
        .iterator()
    ):
        agendar(gerar_exportacao, str(pk))


@shared_task
def recuperar_terminais_exclusao():
    from .exclusao import publicar_terminal
    from .journal import JournalIndisponivel, registrar
    from .models import OperacaoExclusao

    # A lost PREPARE response is reconciled by replaying the identical message.
    # Only the authoritative live ledger can decide ABORT, under its row lock.
    limite = timezone.now() - timedelta(minutes=10)
    preparadas = OperacaoExclusao.objects.filter(
        estado="preparada", criado_em__lt=limite
    ).values_list("pk", flat=True)
    for operacao_id in preparadas.iterator():
        op = OperacaoExclusao.objects.filter(pk=operacao_id, estado="preparada").first()
        if not op:
            continue
        try:
            recibo = registrar(op.pk, op.owner_id, "PREPARE", op.fence)
        except (JournalIndisponivel, ValueError):
            continue
        with transaction.atomic():
            atual = OperacaoExclusao.objects.select_for_update().filter(pk=op.pk).first()
            if not atual or atual.estado != "preparada" or atual.criado_em >= limite:
                continue
            if atual.recibo_prepare and atual.recibo_prepare != recibo:
                continue
            atual.recibo_prepare = recibo
            atual.estado = "abortada"
            atual.save(update_fields=["recibo_prepare", "estado"])
    pendentes = OperacaoExclusao.objects.filter(
        estado__in=("commitada", "abortada"), recibo_terminal__isnull=True
    ).values_list("pk", flat=True)
    for operacao_id in pendentes.iterator():
        publicar_terminal(operacao_id)
