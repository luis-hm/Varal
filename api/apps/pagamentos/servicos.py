from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.espacos.acesso import DONO, lancamento_ou_404, membros_ids, pode, pode_na, quem_ve
from apps.espacos.models import Espaco, Membro, Papel, Subgrupo
from apps.espacos.servicos import Conflito, _admins_travados
from apps.lancamentos.models import Acao, Status, Visibilidade
from apps.lancamentos.servicos import _historico
from apps.solicitacoes.coordenacao import barreira

from .models import DocumentoComprovante, EventoPagamento, Pagamento


def pode_pagar(usuario, conta):
    papel = conta.espaco.meu_papel
    return pode_na(usuario, papel, conta.subgrupo_id, "pagar_qualquer") or (
        pode(papel, "pagar_propria") and conta.pagador_id == usuario.pk
    )


def pode_desfazer(usuario, conta, pagamento):
    return pagamento is not None and (
        pagamento.marcado_por_id == usuario.pk or conta.espaco.meu_papel in (DONO, Papel.ADMIN)
    )


def pode_anexar(usuario, conta, pagamento):
    from apps.solicitacoes.models import ParPagamento

    return bool(
        pagamento
        and pode_pagar(usuario, conta)
        and pode_desfazer(usuario, conta, pagamento)
        and not ParPagamento.objects.filter(derivada=pagamento).exists()
        and not DocumentoComprovante.objects.filter(pagamento=pagamento).exists()
    )


def conta_travada(usuario, conta_id, casas_extra=()):
    inicial = lancamento_ou_404(usuario, conta_id)
    espaco = inicial.espaco
    if espaco.tipo == Espaco.Tipo.GRUPO:
        _admins_travados([espaco.pk])
        list(
            Membro.objects.select_for_update(of=("self",))
            .filter(espaco=espaco, usuario=usuario)
            .values_list("pk", flat=True)
        )
    else:
        list(Espaco.objects.select_for_update().filter(pk=espaco.pk).values_list("pk", flat=True))
    inicial = lancamento_ou_404(usuario, conta_id)
    casas = {pk for pk in (*casas_extra, inicial.subgrupo_id) if pk}
    list(
        Subgrupo.objects.select_for_update()
        .filter(espaco=espaco, pk__in=casas)
        .order_by("pk")
        .values_list("pk", flat=True)
    )
    return lancamento_ou_404(usuario, conta_id, travar=True)


def exigir_pagar(usuario, conta):
    if not pode_pagar(usuario, conta):
        raise PermissionDenied()


def draft(usuario, conta, documento_id, pagamento=None):
    doc = (
        DocumentoComprovante.objects.select_for_update()
        .filter(pk=documento_id, lancamento=conta)
        .first()
    )
    if not doc or doc.criado_por_id != usuario.pk:
        raise NotFound()
    if (
        doc.vinculado_em
        or doc.estado != "valido"
        or doc.criado_em <= timezone.now() - timedelta(hours=24)
        or doc.versao != conta.versao_pagamento
        or doc.pagamento_alvo_id != (pagamento.pk if pagamento else None)
    ):
        raise Conflito("Comprovante indisponível para esta operação.")
    return doc


def vincular(doc, pagamento):
    doc.pagamento = pagamento
    doc.vinculado_em = timezone.now()
    doc.save(update_fields=["pagamento", "vinculado_em"])


def marcar(usuario, conta_id, dados):
    with transaction.atomic():
        barreira()
        conta = conta_travada(usuario, conta_id)
        exigir_pagar(usuario, conta)
        if conta.status != Status.PENDENTE:
            raise Conflito("Só contas pendentes podem ser marcadas.")
        if dados["pago_em"] > timezone.localdate():
            raise ValidationError({"pago_em": ["A data não pode ser futura."]})
        if dados["valor_centavos_esperado"] != conta.valor_centavos:
            raise Conflito("O valor da conta foi alterado.")
        doc = (
            draft(usuario, conta, dados["comprovante_id"]) if dados.get("comprovante_id") else None
        )
        from apps.solicitacoes.servicos import antes_marcar, apos_marcar

        reserva = antes_marcar(conta)
        pagamento = Pagamento.objects.create(
            lancamento=conta,
            pago_em=dados["pago_em"],
            valor_pago_centavos=conta.valor_centavos,
            marcado_por=usuario,
            pagador_id=conta.pagador_id,
        )
        EventoPagamento.objects.create(pagamento=pagamento, destinatario_id=conta.criador_id)
        apos_marcar(reserva, pagamento, usuario)
        if doc:
            vincular(doc, pagamento)
        conta.status = Status.CONFIRMADA if doc else Status.PAGA
        conta.versao_pagamento += 1
        conta.save(update_fields=["status", "versao_pagamento", "atualizado_em"])
        _historico(
            conta,
            usuario,
            Acao.PAGA,
            {
                "pagamento_id": str(pagamento.pk),
                "pago_em": pagamento.pago_em.isoformat(),
                "valor_centavos": pagamento.valor_pago_centavos,
                "comprovante": bool(doc),
            },
        )
        return conta, pagamento


def pagamento_alvo(conta, pagamento_id):
    pagamento = (
        Pagamento.objects.select_for_update().filter(pk=pagamento_id, lancamento=conta).first()
    )
    if not pagamento:
        raise NotFound()
    return pagamento


def anexar(usuario, conta_id, pagamento_id, documento_id):
    with transaction.atomic():
        barreira()
        conta = conta_travada(usuario, conta_id)
        exigir_pagar(usuario, conta)
        pagamento = pagamento_alvo(conta, pagamento_id)
        from apps.solicitacoes.models import ParPagamento

        if ParPagamento.objects.filter(derivada=pagamento).exists():
            raise Conflito("Comprovante deve ser registrado no grupo.")
        if not pode_desfazer(usuario, conta, pagamento):
            raise PermissionDenied()
        if (
            pagamento.desfeito_em
            or conta.status != Status.PAGA
            or DocumentoComprovante.objects.filter(pagamento=pagamento).exists()
        ):
            raise Conflito("Pagamento não aceita comprovante.")
        doc = draft(usuario, conta, documento_id, pagamento)
        vincular(doc, pagamento)
        conta.status = Status.CONFIRMADA
        conta.save(update_fields=["status", "atualizado_em"])
        _historico(conta, usuario, Acao.COMPROVANTE_ANEXADO, {"pagamento_id": str(pagamento.pk)})
        return conta


def desfazer(usuario, conta_id, pagamento_id):
    with transaction.atomic():
        barreira()
        conta = conta_travada(usuario, conta_id)
        pagamento = pagamento_alvo(conta, pagamento_id)
        if not pode_desfazer(usuario, conta, pagamento):
            raise PermissionDenied()
        if pagamento.desfeito_em or conta.status not in (Status.PAGA, Status.CONFIRMADA):
            raise Conflito("Pagamento já desfeito.")
        from apps.solicitacoes.servicos import antes_desfazer

        antes_desfazer(conta, pagamento, usuario)
        if conta.pagador_id and conta.pagador_id not in membros_ids(conta.espaco):
            antigo = conta.pagador_id
            conta.pagador = None
            conta.save(update_fields=["pagador", "atualizado_em"])
            _historico(conta, None, Acao.PAGADOR_REMOVIDO, {"pagador": [str(antigo), None]})
        conta.status = Status.PENDENTE
        conta.versao_pagamento += 1
        conta.save(update_fields=["status", "versao_pagamento", "atualizado_em"])
        if conta.visibilidade == Visibilidade.RESTRITA and not quem_ve(conta):
            raise Conflito("A conta ficaria sem ninguém que possa vê-la.")
        pagamento.desfeito_em = timezone.now()
        pagamento.desfeito_por = usuario
        pagamento.save(update_fields=["desfeito_em", "desfeito_por"])
        _historico(conta, usuario, Acao.PAGAMENTO_DESFEITO, {"pagamento_id": str(pagamento.pk)})
        return conta


def documento_ou_404(usuario, documento_id):
    ref = DocumentoComprovante.objects.filter(pk=documento_id).values("lancamento_id").first()
    if not ref:
        raise NotFound()
    conta = conta_travada(usuario, ref["lancamento_id"])
    doc = (
        DocumentoComprovante.objects.select_for_update()
        .filter(pk=documento_id, lancamento=conta)
        .first()
    )
    if not doc:
        raise NotFound()
    if not doc.vinculado_em:
        if doc.criado_por_id != usuario.pk:
            raise NotFound()
        exigir_pagar(usuario, conta)
        if (
            doc.criado_em <= timezone.now() - timedelta(hours=24)
            or doc.versao != conta.versao_pagamento
        ):
            raise NotFound()
        if doc.pagamento_alvo_id:
            pagamento = pagamento_alvo(conta, doc.pagamento_alvo_id)
            if (
                pagamento.desfeito_em
                or conta.status != Status.PAGA
                or not pode_anexar(usuario, conta, pagamento)
            ):
                raise NotFound()
        elif conta.status != Status.PENDENTE:
            raise NotFound()
    return doc
