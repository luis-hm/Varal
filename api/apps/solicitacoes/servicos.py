"""Solicitation state changes within the coordinated domain transaction."""

from datetime import date

from django.utils import timezone

from apps.boletos.copia import abandonar_copia, liberar_fonte, publicar_copia
from apps.boletos.models import DocumentoBoleto, Instrumento
from apps.espacos.models import Membro, Papel
from apps.lancamentos.models import Acao, Lancamento, Status, Visibilidade
from apps.lancamentos.servicos import _historico

from .models import EstadoSolicitacao, EventoSolicitacao


def encerrar_preparacao(reserva, estado=EstadoSolicitacao.ENCERRADA):
    if reserva.estado != EstadoSolicitacao.PREPARANDO:
        return
    if reserva.tentativa:
        abandonar_copia(reserva.pk, reserva.tentativa)
    liberar_fonte(reserva.pk)
    reserva.estado = estado
    reserva.tentativa = None
    reserva.lease_ate = None
    reserva.save(update_fields=["estado", "tentativa", "lease_ate", "atualizado_em"])


def invalidar_preparacoes(grupo, usuario):
    from django.db.models import Q

    from .models import Solicitacao

    reservas = (
        Solicitacao.objects.select_for_update()
        .filter(grupo=grupo, estado=EstadoSolicitacao.PREPARANDO)
        .filter(Q(solicitante=usuario) | Q(pagador_inicial=usuario))
        .order_by("pk")
    )
    for reserva in reservas:
        if not elegivel(reserva):
            encerrar_preparacao(reserva)


def elegivel(reserva):
    if reserva.estado != EstadoSolicitacao.PREPARANDO:
        return False
    if reserva.origem_id:
        origem = Lancamento.objects.filter(pk=reserva.origem_id).first()
        if not origem or origem.status != Status.PENDENTE:
            return False
        from .views import _snapshot

        atual = _snapshot(origem, "")
        if any(
            atual[campo] != reserva.snapshot[campo]
            for campo in ("valor_centavos", "vencimento", "instrumento", "documento")
        ):
            return False
    if (
        reserva.solicitante_id
        and not Membro.objects.filter(
            espaco_id=reserva.grupo_id,
            usuario_id=reserva.solicitante_id,
            papel__in=[Papel.ADMIN, Papel.MEMBRO],
        ).exists()
    ):
        return False
    return Membro.objects.filter(
        espaco_id=reserva.grupo_id,
        usuario_id=reserva.pagador_inicial_id,
        papel__in=[Papel.ADMIN, Papel.MEMBRO, Papel.PAGADOR],
    ).exists()


def ativar(reserva):
    if not elegivel(reserva):
        encerrar_preparacao(reserva)
        return None
    dados = reserva.snapshot
    copia = Lancamento.objects.create(
        espaco_id=reserva.grupo_id,
        criador_id=reserva.solicitante_id,
        pagador_id=reserva.pagador_inicial_id,
        descricao=dados["descricao"],
        valor_centavos=dados["valor_centavos"],
        vencimento=date.fromisoformat(dados["vencimento"]),
        visibilidade=Visibilidade.RESTRITA,
        status=Status.PENDENTE,
    )
    if instrumento := dados.get("instrumento"):
        Instrumento.objects.create(lancamento=copia, **instrumento)
    if documento := dados.get("documento"):
        documento_id = publicar_copia(reserva.pk, reserva.tentativa)
        DocumentoBoleto.objects.create(
            id=documento_id,
            espaco_id=reserva.grupo_id,
            criado_por_id=reserva.solicitante_id,
            lancamento=copia,
            vinculado_em=timezone.now(),
            estado="conferencia_manual",
            nome=documento["nome"],
            tamanho=documento["tamanho"],
            resultado={},
            avisos=[],
        )
        liberar_fonte(reserva.pk)
    _historico(copia, reserva.solicitante, Acao.CRIADA, {})
    reserva.copia = copia
    reserva.estado = EstadoSolicitacao.ATIVA
    reserva.tentativa = None
    reserva.lease_ate = None
    reserva.save(update_fields=["copia", "estado", "tentativa", "lease_ate", "atualizado_em"])
    EventoSolicitacao.objects.create(
        solicitacao=reserva, destinatario_id=reserva.pagador_inicial_id
    )
    from apps.notificacoes.servicos import agendar_consumo

    agendar_consumo()
    return copia


def vinculo_vivo(conta):
    from django.db.models import Q

    from .models import Solicitacao

    return (
        Solicitacao.objects.select_for_update()
        .filter(Q(origem=conta) | Q(copia=conta), estado__in=["preparando", "ativa", "quitada"])
        .first()
    )


def impedir_alteracao_financeira(conta, dados, pdf, instrumento):
    from apps.boletos.pdf_servicos import metadados_mudaram
    from apps.espacos.servicos import Conflito

    if not vinculo_vivo(conta):
        return
    mudou = any(
        campo in dados and dados[campo] != getattr(conta, campo)
        for campo in ("valor_centavos", "vencimento")
    )
    if mudou or pdf[2] or instrumento.mudou or metadados_mudaram(conta, pdf, instrumento):
        raise Conflito("Encerre a solicitação antes de alterar a cobrança.")


def antes_marcar(conta):
    from apps.espacos.servicos import Conflito
    from apps.lancamentos.servicos import _cancelar

    reserva = vinculo_vivo(conta)
    if not reserva:
        return None
    if reserva.origem_id == conta.pk:
        if reserva.estado == EstadoSolicitacao.PREPARANDO:
            encerrar_preparacao(reserva)
        elif reserva.estado == EstadoSolicitacao.ATIVA:
            copia = Lancamento.objects.select_for_update().filter(pk=reserva.copia_id).first()
            if not copia or copia.status not in (Status.PENDENTE, Status.AGUARDANDO):
                raise Conflito("Solicitação indisponível para esta operação.")
            reserva.estado = EstadoSolicitacao.ENCERRADA
            reserva.save(update_fields=["estado", "atualizado_em"])
            _cancelar(copia, None, dados={"cancelamento_solicitacao": True})
        else:
            raise Conflito("Solicitação indisponível para esta operação.")
        return None
    if reserva.estado != EstadoSolicitacao.ATIVA:
        raise Conflito("Solicitação indisponível para esta operação.")
    origem = (
        Lancamento.objects.select_for_update().filter(pk=reserva.origem_id).first()
        if reserva.origem_id
        else None
    )
    if origem and (
        origem.status != Status.PENDENTE
        or origem.valor_centavos != conta.valor_centavos
        or origem.vencimento != conta.vencimento
    ):
        raise Conflito("Cobrança incompatível com a solicitação.")
    return reserva


def apos_marcar(reserva, pagamento, usuario):
    from apps.pagamentos.models import EventoPagamento, Pagamento

    from .models import ParPagamento

    if not reserva:
        return
    origem = Lancamento.objects.filter(pk=reserva.origem_id).first() if reserva.origem_id else None
    derivada = None
    if origem:
        derivada = Pagamento.objects.create(
            lancamento=origem,
            pago_em=pagamento.pago_em,
            valor_pago_centavos=pagamento.valor_pago_centavos,
            marcado_por=None,
            pagador_id=origem.pagador_id,
        )
        EventoPagamento.objects.create(pagamento=derivada, destinatario_id=origem.criador_id)
        origem.status = Status.PAGA
        origem.versao_pagamento += 1
        origem.save(update_fields=["status", "versao_pagamento", "atualizado_em"])
        _historico(
            origem,
            None,
            Acao.PAGA,
            {
                "pagamento_id": str(derivada.pk),
                "derivado": True,
                "pago_em": derivada.pago_em.isoformat(),
                "valor_centavos": derivada.valor_pago_centavos,
                "comprovante": False,
            },
        )
    ParPagamento.objects.create(solicitacao=reserva, copia=pagamento, derivada=derivada)
    reserva.estado = EstadoSolicitacao.QUITADA
    reserva.save(update_fields=["estado", "atualizado_em"])


def cancelar_relacao(conta):
    from apps.espacos.servicos import Conflito
    from apps.lancamentos.servicos import _cancelar

    reserva = vinculo_vivo(conta)
    if not reserva:
        return
    if reserva.estado == EstadoSolicitacao.PREPARANDO:
        encerrar_preparacao(reserva)
        return
    if reserva.estado != EstadoSolicitacao.ATIVA:
        raise Conflito("Desfaça o pagamento antes de cancelar.")
    reserva.estado = EstadoSolicitacao.ENCERRADA
    reserva.save(update_fields=["estado", "atualizado_em"])
    if reserva.origem_id == conta.pk and reserva.copia_id:
        copia = Lancamento.objects.select_for_update().filter(pk=reserva.copia_id).first()
        if copia and copia.status in (Status.PENDENTE, Status.AGUARDANDO):
            _cancelar(copia, None, dados={"cancelamento_solicitacao": True})
        elif copia:
            raise Conflito("Solicitação indisponível para esta operação.")


def antes_desfazer(conta, pagamento, usuario):
    from apps.espacos.acesso import lancamento_ou_404, membros_ids, quem_ve
    from apps.espacos.servicos import Conflito
    from apps.pagamentos.models import Pagamento
    from apps.pagamentos.servicos import pode_desfazer

    from .models import ParPagamento

    par = ParPagamento.objects.select_for_update().filter(copia=pagamento).first()
    pessoal = False
    if not par:
        par = ParPagamento.objects.select_for_update().filter(derivada=pagamento).first()
        pessoal = bool(par)
    if not par:
        return
    outro_id = par.copia_id if pessoal else par.derivada_id
    if not outro_id:
        if pessoal:
            raise Conflito("Resolva o pedido no grupo.")
        par.solicitacao.estado = EstadoSolicitacao.ATIVA
        par.solicitacao.save(update_fields=["estado", "atualizado_em"])
        return
    outro = (
        Pagamento.objects.select_for_update()
        .select_related("lancamento__espaco")
        .filter(pk=outro_id)
        .first()
    )
    if (
        not outro
        or outro.desfeito_em
        or outro.lancamento.status not in (Status.PAGA, Status.CONFIRMADA)
    ):
        raise Conflito("Pagamento vinculado indisponível.")
    outra_conta = Lancamento.objects.select_for_update().get(pk=outro.lancamento_id)
    if pessoal:
        try:
            visivel = lancamento_ou_404(usuario, outra_conta.pk)
        except Exception:
            raise Conflito("Resolva o pedido no grupo.") from None
        if not pode_desfazer(usuario, visivel, outro):
            raise Conflito("Resolva o pedido no grupo.")
    if outra_conta.pagador_id and outra_conta.pagador_id not in membros_ids(outra_conta.espaco):
        antigo = outra_conta.pagador_id
        outra_conta.pagador = None
        outra_conta.save(update_fields=["pagador", "atualizado_em"])
        _historico(outra_conta, None, Acao.PAGADOR_REMOVIDO, {"pagador": [str(antigo), None]})
    outra_conta.status = Status.PENDENTE
    outra_conta.versao_pagamento += 1
    outra_conta.save(update_fields=["status", "versao_pagamento", "atualizado_em"])
    if outra_conta.visibilidade == Visibilidade.RESTRITA and not quem_ve(outra_conta):
        raise Conflito("A conta ficaria sem ninguém que possa vê-la.")
    outro.desfeito_em = timezone.now()
    outro.desfeito_por = usuario
    outro.save(update_fields=["desfeito_em", "desfeito_por"])
    dados = {"pagamento_id": str(outro.pk)}
    if not pessoal:
        dados["derivado"] = True
    _historico(outra_conta, usuario if pessoal else None, Acao.PAGAMENTO_DESFEITO, dados)
    par.solicitacao.estado = EstadoSolicitacao.ATIVA
    par.solicitacao.save(update_fields=["estado", "atualizado_em"])
