"""Central access filter (RN01-RN07, RNF01). Every view that takes a space id starts here.

Nested objects (membro, casa, convite) must then be fetched filtering by the space returned
by `espaco_ou_404`, never by their id alone.
"""

from django.db.models import Case, Exists, OuterRef, Q, Subquery, Value, When
from rest_framework.exceptions import NotFound, PermissionDenied

from .models import Espaco, Membro, Papel

ACOES = frozenset(
    {
        "ver_grupo",
        "criar_conta",
        "editar_conta",
        "pagar_qualquer",
        "pagar_propria",
        "gerenciar_grupo",
    }
)
DONO = "dono"
PERMISSOES = {
    DONO: ACOES,
    Papel.ADMIN: ACOES,
    Papel.MEMBRO: ACOES - {"gerenciar_grupo"},
    Papel.OBSERVADOR: frozenset({"ver_grupo"}),
    # Decision 6: the payer never sees the group page, only the bills they pay (RN07).
    Papel.PAGADOR: frozenset({"pagar_propria"}),
}


def espacos_do_usuario(usuario):
    """The user's personal space plus the groups they belong to, annotated with `meu_papel`."""
    papel_no_grupo = Membro.objects.filter(espaco=OuterRef("pk"), usuario=usuario).values("papel")
    return Espaco.objects.annotate(
        meu_papel=Case(
            When(tipo=Espaco.Tipo.PESSOAL, dono=usuario, then=Value(DONO)),
            When(tipo=Espaco.Tipo.GRUPO, then=Subquery(papel_no_grupo[:1])),
        )
    ).filter(meu_papel__isnull=False)


def papel(usuario, espaco):
    """Return "dono" in their own personal space, the role in a group, or None."""
    return (
        espacos_do_usuario(usuario).filter(pk=espaco.pk).values_list("meu_papel", flat=True).first()
    )


def pode(papel_, acao):
    return acao in PERMISSOES.get(papel_, ())


def espaco_ou_404(usuario, espaco_id, acao=None, tipo=None):
    """404 when the user does not take part (existence is never revealed); 403 when the role
    lacks `acao`. `acao=None` only requires taking part (e.g. leaving the group)."""
    espacos = espacos_do_usuario(usuario)
    if tipo:
        espacos = espacos.filter(tipo=tipo)
    espaco = espacos.filter(pk=espaco_id).first()
    if espaco is None:
        raise NotFound()
    if acao and not pode(espaco.meu_papel, acao):
        raise PermissionDenied()
    return espaco


# ---- bills (lancamentos): the single definition of "who sees" ------------------------------


def _ve(usuario, papel_):
    """Q over Lancamento for what a user with `papel_` sees inside one space (RN02/RN06/RN07).
    The admin gets no exception (Q6). Explicit access beats RN07 for restricted bills
    (ADR 0008). None = sees nothing."""
    from apps.lancamentos.models import Lancamento, Visibilidade

    escolhido = Exists(
        Lancamento.acesso.through.objects.filter(lancamento=OuterRef("pk"), usuario=usuario)
    )
    if papel_ == DONO:
        return Q()
    if papel_ == Papel.PAGADOR:
        return Q(pagador=usuario) | (Q(visibilidade=Visibilidade.RESTRITA) & Q(escolhido))
    if papel_ in (Papel.ADMIN, Papel.MEMBRO, Papel.OBSERVADOR):
        return (
            Q(visibilidade=Visibilidade.GRUPO)
            | Q(criador=usuario)
            | Q(pagador=usuario)
            | Q(escolhido)
        )
    return None


def lancamentos_visiveis(usuario, espaco):
    """Every bill query (lists, totals, counts, filter options, detail) starts here. Annotated
    with `status_exibido` (RN12) using the space's window and today in Fortaleza."""
    from apps.lancamentos.models import Lancamento

    # Always re-read the role: `espaco.meu_papel` may belong to someone else (e.g. the admin
    # removing `usuario`).
    filtro = _ve(usuario, papel(usuario, espaco))
    contas = Lancamento.objects.filter(espaco=espaco).com_status(espaco.janela_alerta_dias)
    return contas.none() if filtro is None else contas.filter(filtro)


def lancamentos_do_usuario(usuario):
    """Visible bills across spaces, using the same role rules as the per-space filter.

    The role is read inside the bill query: a missing id and an inaccessible bill take the
    same query path. This also scopes the operator admin; superusers get no RN06 exception.
    """
    from apps.lancamentos.models import Lancamento

    espacos = espacos_do_usuario(usuario).filter(pk=OuterRef("espaco_id"))
    contas = Lancamento.objects.annotate(
        meu_papel=Subquery(espacos.values("meu_papel")[:1]),
    )
    return contas.filter(
        Q(meu_papel=DONO)
        | (Q(meu_papel=Papel.PAGADOR) & _ve(usuario, Papel.PAGADOR))
        | (
            Q(meu_papel__in=(Papel.ADMIN, Papel.MEMBRO, Papel.OBSERVADOR))
            & _ve(usuario, Papel.MEMBRO)
        )
    )


def lancamento_ou_404(usuario, lancamento_id, acao=None, travar=False):
    """404 whenever the user does not see the bill (missing, other space, restricted): its
    existence is never revealed. 403 only when they see it and the role lacks `acao`.
    `travar` locks the row first (needs a transaction), then checks with a fresh query."""
    from apps.lancamentos.models import Lancamento

    if travar:
        list(Lancamento.objects.select_for_update().filter(pk=lancamento_id).values("pk"))
    conta = (
        lancamentos_do_usuario(usuario).select_related("espaco").filter(pk=lancamento_id).first()
    )
    if not conta:
        raise NotFound()
    espaco = conta.espaco
    espaco.meu_papel = conta.meu_papel
    if acao and not pode(espaco.meu_papel, acao):
        raise PermissionDenied()
    conta.espaco = espaco  # keeps `meu_papel` for the caller
    return conta


def membros_ids(espaco):
    """User ids of the space's current members (personal space: only the owner). One query."""
    if espaco.tipo == Espaco.Tipo.PESSOAL:
        return {espaco.dono_id}
    return set(Membro.objects.filter(espaco=espaco).values_list("usuario_id", flat=True))


def quem_ve(conta, sem=None):
    """Ids of the users who see `conta`, by the same rule as `lancamentos_visiveis`, leaving out
    `sem` (someone leaving: with RN21 they stop counting as payer and as chosen). Base of RN32."""
    from apps.lancamentos.models import Lancamento

    espaco = conta.espaco
    if espaco.tipo == Espaco.Tipo.PESSOAL:
        pessoas = [(espaco.dono_id, DONO)]
    else:
        pessoas = Membro.objects.filter(espaco=espaco).values_list("usuario_id", "papel")
    so_ela = Lancamento.objects.filter(pk=conta.pk)
    # ponytail: one EXISTS per member keeps a single definition of "who sees"; groups are small.
    return {
        usuario_id
        for usuario_id, papel_ in pessoas
        if (sem is None or usuario_id != sem.pk)
        and (filtro := _ve(usuario_id, papel_)) is not None
        and so_ela.filter(filtro).exists()
    }
