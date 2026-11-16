from datetime import datetime, time, timedelta
from uuid import UUID, uuid5

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.boletos.tasks import _travar_objeto, agendar
from apps.espacos.acesso import quem_ve
from apps.espacos.models import Espaco, Membro, Papel, Subgrupo
from apps.lancamentos.models import ABERTOS, Acao, Historico, Lancamento, Status
from apps.pagamentos.models import EventoPagamento, Pagamento
from apps.recorrencias.servicos import travar_espaco
from apps.solicitacoes.coordenacao import barreira

from .acesso import autorizadas
from .models import (
    ControleNotificacoes,
    EntregaNotificacao,
    EntregaPushDispositivo,
    EstadoEntrega,
    EventoNotificacao,
    InscricaoPush,
    Notificacao,
    TipoEvento,
)


def preferencias(usuario):
    dados = usuario.prefs_notificacao if isinstance(usuario.prefs_notificacao, dict) else {}
    return {
        "versao": 1,
        "email": dados.get("email", True) is not False,
        "push": dados.get("push", True) is not False,
    }


def agendar_consumo():
    from .tasks import consumir_eventos

    transaction.on_commit(lambda: agendar(consumir_eventos))


def _evento(chave, tipo, **dados):
    return EventoNotificacao.objects.get_or_create(chave=chave, defaults={"tipo": tipo, **dados})[0]


def travar_preferencias(usuario):
    _travar_objeto(uuid5(usuario.pk, "varal.notificacoes.preferencias"))


def criar_notificacao(evento, usuario):
    from apps.contas_usuario.models import Usuario

    travar_preferencias(usuario)
    usuario = Usuario.objects.get(pk=usuario.pk)
    notificacao, criado = Notificacao.objects.get_or_create(evento=evento, destinatario=usuario)
    if not criado:
        return notificacao
    prefs = preferencias(usuario)
    for canal in ("email", "push"):
        permitido = evento.canais_permitidos and prefs[canal]
        entrega = EntregaNotificacao.objects.create(
            notificacao=notificacao,
            canal=canal,
            estado=EstadoEntrega.PENDENTE if permitido else EstadoEntrega.DESCARTADA,
        )
        if canal == "push" and permitido:
            inscricoes = list(InscricaoPush.objects.filter(usuario=usuario, ativa=True))
            EntregaPushDispositivo.objects.bulk_create(
                [
                    EntregaPushDispositivo(entrega=entrega, inscricao=i, geracao=i.geracao)
                    for i in inscricoes
                ]
            )
            if not inscricoes:
                entrega.estado = EstadoEntrega.DESCARTADA
                entrega.resultado = "sem_inscricao"
                entrega.save(update_fields=["estado", "resultado", "atualizada_em"])
    return notificacao


def _conta_travada_sistema(conta_id):
    ref = Lancamento.objects.select_related("espaco").filter(pk=conta_id).first()
    if not ref:
        return None
    travar_espaco(None, ref.espaco)
    atual = Lancamento.objects.filter(pk=conta_id).values("subgrupo_id").first()
    if not atual:
        return None
    if atual["subgrupo_id"]:
        list(
            Subgrupo.objects.select_for_update()
            .filter(pk=atual["subgrupo_id"])
            .values_list("pk", flat=True)
        )
    return (
        Lancamento.objects.select_for_update(of=("self",))
        .select_related("espaco", "criador", "pagador", "recorrencia")
        .filter(pk=conta_id)
        .first()
    )


def _usuarios_visiveis(conta, ids):
    from apps.contas_usuario.models import Usuario

    visiveis = quem_ve(conta)
    return list(Usuario.objects.filter(pk__in=visiveis.intersection({uid for uid in ids if uid})))


def capturar_historico(historico, conta):
    controle = ControleNotificacoes.objects.filter(pk="ativacao_09").first()
    novo = bool(controle and historico.criado_em >= controle.ativado_em)
    if historico.acao == Acao.CANCELADA_AUTOMATICAMENTE:
        snapshot = {
            "referencia": str(historico.pk),
            "data": timezone.localtime(historico.criado_em).date().isoformat(),
        }
        if novo:
            snapshot["descricao"] = conta.descricao
        evento = _evento(
            f"p7:{historico.pk}",
            TipoEvento.CANCELADA_RN32,
            lancamento=conta,
            historico=historico,
            snapshot_p7=snapshot,
            canais_permitidos=novo,
        )
    elif historico.acao == Acao.PAGADOR_REMOVIDO:
        evento = _evento(
            f"rn21:{historico.pk}",
            TipoEvento.PAGADOR_REMOVIDO,
            lancamento=conta,
            historico=historico,
            canais_permitidos=novo,
        )
    else:
        return
    # The periodic durable scanner avoids variable broker I/O in member removal.
    return evento


def revogar_obsoletas(conta=None, usuario=None, grupo=None):
    from apps.solicitacoes.models import EventoSolicitacao

    fontes = EventoSolicitacao.objects.filter(processado_em__isnull=True)
    if conta is not None:
        fontes = fontes.filter(solicitacao__copia=conta)
    if usuario is not None:
        fontes = fontes.filter(destinatario=usuario)
    if grupo is not None:
        fontes = fontes.filter(solicitacao__grupo=grupo)
    for fonte in fontes.select_related("solicitacao__copia").order_by("pk"):
        reserva = fonte.solicitacao
        copia = reserva.copia
        if not (
            copia
            and copia.status in ABERTOS
            and reserva.estado == "ativa"
            and copia.pagador_id == fonte.destinatario_id
            and Membro.objects.filter(
                espaco_id=reserva.grupo_id,
                usuario_id=fonte.destinatario_id,
                papel__in=[Papel.ADMIN, Papel.MEMBRO, Papel.PAGADOR],
            ).exists()
            and _usuarios_visiveis(copia, [fonte.destinatario_id])
        ):
            fonte.resultado = "inaplicavel"
            fonte.processado_em = timezone.now()
            fonte.save(update_fields=["resultado", "processado_em"])
    base = Notificacao.objects.filter(revogado_em__isnull=True).exclude(
        evento__tipo=TipoEvento.CANCELADA_RN32
    )
    if conta is not None:
        base = base.filter(evento__lancamento=conta)
    if usuario is not None:
        base = base.filter(destinatario=usuario)
    if grupo is not None:
        base = base.filter(evento__lancamento__espaco=grupo)
    for n in base.select_for_update(of=("self",)).select_related("destinatario").order_by("pk"):
        if not autorizadas(n.destinatario).filter(pk=n.pk).exists():
            n.revogado_em = timezone.now()
            n.save(update_fields=["revogado_em"])
            n.entregas.filter(estado__in=[EstadoEntrega.PENDENTE, EstadoEntrega.RESERVADA]).update(
                estado=EstadoEntrega.DESCARTADA, resultado="revogada"
            )
            EntregaPushDispositivo.objects.filter(
                entrega__notificacao=n, estado__in=[EstadoEntrega.PENDENTE, EstadoEntrega.RESERVADA]
            ).update(estado=EstadoEntrega.DESCARTADA, resultado="revogada")


def consumir_pagamento(pk):
    from apps.solicitacoes.models import ParPagamento

    ref = EventoPagamento.objects.filter(pk=pk).values("pagamento__lancamento_id").first()
    if not ref:
        return
    with transaction.atomic():
        barreira()
        conta = _conta_travada_sistema(ref["pagamento__lancamento_id"])
        if not conta:
            return
        fonte = (
            EventoPagamento.objects.select_for_update(of=("self",))
            .select_related("destinatario")
            .filter(pk=pk, processado_em__isnull=True)
            .first()
        )
        if not fonte:
            return
        pagamento = (
            Pagamento.objects.select_for_update()
            .filter(pk=fonte.pagamento_id, lancamento=conta)
            .first()
        )
        par = (
            ParPagamento.objects.filter(Q(copia=pagamento) | Q(derivada=pagamento)).first()
            if pagamento
            else None
        )
        chave = f"pagamento:{fonte.pk}"
        if par and fonte.destinatario_id:
            chave = f"pagamento-par:{par.pk}:{fonte.destinatario_id}"
            if par.derivada_id:
                pessoal = (
                    Pagamento.objects.select_related("lancamento")
                    .filter(pk=par.derivada_id)
                    .first()
                )
                if (
                    pessoal
                    and pessoal.evento.destinatario_id == fonte.destinatario_id
                    and _usuarios_visiveis(pessoal.lancamento, [fonte.destinatario_id])
                ):
                    pagamento = pessoal
                    conta = pessoal.lancamento
        evento = _evento(chave, TipoEvento.PAGAMENTO, lancamento=conta, pagamento=pagamento)
        if not pagamento or pagamento.desfeito_em:
            evento.resultado = "pagamento_desfeito"
        elif not fonte.destinatario_id:
            evento.resultado = "destinatario_ausente"
        else:
            destinatarios = _usuarios_visiveis(conta, [fonte.destinatario_id])
            evento.resultado = "materializado" if destinatarios else "sem_acesso"
            for usuario in destinatarios:
                criar_notificacao(evento, usuario)
        evento.materializado_em = timezone.now()
        evento.save(update_fields=["materializado_em", "resultado"])
        fonte.processado_em = timezone.now()
        fonte.save(update_fields=["processado_em"])


def importar_historico(pk):
    from apps.contas_usuario.models import Usuario

    ref = Historico.objects.filter(pk=pk).values("lancamento_id").first()
    if not ref:
        return
    with transaction.atomic():
        barreira()
        conta = _conta_travada_sistema(ref["lancamento_id"])
        if not conta:
            return
        historico = Historico.objects.filter(pk=pk, lancamento=conta).first()
        if not historico or historico.acao not in (
            Acao.PAGADOR_REMOVIDO,
            Acao.CANCELADA_AUTOMATICAMENTE,
        ):
            return
        tipo = (
            TipoEvento.CANCELADA_RN32
            if historico.acao == Acao.CANCELADA_AUTOMATICAMENTE
            else TipoEvento.PAGADOR_REMOVIDO
        )
        prefixo = "p7" if tipo == TipoEvento.CANCELADA_RN32 else "rn21"
        corte = ControleNotificacoes.objects.get(pk="ativacao_09").ativado_em
        evento = _evento(
            f"{prefixo}:{historico.pk}",
            tipo,
            lancamento=conta,
            historico=historico,
            canais_permitidos=historico.criado_em >= corte,
            snapshot_p7={
                "referencia": str(historico.pk),
                "data": timezone.localtime(historico.criado_em).date().isoformat(),
            }
            if tipo == TipoEvento.CANCELADA_RN32
            else {},
        )
        if evento.materializado_em:
            return
        evento.resultado = "sem_destinatario"
        if tipo == TipoEvento.CANCELADA_RN32:
            try:
                removido = UUID(str(historico.dados.get("removido")))
            except (TypeError, ValueError):
                removido = None
            if removido:
                usuario = Usuario.objects.filter(pk=removido).first()
                if usuario:
                    criar_notificacao(evento, usuario)
                    evento.resultado = "materializado"
        elif conta.status in ABERTOS and not conta.pagador_id:
            admins = Membro.objects.filter(espaco=conta.espaco, papel=Papel.ADMIN).values_list(
                "usuario_id", flat=True
            )
            for usuario in _usuarios_visiveis(conta, set(admins)):
                criar_notificacao(evento, usuario)
                evento.resultado = "materializado"
        else:
            evento.resultado = "conta_resolvida"
        evento.materializado_em = timezone.now()
        evento.save(update_fields=["materializado_em", "resultado"])


def consumir_fontes():
    from apps.solicitacoes.models import EventoSolicitacao

    for pk in (
        EventoSolicitacao.objects.filter(processado_em__isnull=True)
        .values_list("pk", flat=True)
        .iterator()
    ):
        consumir_solicitacao(pk)
    for pk in (
        EventoPagamento.objects.filter(processado_em__isnull=True)
        .values_list("pk", flat=True)
        .iterator()
    ):
        consumir_pagamento(pk)
    # Anti-join makes late commits visible on the next pass, independent of UUID order.
    pendentes = Historico.objects.filter(
        acao__in=[Acao.PAGADOR_REMOVIDO, Acao.CANCELADA_AUTOMATICAMENTE]
    ).exclude(
        pk__in=EventoNotificacao.objects.filter(
            materializado_em__isnull=False, historico__isnull=False
        ).values("historico_id")
    )
    for pk in pendentes.values_list("pk", flat=True).iterator():
        importar_historico(pk)


def consumir_solicitacao(pk):
    from apps.solicitacoes.models import EventoSolicitacao

    with transaction.atomic():
        barreira()
        fonte = (
            EventoSolicitacao.objects.select_for_update()
            .select_related("solicitacao")
            .filter(pk=pk, processado_em__isnull=True)
            .first()
        )
        if not fonte:
            return
        reserva = fonte.solicitacao
        conta = _conta_travada_sistema(reserva.copia_id) if reserva.copia_id else None
        evento = _evento(f"solicitacao:{fonte.pk}", TipoEvento.SOLICITACAO, lancamento=conta)
        elegiveis = (
            _usuarios_visiveis(conta, [fonte.destinatario_id])
            if conta
            and conta.status in ABERTOS
            and reserva.estado == "ativa"
            and conta.pagador_id == fonte.destinatario_id
            and Membro.objects.filter(
                espaco_id=reserva.grupo_id,
                usuario_id=fonte.destinatario_id,
                papel__in=[Papel.ADMIN, Papel.MEMBRO, Papel.PAGADOR],
            ).exists()
            else []
        )
        for usuario in elegiveis:
            criar_notificacao(evento, usuario)
        fonte.resultado = evento.resultado = "materializado" if elegiveis else "inaplicavel"
        fonte.processado_em = evento.materializado_em = timezone.now()
        fonte.save(update_fields=["resultado", "processado_em"])
        evento.save(update_fields=["resultado", "materializado_em"])


def reagendar_lembretes(conta):
    if not conta.vencimento:
        return
    for tipo, dias in (
        (TipoEvento.BOLETO_AUSENTE, 5),
        (TipoEvento.VENCE_3, 3),
        (TipoEvento.VENCE_HOJE, 0),
        (TipoEvento.VENCEU_1, -1),
    ):
        alvo = conta.vencimento - timedelta(days=dias)
        eventos = EventoNotificacao.objects.filter(lancamento=conta, tipo=tipo)
        eventos.update(alvo=alvo)
        inicio = timezone.make_aware(
            datetime.combine(alvo, time(7)), timezone.get_current_timezone()
        )
        EntregaNotificacao.objects.filter(
            notificacao__evento__in=eventos, estado=EstadoEntrega.PENDENTE, proxima_em__gt=inicio
        ).update(proxima_em=inicio)
        EntregaPushDispositivo.objects.filter(
            entrega__notificacao__evento__in=eventos,
            estado=EstadoEntrega.PENDENTE,
            proxima_em__gt=inicio,
        ).update(proxima_em=inicio)


def fase(conta, hoje):
    dias = (conta.vencimento - hoje).days
    if (
        dias == 5 and conta.status == Status.AGUARDANDO and conta.recorrencia_id
        # RN17: an occurrence born awaiting is variable; a later template change must
        # not retroactively change its origin or suppress its reminder.
    ):
        return TipoEvento.BOLETO_AUSENTE
    return {3: TipoEvento.VENCE_3, 0: TipoEvento.VENCE_HOJE, -1: TipoEvento.VENCEU_1}.get(dias)


def varrer_lembretes():
    agora = timezone.localtime()
    if agora.hour < 7:
        return
    hoje = agora.date()
    ids = (
        Lancamento.objects.filter(
            status__in=ABERTOS, vencimento__in=[hoje + timedelta(days=n) for n in (5, 3, 0, -1)]
        )
        .order_by("pk")
        .values_list("pk", flat=True)
    )
    for conta_id in ids.iterator():
        with transaction.atomic():
            barreira()
            conta = _conta_travada_sistema(conta_id)
            if not conta or conta.status not in ABERTOS:
                continue
            tipo = fase(conta, hoje)
            if not tipo:
                continue
            ids_pessoas = set()
            if tipo in (TipoEvento.BOLETO_AUSENTE, TipoEvento.VENCEU_1):
                ids_pessoas.add(conta.criador_id)
            ids_pessoas.add(conta.pagador_id)
            if tipo == TipoEvento.VENCEU_1 and conta.espaco.tipo == Espaco.Tipo.GRUPO:
                ids_pessoas.update(
                    Membro.objects.filter(espaco=conta.espaco, papel=Papel.ADMIN).values_list(
                        "usuario_id", flat=True
                    )
                )
            evento = _evento(f"fase:{conta.pk}:{tipo}", tipo, lancamento=conta, alvo=hoje)
            if evento.alvo != hoje:
                evento.alvo = hoje
                evento.save(update_fields=["alvo"])
            for usuario in _usuarios_visiveis(conta, ids_pessoas):
                criar_notificacao(evento, usuario)
