"""Two-phase deletion with an independently durable PREPARE receipt."""

import hashlib
import hmac
from contextlib import contextmanager
from contextvars import ContextVar

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException

from apps.espacos.servicos import (
    ContaRestritaSemQuemVeja,
    UltimoAdmin,
    grupos_sem_outro_admin,
    restritas_de_quem_sai,
)
from apps.solicitacoes.coordenacao import barreira

from .journal import JournalIndisponivel, registrar
from .models import IntencaoExclusao, OperacaoExclusao

_collector_autorizado = ContextVar("exclusao_collector_autorizado", default=False)


@contextmanager
def collector_autorizado():
    token = _collector_autorizado.set(True)
    try:
        yield
    finally:
        _collector_autorizado.reset(token)


def collector_permitido():
    return _collector_autorizado.get()


class ExclusaoIndisponivel(APIException):
    status_code = 503
    default_detail = "Não foi possível concluir a exclusão. Tente novamente."


class IntencaoInvalida(APIException):
    status_code = 409
    default_detail = "A confirmação não está disponível. Inicie uma nova confirmação."


def guardas(usuario):
    grupos = list(grupos_sem_outro_admin(usuario).values_list("nome", flat=True))
    if grupos:
        raise UltimoAdmin(f"Único admin de {', '.join(grupos)}. Promova outra pessoa antes.")
    orfas = restritas_de_quem_sai(usuario)
    if orfas:
        # Do not expose restricted bill details from the deletion endpoint.
        raise ContaRestritaSemQuemVeja([], mensagem=ContaRestritaSemQuemVeja.EXCLUIR)


def validar_intencao(usuario, identificador, segredo, sessao_hash):
    item = (
        IntencaoExclusao.objects.select_for_update()
        .filter(
            pk=identificador,
            usuario=usuario,
            consumida_em__isnull=True,
            expira_em__gt=timezone.now(),
        )
        .first()
    )
    digest = hashlib.sha256(segredo.encode()).hexdigest()
    if (
        not item
        or not hmac.compare_digest(item.segredo_hash, digest)
        or not hmac.compare_digest(item.sessao_hash, sessao_hash)
    ):
        raise IntencaoInvalida()
    return item


def publicar_terminal(operacao_id):
    op = OperacaoExclusao.objects.filter(pk=operacao_id).first()
    if not op or op.estado not in ("commitada", "abortada") or not op.recibo_prepare:
        return
    kind = "COMMIT" if op.estado == "commitada" else "ABORT"
    try:
        receipt = registrar(op.pk, op.owner_id, kind, op.fence, op.recibo_prepare["seq"])
    except (JournalIndisponivel, ValueError):
        return
    OperacaoExclusao.objects.filter(
        pk=op.pk, estado=op.estado, recibo_terminal__isnull=True
    ).update(recibo_terminal=receipt)


def excluir(request, identificador, segredo, sessao_hash):
    from apps.contas_usuario.models import Usuario

    from .views import sem_prova

    if transaction.get_connection().in_atomic_block:
        raise ExclusaoIndisponivel()
    with transaction.atomic():
        barreira()
        usuario = Usuario.objects.filter(pk=request.user.pk, is_active=True).first()
        if not usuario or sem_prova(request, travar=True):
            raise IntencaoInvalida()
        item = validar_intencao(usuario, identificador, segredo, sessao_hash)
        guardas(usuario)
        op = OperacaoExclusao.objects.filter(intencao_id=item.pk, estado="preparada").first()
        if not op:
            op = OperacaoExclusao.objects.create(intencao_id=item.pk, owner_id=usuario.pk)
        if op.estado != "preparada" or op.owner_id != usuario.pk:
            raise IntencaoInvalida()
    try:
        receipt = registrar(op.pk, op.owner_id, "PREPARE", op.fence)
    except (JournalIndisponivel, ValueError):
        raise ExclusaoIndisponivel() from None
    with transaction.atomic():
        operacao = OperacaoExclusao.objects.select_for_update().get(pk=op.pk)
        if operacao.estado != "preparada":
            raise IntencaoInvalida()
        if operacao.recibo_prepare and operacao.recibo_prepare != receipt:
            raise ExclusaoIndisponivel()
        operacao.recibo_prepare = receipt
        operacao.save(update_fields=["recibo_prepare"])
    erro = None
    with transaction.atomic():
        barreira()
        try:
            usuario = Usuario.objects.filter(pk=request.user.pk, is_active=True).first()
            if not usuario or sem_prova(request, travar=True):
                raise IntencaoInvalida()
            item = validar_intencao(usuario, identificador, segredo, sessao_hash)
            guardas(usuario)
        except (UltimoAdmin, ContaRestritaSemQuemVeja, IntencaoInvalida) as exc:
            operacao = OperacaoExclusao.objects.select_for_update().get(pk=op.pk)
            if operacao.estado == "preparada":
                operacao.estado = "abortada"
                operacao.save(update_fields=["estado"])
            erro = exc
        else:
            operacao = OperacaoExclusao.objects.select_for_update().get(pk=op.pk)
            if operacao.estado != "preparada" or operacao.recibo_prepare != receipt:
                raise ExclusaoIndisponivel()
            item.consumida_em = timezone.now()
            item.save(update_fields=["consumida_em"])
            with collector_autorizado():
                usuario.delete()
            operacao.estado = "commitada"
            operacao.save(update_fields=["estado"])
    publicar_terminal(op.pk)
    if erro:
        raise erro


def excluir_privilegiado(usuario, *, elegivel=None):
    """Single privileged ORM deletion; no identity proof is inferred from a UUID."""
    from django.conf import settings

    from apps.contas_usuario.models import Usuario

    # The fake exists solely in test settings, and replaces transport rather than guards.
    fake = bool(getattr(settings, "PRIVACIDADE_JOURNAL_FAKE_TESTE", False) and settings.DEBUG)
    if transaction.get_connection().in_atomic_block and not fake:
        raise ExclusaoIndisponivel()
    with transaction.atomic():
        barreira()
        usuario = Usuario.objects.filter(pk=usuario.pk).first()
        if not usuario:
            return 0, {}
        if elegivel and not elegivel(usuario):
            raise IntencaoInvalida()
        guardas(usuario)
        op = OperacaoExclusao.objects.create(owner_id=usuario.pk)
    try:
        receipt = registrar(op.pk, op.owner_id, "PREPARE", op.fence)
    except (JournalIndisponivel, ValueError):
        raise ExclusaoIndisponivel() from None
    with transaction.atomic():
        locked = OperacaoExclusao.objects.select_for_update().get(pk=op.pk)
        locked.recibo_prepare = receipt
        locked.save(update_fields=["recibo_prepare"])
    erro = None
    resultado = (0, {})
    with transaction.atomic():
        barreira()
        try:
            usuario = Usuario.objects.filter(pk=op.owner_id).first()
            if not usuario or (elegivel and not elegivel(usuario)):
                raise IntencaoInvalida()
            guardas(usuario)
        except (UltimoAdmin, ContaRestritaSemQuemVeja, IntencaoInvalida) as exc:
            op = OperacaoExclusao.objects.select_for_update().get(pk=op.pk)
            if op.estado == "preparada":
                op.estado = "abortada"
                op.save(update_fields=["estado"])
            erro = exc
        else:
            op = OperacaoExclusao.objects.select_for_update().get(pk=op.pk)
            if op.estado != "preparada" or op.recibo_prepare != receipt:
                raise ExclusaoIndisponivel()
            with collector_autorizado():
                resultado = usuario.delete()
            op.estado = "commitada"
            op.save(update_fields=["estado"])
    publicar_terminal(op.pk)
    if erro:
        raise erro
    return resultado
