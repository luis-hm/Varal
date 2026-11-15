"""Central access filter (RN01-RN07, RNF01). Every view that takes a space id starts here.

Nested objects (membro, casa, convite) must then be fetched filtering by the space returned
by `espaco_ou_404`, never by their id alone.
"""

from django.db.models import Case, OuterRef, Subquery, Value, When
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
