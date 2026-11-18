"""Account deletion (RN30) in one transaction, plus a record kept outside the database.

The record (owner UUID and date only) goes to object storage after the commit. A database
restored from an older dump re-applies the deletions made after it with
`manage.py reaplicar_exclusoes` (ADR 0018).
"""

import hashlib
import hmac
import json
from contextlib import contextmanager
from contextvars import ContextVar

from django.conf import settings
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

from .models import IntencaoExclusao, OperacaoExclusao

PREFIXO = "exclusoes/"

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


def registro(op):
    """Write the deletion record; the caller marks it published."""
    from apps.boletos.storage import cliente

    corpo = {"owner_id": str(op.owner_id), "excluida_em": op.criado_em.isoformat()}
    cliente().put_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=f"{PREFIXO}{op.pk}.json",
        Body=json.dumps(corpo).encode(),
        ContentType="application/json",
    )


def _apagar(usuario, intencao_id=None):
    from .tasks import publicar_exclusoes

    OperacaoExclusao.objects.create(owner_id=usuario.pk, intencao_id=intencao_id)
    with collector_autorizado():
        resultado = usuario.delete()
    transaction.on_commit(publicar_exclusoes.delay)
    return resultado


def excluir(request, identificador, segredo, sessao_hash):
    from apps.contas_usuario.models import Usuario

    from .views import sem_prova

    with transaction.atomic():
        barreira()
        usuario = Usuario.objects.filter(pk=request.user.pk, is_active=True).first()
        if not usuario or sem_prova(request, travar=True):
            raise IntencaoInvalida()
        item = validar_intencao(usuario, identificador, segredo, sessao_hash)
        guardas(usuario)
        item.consumida_em = timezone.now()
        item.save(update_fields=["consumida_em"])
        _apagar(usuario, intencao_id=item.pk)


def excluir_privilegiado(usuario, *, elegivel=None):
    """Single privileged ORM deletion; no identity proof is inferred from a UUID."""
    from apps.contas_usuario.models import Usuario

    with transaction.atomic():
        barreira()
        usuario = Usuario.objects.filter(pk=usuario.pk).first()
        if not usuario:
            return 0, {}
        if elegivel and not elegivel(usuario):
            raise IntencaoInvalida()
        guardas(usuario)
        return _apagar(usuario)
