import calendar
import hashlib
import json
import uuid
from datetime import date

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.boletos.tasks import _travar_objeto
from apps.espacos.acesso import espaco_ou_404, recorrencia_ou_404
from apps.espacos.models import Espaco, Membro, Papel, Subgrupo
from apps.espacos.servicos import Conflito, _admins_travados
from apps.lancamentos.models import Acao, Lancamento, Status
from apps.lancamentos.servicos import _historico, validar
from apps.lancamentos.servicos import criar as criar_conta

from .models import CompetenciaDevida, OperacaoRecorrencia, Recorrencia, RevisaoRecorrencia

MENSAGEM_MES = (
    "A primeira conta recorrente precisa vencer neste mês. Salve esta cobrança "
    "sem repetir ou use uma cobrança deste mês."
)


def mes_atual():
    return timezone.localdate().replace(day=1)


def proximo_mes(mes):
    return date(mes.year + (mes.month == 12), 1 if mes.month == 12 else mes.month + 1, 1)


def vencimento(competencia, dia):
    return competencia.replace(
        day=min(dia, calendar.monthrange(competencia.year, competencia.month)[1])
    )


def travar_espaco(usuario, espaco):
    if espaco.tipo == Espaco.Tipo.GRUPO:
        _admins_travados([espaco.pk])
        if usuario is not None:
            list(
                Membro.objects.select_for_update(of=("self",))
                .filter(espaco=espaco, usuario=usuario)
                .values_list("pk", flat=True)
            )
    else:
        list(Espaco.objects.select_for_update().filter(pk=espaco.pk).values_list("pk", flat=True))


def travar_modelo(usuario, recorrencia_id, acao=None, casas_extra=()):
    inicial = recorrencia_ou_404(usuario, recorrencia_id)
    travar_espaco(usuario, inicial.espaco)
    inicial = recorrencia_ou_404(usuario, recorrencia_id)
    casas = {pk for pk in (*casas_extra, inicial.subgrupo_id) if pk}
    list(
        Subgrupo.objects.select_for_update()
        .filter(espaco=inicial.espaco, pk__in=casas)
        .order_by("pk")
        .values_list("pk", flat=True)
    )
    list(
        Recorrencia.objects.select_for_update()
        .filter(pk=recorrencia_id)
        .values_list("pk", flat=True)
    )
    return recorrencia_ou_404(usuario, recorrencia_id, acao)


def _normalizar_template(espaco, dados, modelo=None):
    dados = dict(dados)
    mapeados = {
        k: dados.pop(k)
        for k in list(dados)
        if k in ("subgrupo", "pagador", "visibilidade", "acesso")
    }
    valores = validar(espaco, mapeados, modelo)
    dados.update(valores)
    tipo = dados.get("valor_tipo", modelo.valor_tipo if modelo else None)
    valor = dados.get("valor_centavos", modelo.valor_centavos if modelo else None)
    if tipo == "variavel":
        if valor is not None and "valor_centavos" in dados:
            raise ValidationError({"valor_centavos": ["Valor variável deve ficar a definir."]})
        dados["valor_centavos"] = None
    elif tipo == "fixo" and (valor is None or valor <= 0):
        raise ValidationError({"valor_centavos": ["Informe um valor fixo positivo."]})
    return dados


def _snapshot(modelo):
    return {
        "descricao": modelo.descricao,
        "dia_vencimento": modelo.dia_vencimento,
        "valor_tipo": modelo.valor_tipo,
        "valor_centavos": modelo.valor_centavos,
    }


def _dados_da_competencia(modelo, competencia):
    dados = {}
    for alteracoes in modelo.revisoes.filter(competencia_inicio__lte=competencia).values_list(
        "alteracoes", flat=True
    ):
        dados.update(alteracoes)
    return dados


def materializar(modelo, ate):
    if modelo.estado != Recorrencia.Estado.ATIVA:
        return
    cursor = modelo.cursor
    lote = []
    while cursor <= ate:
        lote.append(CompetenciaDevida(recorrencia=modelo, competencia=cursor))
        cursor = proximo_mes(cursor)
        if len(lote) == 120:
            CompetenciaDevida.objects.bulk_create(lote, ignore_conflicts=True)
            lote = []
    if lote:
        CompetenciaDevida.objects.bulk_create(lote, ignore_conflicts=True)
    if cursor != modelo.cursor:
        modelo.cursor = cursor
        modelo.save(update_fields=["cursor", "atualizado_em"])


def _audiencia(modelo, pagador_id):
    if modelo.espaco.tipo == Espaco.Tipo.PESSOAL:
        return {modelo.espaco.dono_id}
    escolhidos = set(modelo.acesso.values_list("pk", flat=True))
    membros = list(Membro.objects.filter(espaco=modelo.espaco).values_list("usuario_id", "papel"))
    vistos = set()
    for uid, papel in membros:
        if papel == Papel.PAGADOR:
            ve = uid == pagador_id or (modelo.visibilidade == "restrita" and uid in escolhidos)
        else:
            ve = (
                modelo.visibilidade == "grupo"
                or uid in (modelo.criador_id, pagador_id)
                or uid in escolhidos
            )
        if ve:
            vistos.add(uid)
    return vistos


def gerar(modelo, devida):
    if devida.estado == "gerada":
        return Lancamento.objects.filter(recorrencia=modelo, competencia=devida.competencia).first()
    pagador_id = modelo.pagador_id
    if modelo.espaco.tipo == Espaco.Tipo.GRUPO and pagador_id:
        if not Membro.objects.filter(
            espaco=modelo.espaco,
            usuario_id=pagador_id,
            papel__in=[Papel.ADMIN, Papel.MEMBRO, Papel.PAGADOR],
        ).exists():
            pagador_id = None
    if modelo.visibilidade == "restrita" and not _audiencia(modelo, pagador_id):
        if modelo.estado != Recorrencia.Estado.ENCERRADA:
            modelo.estado = Recorrencia.Estado.PAUSADA
        modelo.motivo_pausa = "sem_audiencia"
        modelo.save(update_fields=["estado", "motivo_pausa", "atualizado_em"])
        devida.estado = "bloqueada"
        devida.save(update_fields=["estado"])
        return None
    dados = _dados_da_competencia(modelo, devida.competencia)
    subgrupo = modelo.subgrupo if modelo.subgrupo_id and not modelo.subgrupo.arquivado else None
    valor = dados["valor_centavos"] if dados["valor_tipo"] == "fixo" else None
    conta = Lancamento.objects.create(
        espaco=modelo.espaco,
        criador=modelo.criador,
        pagador_id=pagador_id,
        descricao=dados["descricao"],
        valor_centavos=valor,
        vencimento=vencimento(devida.competencia, dados["dia_vencimento"]),
        status=Status.PENDENTE if valor is not None else Status.AGUARDANDO,
        subgrupo=subgrupo,
        visibilidade=modelo.visibilidade,
        recorrencia=modelo,
        competencia=devida.competencia,
    )
    if modelo.visibilidade == "restrita":
        conta.acesso.set(modelo.acesso.filter(participacoes__espaco=modelo.espaco).distinct())
    evento = {"competencia": devida.competencia.isoformat()}
    if modelo.subgrupo_id and subgrupo is None:
        evento["casa_arquivada"] = True
    if modelo.pagador_id and not pagador_id:
        evento["pagador_indisponivel"] = True
    _historico(conta, None, Acao.CRIADA, evento)
    devida.estado = "gerada"
    devida.save(update_fields=["estado"])
    return conta


def _hash(dados):
    return hashlib.sha256(
        json.dumps(dados, sort_keys=True, default=str, separators=(",", ":")).encode()
    ).hexdigest()


def criar(usuario, espaco, dados):
    dados = dict(dados)
    chave = dados.pop("chave_idempotencia")
    inicial = dados.pop("ocorrencia_inicial", None)
    assinatura = _hash({"espaco": str(espaco.pk), "dados": dados, "inicial": inicial})
    atual = mes_atual()
    with transaction.atomic():
        travar_espaco(usuario, espaco)
        espaco = espaco_ou_404(usuario, espaco.pk, "criar_conta")
        _travar_objeto(uuid.uuid5(usuario.pk, str(chave)))
        anterior = (
            OperacaoRecorrencia.objects.filter(usuario=usuario, chave=chave)
            .select_related("recorrencia")
            .first()
        )
        if anterior:
            if anterior.hash_entrada != assinatura:
                raise Conflito("Chave de operação já utilizada com outros dados.")
            modelo = recorrencia_ou_404(usuario, anterior.recorrencia_id)
            conta = Lancamento.objects.filter(
                recorrencia=modelo, competencia=anterior.competencia
            ).first()
            return modelo, conta, False
        if dados.get("subgrupo"):
            list(
                Subgrupo.objects.select_for_update()
                .filter(espaco=espaco, pk=dados["subgrupo"])
                .values_list("pk", flat=True)
            )
        dados = _normalizar_template(espaco, dados)
        acesso = dados.pop("acesso", set())
        modelo = Recorrencia.objects.create(espaco=espaco, criador=usuario, cursor=atual, **dados)
        modelo.acesso.set(acesso)
        RevisaoRecorrencia.objects.create(
            recorrencia=modelo, competencia_inicio=atual, alteracoes=_snapshot(modelo)
        )
        materializar(modelo, atual)
        devida = modelo.competencias.select_for_update().get(competencia=atual)
        if inicial is None:
            conta = gerar(modelo, devida)
        else:
            inicial = dict(inicial)
            if inicial["vencimento"].replace(day=1) != atual:
                raise ValidationError({"ocorrencia_inicial": {"vencimento": [MENSAGEM_MES]}})
            if modelo.valor_tipo == "fixo" and inicial["valor_centavos"] != modelo.valor_centavos:
                raise ValidationError(
                    {"ocorrencia_inicial": {"valor_centavos": ["Valor diferente do modelo fixo."]}}
                )
            inicial.update(
                descricao=modelo.descricao,
                subgrupo=modelo.subgrupo_id,
                pagador=modelo.pagador_id,
                visibilidade=modelo.visibilidade,
                acesso=list(acesso),
            )
            conta = criar_conta(usuario, espaco, inicial)
            if conta.vencimento.replace(day=1) != atual:
                raise ValidationError({"ocorrencia_inicial": {"vencimento": [MENSAGEM_MES]}})
            if modelo.valor_tipo == "fixo" and conta.valor_centavos != modelo.valor_centavos:
                raise ValidationError(
                    {"ocorrencia_inicial": {"valor_centavos": ["Valor diferente do modelo fixo."]}}
                )
            conta.recorrencia, conta.competencia = modelo, atual
            conta.save(update_fields=["recorrencia", "competencia"])
            devida.estado = "gerada"
            devida.save(update_fields=["estado"])
        OperacaoRecorrencia.objects.create(
            usuario=usuario,
            chave=chave,
            hash_entrada=assinatura,
            recorrencia=modelo,
            competencia=atual,
        )
        modelo.espaco.meu_papel = espaco.meu_papel
        return modelo, conta, True


def editar_modelo(usuario, recorrencia_id, dados, competencia_inicio=None):
    with transaction.atomic():
        modelo = travar_modelo(
            usuario, recorrencia_id, "editar_conta", casas_extra=(dados.get("subgrupo"),)
        )
        if modelo.estado == Recorrencia.Estado.ENCERRADA:
            raise Conflito("Recorrência encerrada não pode ser alterada.")
        materializar(modelo, mes_atual())
        dados = _normalizar_template(modelo.espaco, dados, modelo)
        acesso = dados.pop("acesso", None)
        alteracoes = {}
        for campo, valor in dados.items():
            if getattr(modelo, campo) != valor:
                setattr(modelo, campo, valor)
                if campo in ("descricao", "dia_vencimento", "valor_tipo", "valor_centavos"):
                    alteracoes[campo] = valor
        if acesso is not None:
            modelo.acesso.set(acesso)
        modelo.save()
        if alteracoes:
            RevisaoRecorrencia.objects.create(
                recorrencia=modelo,
                competencia_inicio=competencia_inicio or mes_atual(),
                alteracoes=alteracoes,
            )
        return modelo


def transicao(usuario, recorrencia_id, acao):
    with transaction.atomic():
        modelo = travar_modelo(usuario, recorrencia_id, "editar_conta")
        atual = mes_atual()
        if acao == "pausar":
            if modelo.estado != Recorrencia.Estado.ATIVA:
                raise Conflito("A recorrência não está ativa.")
            materializar(modelo, atual)
            modelo.estado, modelo.motivo_pausa = Recorrencia.Estado.PAUSADA, "manual"
        elif acao == "encerrar":
            if modelo.estado == Recorrencia.Estado.ENCERRADA:
                raise Conflito("A recorrência já está encerrada.")
            materializar(modelo, atual)
            modelo.estado, modelo.motivo_pausa = Recorrencia.Estado.ENCERRADA, ""
        elif acao == "retomar":
            if modelo.estado != Recorrencia.Estado.PAUSADA:
                raise Conflito("Só recorrência pausada pode ser retomada.")
            modelo.estado, modelo.motivo_pausa, modelo.cursor = Recorrencia.Estado.ATIVA, "", atual
            modelo.save(update_fields=["estado", "motivo_pausa", "cursor", "atualizado_em"])
            modelo.competencias.filter(estado="bloqueada").update(estado="pendente")
            materializar(modelo, atual)
            devida = modelo.competencias.select_for_update().get(competencia=atual)
            gerar(modelo, devida)
            return modelo
        else:
            raise ValueError("Unknown transition")
        modelo.save(update_fields=["estado", "motivo_pausa", "atualizado_em"])
        return modelo


def processar_recorrencia(pk):
    with transaction.atomic():
        ref = Recorrencia.objects.select_related("espaco").filter(pk=pk).first()
        if not ref:
            return
        travar_espaco(None, ref.espaco)
        ref = Recorrencia.objects.filter(pk=pk).first()
        if not ref:
            return
        if ref.subgrupo_id:
            list(
                Subgrupo.objects.select_for_update()
                .filter(pk=ref.subgrupo_id)
                .values_list("pk", flat=True)
            )
        modelo = (
            Recorrencia.objects.select_for_update(of=("self",))
            .select_related("espaco", "subgrupo", "criador")
            .filter(pk=pk)
            .first()
        )
        if not modelo:
            return
        materializar(modelo, mes_atual())
        if modelo.motivo_pausa == "sem_audiencia":
            if modelo.estado != Recorrencia.Estado.ENCERRADA:
                return
            modelo.competencias.filter(estado="bloqueada").update(estado="pendente")
            modelo.motivo_pausa = ""
            modelo.save(update_fields=["motivo_pausa", "atualizado_em"])
        for devida in (
            modelo.competencias.select_for_update()
            .filter(estado="pendente", competencia__lte=mes_atual())
            .order_by("competencia")
        ):
            gerar(modelo, devida)
            if modelo.motivo_pausa == "sem_audiencia":
                break


def _alvo_proximos(usuario, conta_id, casas_extra=()):
    from apps.espacos.acesso import lancamento_ou_404, lancamentos_visiveis

    inicial = lancamento_ou_404(usuario, conta_id, "editar_conta")
    if not inicial.recorrencia_id:
        raise ValidationError({"escopo": ["Esta conta não é recorrente."]})
    modelo = travar_modelo(usuario, inicial.recorrencia_id, "editar_conta", casas_extra=casas_extra)
    contas = lancamentos_visiveis(usuario, modelo.espaco).filter(
        recorrencia=modelo,
        competencia__gte=inicial.competencia,
        status__in=(Status.PENDENTE, Status.AGUARDANDO),
    )
    ids = list(contas.order_by("pk").values_list("pk", flat=True))
    list(
        Lancamento.objects.select_for_update()
        .filter(pk__in=ids)
        .order_by("pk")
        .values_list("pk", flat=True)
    )
    alvo = lancamento_ou_404(usuario, conta_id, "editar_conta")
    if alvo.status not in (Status.PENDENTE, Status.AGUARDANDO) or alvo.recorrencia_id != modelo.pk:
        raise Conflito("Só conta aberta pode alterar próximas ocorrências.")
    return modelo, alvo, ids


def editar_proximos(usuario, conta_id, dados):
    from apps.lancamentos.servicos import editar

    with transaction.atomic():
        modelo, alvo, ids = _alvo_proximos(usuario, conta_id, casas_extra=(dados.get("subgrupo"),))
        dados = dict(dados)
        tipo = dados.pop("valor_tipo", None)
        alteracoes = {
            k: dados[k]
            for k in ("descricao", "subgrupo", "pagador", "visibilidade", "acesso")
            if k in dados
        }
        if "vencimento" in dados:
            alteracoes["dia_vencimento"] = dados["vencimento"].day
        if tipo is not None:
            alteracoes["valor_tipo"] = tipo
        tipo_final = tipo or modelo.valor_tipo
        if tipo_final == "variavel":
            if tipo == "variavel":
                alteracoes["valor_centavos"] = None
        elif "valor_centavos" in dados:
            alteracoes["valor_centavos"] = dados["valor_centavos"]
        editar_modelo(usuario, modelo.pk, alteracoes, competencia_inicio=alvo.competencia)
        for conta in Lancamento.objects.filter(pk__in=ids).order_by("pk"):
            mudanca = dict(dados)
            if conta.pk != alvo.pk:
                for campo in (
                    "instrumento",
                    "documento_pdf",
                    "data_emissao",
                    "beneficiario",
                    "confirmar_chegada",
                ):
                    mudanca.pop(campo, None)
                if "vencimento" in mudanca:
                    mudanca["vencimento"] = vencimento(conta.competencia, dados["vencimento"].day)
                if conta.status == Status.AGUARDANDO or tipo_final == "variavel":
                    mudanca.pop("valor_centavos", None)
            editar(usuario, conta.pk, mudanca)
        resultado = Lancamento.objects.select_related("espaco").get(pk=alvo.pk)
        resultado.espaco.meu_papel = modelo.espaco.meu_papel
        return resultado


def cancelar_proximos(usuario, conta_id):
    from apps.lancamentos.servicos import _cancelar

    with transaction.atomic():
        modelo, alvo, ids = _alvo_proximos(usuario, conta_id)
        materializar(modelo, mes_atual())
        modelo.estado, modelo.motivo_pausa = Recorrencia.Estado.ENCERRADA, ""
        modelo.save(update_fields=["estado", "motivo_pausa", "atualizado_em"])
        # The explicit cancellation closes generated and not-yet-generated obligations at the cut.
        modelo.competencias.filter(competencia__gte=alvo.competencia).exclude(
            estado="gerada"
        ).delete()
        for conta in Lancamento.objects.filter(pk__in=ids).order_by("pk"):
            _cancelar(conta, usuario)
        return alvo
