"""Single, current authorization for notification reads and writes."""

from django.db.models import Exists, OuterRef, Q

from apps.espacos.acesso import lancamentos_do_usuario
from apps.espacos.models import Espaco, Membro, Papel
from apps.espacos.servicos import _admins_travados
from apps.lancamentos.models import ABERTOS, Lancamento, Status

from .models import Notificacao, TipoEvento


def autorizadas(usuario):
    visiveis = lancamentos_do_usuario(usuario).filter(pk=OuterRef("evento__lancamento_id"))
    admin = Membro.objects.filter(
        espaco_id=OuterRef("evento__lancamento__espaco_id"), usuario=usuario, papel=Papel.ADMIN
    )
    consulta = Notificacao.objects.filter(destinatario=usuario, revogado_em__isnull=True).annotate(
        _conta_visivel=Exists(visiveis), _admin_atual=Exists(admin)
    )
    conta_aberta = Q(evento__lancamento__status__in=ABERTOS)
    return consulta.filter(
        Q(evento__tipo=TipoEvento.CANCELADA_RN32)
        | (
            Q(_conta_visivel=True)
            & (
                (
                    Q(
                        evento__tipo=TipoEvento.BOLETO_AUSENTE,
                        evento__lancamento__status=Status.AGUARDANDO,
                    )
                    & (
                        Q(evento__lancamento__criador=usuario)
                        | Q(evento__lancamento__pagador=usuario)
                    )
                )
                | (
                    Q(evento__tipo__in=[TipoEvento.VENCE_3, TipoEvento.VENCE_HOJE])
                    & conta_aberta
                    & Q(evento__lancamento__pagador=usuario)
                )
                | (
                    Q(evento__tipo=TipoEvento.VENCEU_1)
                    & conta_aberta
                    & (
                        Q(evento__lancamento__pagador=usuario)
                        | Q(evento__lancamento__criador=usuario)
                        | Q(_admin_atual=True)
                    )
                )
                | (
                    Q(
                        evento__tipo=TipoEvento.PAGAMENTO,
                        evento__pagamento__isnull=False,
                        evento__pagamento__desfeito_em__isnull=True,
                    )
                )
                | (
                    Q(
                        evento__tipo=TipoEvento.PAGADOR_REMOVIDO,
                        evento__lancamento__pagador__isnull=True,
                        _admin_atual=True,
                    )
                    & conta_aberta
                )
            )
        )
    )


def travar_contexto(usuario):
    """Hold current access stable through serialization; caller owns transaction."""
    ids = list(
        Notificacao.objects.filter(destinatario=usuario, revogado_em__isnull=True).values_list(
            "pk", flat=True
        )
    )
    fontes = (
        Notificacao.objects.filter(pk__in=ids)
        .exclude(evento__tipo=TipoEvento.CANCELADA_RN32)
        .filter(evento__lancamento__isnull=False)
    )
    contas = Lancamento.objects.filter(pk__in=fontes.values("evento__lancamento_id"))
    espacos = Espaco.objects.filter(pk__in=contas.values("espaco_id"))
    grupos = list(espacos.filter(tipo=Espaco.Tipo.GRUPO).values_list("pk", flat=True))
    _admins_travados(grupos)
    list(
        Membro.objects.select_for_update(of=("self",))
        .filter(espaco_id__in=grupos, usuario=usuario)
        .order_by("pk")
        .values_list("pk", flat=True)
    )
    list(
        espacos.filter(tipo=Espaco.Tipo.PESSOAL)
        .select_for_update()
        .order_by("pk")
        .values_list("pk", flat=True)
    )
    list(contas.select_for_update().order_by("pk").values_list("pk", flat=True))
    return ids
