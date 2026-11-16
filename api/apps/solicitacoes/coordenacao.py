"""Short domain barrier, acquired before any row lock for cross-space operations."""

from functools import wraps

from django.db import connection


def barreira():
    if not connection.in_atomic_block:
        raise RuntimeError("Domain barrier requires an enclosing transaction")
    with connection.cursor() as cursor:
        # Two-int namespace is separate from the existing single-bigint object locks.
        cursor.execute("SELECT pg_advisory_xact_lock(%s, %s)", [0x56415241, 10])


def coordenado(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        barreira()
        return fn(*args, **kwargs)

    return wrapped


def travar_reserva(pk):
    """Read identities under the barrier, then lock domain rows in the shared order."""
    from apps.espacos.models import Espaco, Membro, Subgrupo
    from apps.espacos.servicos import _admins_travados
    from apps.lancamentos.models import Lancamento
    from apps.recorrencias.models import Recorrencia

    from .models import Solicitacao

    ref = Solicitacao.objects.filter(pk=pk).values("grupo_id", "origem_id", "copia_id").first()
    if not ref:
        return None
    _admins_travados([ref["grupo_id"]])
    list(Membro.objects.select_for_update().filter(espaco_id=ref["grupo_id"]).order_by("pk"))
    ids = [pk for pk in (ref["origem_id"], ref["copia_id"]) if pk]
    contas = Lancamento.objects.filter(pk__in=ids)
    pessoais = contas.filter(espaco__tipo=Espaco.Tipo.PESSOAL).values("espaco_id")
    list(Espaco.objects.select_for_update().filter(pk__in=pessoais).order_by("pk"))
    casas = contas.exclude(subgrupo__isnull=True).values("subgrupo_id")
    list(Subgrupo.objects.select_for_update().filter(pk__in=casas).order_by("pk"))
    modelos = contas.exclude(recorrencia__isnull=True).values("recorrencia_id")
    list(Recorrencia.objects.select_for_update().filter(pk__in=modelos).order_by("pk"))
    list(contas.select_for_update().order_by("pk"))
    return Solicitacao.objects.select_for_update().filter(pk=pk).first()
