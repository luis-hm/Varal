"""Bill (lancamento) domain operations. Every write runs in a transaction and leaves a history
row (RN22); nothing is ever deleted."""

from django.db import transaction
from django.db.models import Exists, OuterRef
from rest_framework.exceptions import ValidationError

from apps.boletos import pdf_servicos
from apps.boletos import servicos as instrumentos
from apps.espacos.acesso import espaco_ou_404, lancamento_ou_404, lancamentos_visiveis, quem_ve
from apps.espacos.models import Espaco, Membro, Papel, Subgrupo
from apps.espacos.servicos import Conflito, _admins_travados

from .models import ABERTOS, Acao, Historico, Lancamento, Status, Visibilidade

PODEM_PAGAR = (Papel.ADMIN, Papel.MEMBRO, Papel.PAGADOR)  # Q16
PODEM_VER_ESCOLHIDOS = (Papel.ADMIN, Papel.MEMBRO, Papel.OBSERVADOR)  # decision 7 (RN07)
SO_VOCE_VE = "Você é a única pessoa que vê esta conta. Escolha outra pessoa antes de sair da lista."
CAMPOS = ["descricao", "valor_centavos", "vencimento", "subgrupo_id", "pagador_id", "visibilidade"]


SEM_NOME, EX_MEMBRO = "Pessoa sem nome", "Ex-membro"


def rotulo(usuario, membros, historico=False):
    """How a person is shown, by context (decision 23). `membros`: user ids of the bill's space
    (`acesso.membros_ids`). Deleted or no longer a member: "Ex-membro", never the e-mail (RN30).
    A current member: the name; without one, the e-mail in live data (as in the member list)
    and "Pessoa sem nome" in the history, which never shows an e-mail."""
    if usuario is None or usuario.pk not in membros:
        return EX_MEMBRO
    return usuario.nome or (SEM_NOME if historico else usuario.email)


def _ids(usuario_ids):
    return sorted(str(pk) for pk in usuario_ids)


def _membros(espaco, ids, papeis):
    return set(
        Membro.objects.filter(espaco=espaco, usuario_id__in=ids, papel__in=papeis).values_list(
            "usuario_id", flat=True
        )
    )


def validar(espaco, dados, conta=None):
    """Returns model-ready values (`subgrupo_id`, `pagador_id`, `acesso` as a set of ids).
    Houses, payers and chosen people are only checked when they change (Q20, ADR 0008)."""
    dados = dict(dados)
    if espaco.tipo == Espaco.Tipo.PESSOAL:  # decision 6: owner pays, everyone (= owner) sees
        dados.update(subgrupo=None, pagador=espaco.dono_id, visibilidade=Visibilidade.GRUPO)
        dados["acesso"] = []
    erros = {}
    if "subgrupo" in dados:
        casa_id = dados.pop("subgrupo")
        if casa_id is not None and (conta is None or conta.subgrupo_id != casa_id):
            if not Subgrupo.objects.filter(espaco=espaco, pk=casa_id, arquivado=False).exists():
                erros["subgrupo"] = ["Escolha uma casa ativa deste grupo."]
        dados["subgrupo_id"] = casa_id
    if "pagador" in dados:
        pagador_id = dados.pop("pagador")
        mudou = conta is None or conta.pagador_id != pagador_id
        if pagador_id is not None and mudou and espaco.tipo == Espaco.Tipo.GRUPO:
            if not _membros(espaco, [pagador_id], PODEM_PAGAR):
                erros["pagador"] = ["Quem paga precisa ser admin, membro ou pagador deste grupo."]
        dados["pagador_id"] = pagador_id
    visibilidade = dados.get("visibilidade", conta.visibilidade if conta else Visibilidade.GRUPO)
    if visibilidade == Visibilidade.GRUPO:
        dados["acesso"] = set()
    elif "acesso" in dados:
        escolhidos = set(dados["acesso"])
        atuais = set(conta.acesso.values_list("pk", flat=True)) if conta else set()
        novos = escolhidos - atuais
        if novos - _membros(espaco, novos, PODEM_VER_ESCOLHIDOS):
            erros["acesso"] = ["Só admin, membro ou observador deste grupo podem ver a conta."]
        dados["acesso"] = escolhidos
    if erros:
        raise ValidationError(erros)
    return dados


def resolver_pessoas(historicos, membros):
    """RN22/RN30: `dados` stores user ids, never names or e-mails (LGPD), so nothing about a
    person outlives their account. Sets `dados_exibidos` with labels resolved now against the
    space's current `membros`, in one query; the stored `dados` is left untouched."""
    from apps.contas_usuario.models import Usuario

    ids = set()
    for h in historicos:
        ids.update(i for i in h.dados.get("pagador", ()) if i)
        ids.update(i for lado in h.dados.get("acesso", ()) for i in lado)
        if h.dados.get("pessoa"):
            ids.add(h.dados["pessoa"])
    nomes = {
        str(u.pk): rotulo(u, membros, historico=True) for u in Usuario.objects.filter(pk__in=ids)
    }

    def nome(i):
        return None if i is None else nomes.get(i, EX_MEMBRO)

    for h in historicos:
        dados = dict(h.dados)
        if "pagador" in dados:
            dados["pagador"] = [nome(i) for i in dados["pagador"]]
        if "acesso" in dados:
            dados["acesso"] = [sorted(nome(i) for i in lado) for lado in dados["acesso"]]
        if "pessoa" in dados:
            dados["pessoa"] = nome(dados["pessoa"])
        h.dados_exibidos = dados


def _historico(conta, usuario, acao, dados=None):
    Historico.objects.create(lancamento=conta, usuario=usuario, acao=acao, dados=dados or {})


def criar(usuario, espaco, dados):
    with transaction.atomic():
        # The view's authorization may predate a departure, removal or role change. Freeze
        # membership mutations in the same admins -> member order, then re-read permission.
        # All candidate payers/chosen users are validated while this group's admins are held.
        if espaco.tipo == Espaco.Tipo.GRUPO:
            _admins_travados([espaco.pk])
            list(
                Membro.objects.select_for_update(of=("self",))
                .filter(espaco=espaco, usuario=usuario)
                .values_list("pk", flat=True)
            )
        else:
            list(Espaco.objects.select_for_update().filter(pk=espaco.pk).values("pk"))
        espaco = espaco_ou_404(usuario, espaco.pk, "criar_conta")
        dados = dict(dados)
        pdf = pdf_servicos.preparar_pdf(usuario, espaco, dados)
        instrumento = instrumentos.preparar(dados)
        dados = validar(espaco, dados)
        acesso = dados.pop("acesso", set())
        conta = Lancamento.objects.create(espaco=espaco, criador=usuario, **dados)
        conta.acesso.set(acesso)
        instrumentos.aplicar(conta, instrumento)
        mudancas_pdf = pdf_servicos.aplicar_pdf(conta, pdf, instrumento)
        _historico(conta, usuario, Acao.CRIADA, {**instrumento.historico, **mudancas_pdf})
    return conta


def _legivel(campo, valor):
    if valor is None:
        return None
    if campo == "subgrupo_id":
        return Subgrupo.objects.get(pk=valor).nome
    if campo == "pagador_id":
        return str(valor)  # user ids only (LGPD); names are resolved on read
    if campo == "vencimento":
        return valor.isoformat()
    return valor


def editar(usuario, conta_id, dados):
    with transaction.atomic():
        conta = lancamento_ou_404(usuario, conta_id, "editar_conta", travar=True)
        if conta.status == Status.CANCELADA:
            raise Conflito("Conta cancelada não pode ser editada.")
        dados = dict(dados)
        pdf = pdf_servicos.preparar_pdf(usuario, conta.espaco, dados, conta)
        instrumento = instrumentos.preparar(dados, conta)
        dados = validar(conta.espaco, dados, conta)
        mudancas = instrumento.historico
        if pdf[2]:
            mudancas["pdf_alterado"] = True
        elif pdf_servicos.metadados_mudaram(conta, pdf, instrumento):
            mudancas["metadados_pdf_alterados"] = True
        for campo in CAMPOS:
            if campo in dados and getattr(conta, campo) != dados[campo]:
                chave = campo.removesuffix("_id")
                mudancas[chave] = [
                    _legivel(campo, getattr(conta, campo)),
                    _legivel(campo, dados[campo]),
                ]
                setattr(conta, campo, dados[campo])
        if "acesso" in dados:
            antes = set(conta.acesso.values_list("pk", flat=True))
            if antes != dados["acesso"]:
                mudancas["acesso"] = [_ids(antes), _ids(dados["acesso"])]
                conta.acesso.set(dados["acesso"])
        if conta.status == Status.AGUARDANDO and instrumento.dados is not None:
            mudancas["status"] = [Status.AGUARDANDO, Status.PENDENTE]
            conta.status = Status.PENDENTE
        if not mudancas:
            return conta
        conta.save()
        # Q19b / RN32: an edit never leaves an open restricted bill without anyone who sees it.
        abertas_restrita = conta.status in ABERTOS and conta.visibilidade == Visibilidade.RESTRITA
        if abertas_restrita and not quem_ve(conta):
            raise ValidationError({"acesso": [SO_VOCE_VE]})
        instrumentos.aplicar(conta, instrumento)
        pdf_servicos.aplicar_pdf(conta, pdf, instrumento)
        _historico(conta, usuario, Acao.EDITADA, mudancas)
    return conta


def _cancelar(conta, usuario, acao=Acao.CANCELADA, dados=None):
    conta.status = Status.CANCELADA
    conta.save(update_fields=["status", "atualizado_em"])
    _historico(conta, usuario, acao, dados)


def cancelar(usuario, conta_id):
    with transaction.atomic():
        conta = lancamento_ou_404(usuario, conta_id, "editar_conta", travar=True)
        if conta.status not in ABERTOS:
            raise Conflito("Só conta aguardando boleto ou pendente pode ser cancelada.")
        _cancelar(conta, usuario)
    return conta


# ---- RN21 / RN32 / ADR 0007 / ADR 0008 (called from espacos.servicos) ----------------------


def _escolhido(usuario):
    return Exists(
        Lancamento.acesso.through.objects.filter(lancamento=OuterRef("pk"), usuario=usuario)
    )


def travar_abertas(grupo):
    """RN32: lock every open bill by pk, including those still public in this snapshot: an edit
    may be making one restricted. The fresh orphan query sees that edit after acquiring its
    lock. Callers lock admins -> member before this; `editar` locks only the bill."""
    list(
        Lancamento.objects.select_for_update()
        .filter(espaco=grupo, status__in=ABERTOS)
        .order_by("pk")
        .values_list("pk", flat=True)
    )


def restritas_sem_quem_veja(grupo, usuario, travar=True):
    """RN32: open restricted bills `usuario` sees now that nobody would see without them (RN21
    applied). Locked by pk (fixed order) when `travar`; needs a transaction then."""
    if travar:
        travar_abertas(grupo)
    contas = lancamentos_visiveis(usuario, grupo).filter(
        visibilidade=Visibilidade.RESTRITA, status__in=ABERTOS
    )
    if travar:
        contas = contas.select_for_update()
    orfas = []
    for conta in contas.order_by("pk"):
        conta.espaco = grupo
        if not quem_ve(conta, sem=usuario):
            orfas.append(conta)
    return orfas


def pessoas_para_escolher(grupo, sem):
    membros = (
        Membro.objects.filter(espaco=grupo, papel__in=PODEM_VER_ESCOLHIDOS)
        .exclude(usuario=sem)
        .select_related("usuario")
        .order_by("usuario__nome", "usuario__email")
    )
    # Live data (decision 23): current members only, so the name or, without one, the e-mail.
    return [{"id": m.usuario_id, "nome": rotulo(m.usuario, {m.usuario_id})} for m in membros]


def resolver_na_saida(usuario, grupo, resolucoes, orfas):
    """ADR 0007: the only exception to RN05. Runs inside the leaving transaction; only for the
    bills that block this exit; always in the history with the reason `saida_rn32`."""
    pendentes = {conta.pk: conta for conta in orfas}
    for resolucao in resolucoes:
        conta = pendentes.pop(resolucao["lancamento"], None)
        if conta is None:
            raise ValidationError({"resolucoes": ["Esta conta não impede a sua saída do grupo."]})
        if resolucao["acao"] == "cancelar":
            _cancelar(conta, usuario, dados={"motivo": "saida_rn32"})
            continue
        novos = set(resolucao["usuarios"]) - {usuario.pk}
        if not novos or novos - _membros(grupo, novos, PODEM_VER_ESCOLHIDOS):
            raise ValidationError(
                {
                    "resolucoes": [
                        "Escolha admin, membro ou observador deste grupo para ver a conta."
                    ]
                }
            )
        antes = set(conta.acesso.values_list("pk", flat=True))
        conta.acesso.add(*novos)
        dados = {"acesso": [_ids(antes), _ids(antes | novos)], "motivo": "saida_rn32"}
        _historico(conta, usuario, Acao.EDITADA, dados)


def cancelar_orfas(usuario, orfas):
    """RN32, removal by an admin: never blocks, never tells the admin. No author (automatic);
    `removido` feeds the Etapa 09 notice to the removed person."""
    for conta in orfas:
        dados = {"motivo": "sem_quem_veja", "removido": str(usuario.pk)}
        _cancelar(conta, None, Acao.CANCELADA_AUTOMATICAMENTE, dados)


def desligar_das_contas(usuario, grupo):
    """RN21: open bills lose the payer (paid and cancelled keep it, Q7); the person leaves every
    "Quem vê" list of the group. Bills they created stay in the group."""
    abertas = Lancamento.objects.filter(espaco=grupo, pagador=usuario, status__in=ABERTOS)
    for conta in abertas.select_for_update().order_by("pk"):
        conta.pagador = None
        conta.save(update_fields=["pagador", "atualizado_em"])
        _historico(conta, None, Acao.PAGADOR_REMOVIDO, {"pagador": [str(usuario.pk), None]})
    acessos = Lancamento.acesso.through.objects.filter(lancamento__espaco=grupo, usuario=usuario)
    Historico.objects.bulk_create(
        Historico(
            lancamento_id=lancamento_id,
            acao=Acao.ACESSO_REMOVIDO,
            dados={"pessoa": str(usuario.pk)},
        )
        for lancamento_id in acessos.values_list("lancamento_id", flat=True)
    )
    acessos.delete()


def preservar_acesso(grupo, usuario):
    """ADR 0008 (Q19a): before `usuario` becomes a payer, every open restricted bill only they
    see (and would stop seeing by RN07) gets their explicit access. Nothing tells the admin."""
    travar_abertas(grupo)
    contas = (
        lancamentos_visiveis(usuario, grupo)
        .filter(visibilidade=Visibilidade.RESTRITA, status__in=ABERTOS)
        .exclude(pagador=usuario)
        .exclude(_escolhido(usuario))
        .select_for_update()
        .order_by("pk")
    )
    for conta in contas:
        conta.espaco = grupo
        if not quem_ve(conta, sem=usuario):
            conta.acesso.add(usuario)
            _historico(conta, None, Acao.ACESSO_PRESERVADO, {"motivo": "papel_pagador"})
