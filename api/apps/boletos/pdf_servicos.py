"""Authorization and atomic attachment of immutable private documents."""

from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from apps.espacos.acesso import espaco_ou_404, lancamento_ou_404
from apps.espacos.servicos import Conflito
from apps.lancamentos.models import ABERTOS

from .models import DocumentoBoleto, TipoInstrumento
from .servicos import AUSENTE
from .tasks import agendar, recuperar_limpeza


def documento_ou_404(usuario, pk):
    doc = DocumentoBoleto.objects.filter(pk=pk).first()
    identidade = (doc.lancamento_id, doc.destino_id) if doc else None
    if doc and (doc.lancamento_id or doc.destino_id):
        lancamento_ou_404(usuario, doc.lancamento_id or doc.destino_id, travar=True)
    doc = DocumentoBoleto.objects.select_for_update().filter(pk=pk).first()
    if not doc or (doc.lancamento_id, doc.destino_id) != identidade:
        raise NotFound()
    if doc.lancamento_id:
        lancamento_ou_404(usuario, doc.lancamento_id)
    elif (
        doc.vinculado_em
        or doc.criado_por_id != usuario.pk
        or doc.criado_em <= timezone.now() - timedelta(hours=24)
    ):
        raise NotFound()
    else:
        try:
            if doc.destino_id:
                lancamento_ou_404(usuario, doc.destino_id, "editar_conta")
            else:
                espaco_ou_404(usuario, doc.espaco_id, "criar_conta")
        except Exception:
            raise NotFound() from None
    return doc


def preparar_pdf(usuario, espaco, dados, conta=None):
    valor = dados.pop("documento_pdf", AUSENTE)
    emissao = dados.pop("data_emissao", AUSENTE)
    beneficiario = dados.pop("beneficiario", AUSENTE)
    atual = DocumentoBoleto.objects.filter(lancamento=conta).first() if conta else None
    if valor is AUSENTE:
        doc = atual
    elif valor is None:
        doc = None
    elif atual and atual.pk == valor:
        doc = atual
    else:
        doc = DocumentoBoleto.objects.select_for_update().filter(pk=valor).first()
        if (
            not doc
            or doc.criado_por_id != usuario.pk
            or doc.espaco_id != espaco.pk
            or doc.vinculado_em
            or doc.lancamento_id
            or doc.criado_em <= timezone.now() - timedelta(hours=24)
            or doc.destino_id != (conta.pk if conta else None)
        ):
            raise NotFound()
        if doc.estado not in ("lido", "conferencia_manual"):
            raise ValidationError({"documento_pdf": ["Aguarde a leitura de um PDF válido."]})
    mudou = doc != atual
    if (
        conta
        and conta.status not in ABERTOS
        and (mudou or emissao is not AUSENTE or beneficiario is not AUSENTE)
    ):
        raise Conflito("Só contas abertas podem alterar o PDF ou seus dados.")
    if (emissao is not AUSENTE or beneficiario is not AUSENTE) and not doc:
        raise ValidationError({"documento_pdf": ["Informe um PDF para seus metadados."]})
    if doc and (mudou or "instrumento" in dados):
        candidatos = doc.resultado.get("candidatos", [])
        if candidatos:
            entrada = dados.get("instrumento") or {}
            codigo = entrada.get("codigo")
            from .serializers import ler_entrada

            if not codigo or ler_entrada({"codigo": codigo}).codigo not in [
                c.get("codigo") for c in candidatos
            ]:
                raise ValidationError(
                    {"instrumento": ["Escolha uma das linhas válidas encontradas no PDF."]}
                )
    return doc, atual, mudou, emissao, beneficiario


def metadados_mudaram(conta, alteracao, instrumento):
    """Compare confirmed values after the instrument and PDF rules have been applied."""
    from .models import Instrumento

    doc, _, _, emissao, beneficiario = alteracao
    if not doc or (emissao is AUSENTE and beneficiario is AUSENTE):
        return False
    atual = Instrumento.objects.filter(lancamento=conta).first()
    antes_emissao = atual.data_emissao if atual else None
    antes_beneficiario = atual.beneficiario if atual else None
    if instrumento.mudou:
        novo = instrumento.dados
        tipo = novo["tipo"] if novo else TipoInstrumento.MANUAL
        final_beneficiario = novo.get("beneficiario") if novo else None
        final_emissao = antes_emissao if novo and atual else None
    else:
        tipo = atual.tipo if atual else TipoInstrumento.MANUAL
        final_emissao = antes_emissao
        final_beneficiario = antes_beneficiario
    if emissao is not AUSENTE:
        final_emissao = emissao
    if beneficiario is not AUSENTE and not (tipo == TipoInstrumento.PIX and final_beneficiario):
        final_beneficiario = beneficiario
    return (antes_emissao, antes_beneficiario) != (final_emissao, final_beneficiario)


def aplicar_pdf(conta, alteracao, instrumento):
    doc, atual, mudou, emissao, beneficiario = alteracao
    if mudou and atual:
        atual.delete()
        transaction.on_commit(lambda: agendar(recuperar_limpeza))
    if mudou and doc:
        doc.lancamento = conta
        doc.vinculado_em = timezone.now()
        doc.save(update_fields=["lancamento", "vinculado_em"])
    if not doc and mudou:
        from .models import Instrumento

        Instrumento.objects.filter(lancamento=conta, tipo=TipoInstrumento.MANUAL).delete()
    if doc:
        from .models import Instrumento

        obj, _ = Instrumento.objects.get_or_create(
            lancamento=conta, defaults={"tipo": TipoInstrumento.MANUAL}
        )
        campos = []
        if emissao is not AUSENTE and obj.data_emissao != emissao:
            obj.data_emissao = emissao
            campos.append("data_emissao")
        if (
            beneficiario is not AUSENTE
            and obj.beneficiario != beneficiario
            and not (obj.tipo == TipoInstrumento.PIX and obj.beneficiario)
        ):
            obj.beneficiario = beneficiario
            campos.append("beneficiario")
        if campos:
            obj.save(update_fields=campos)
    return (
        {"pdf_alterado": True}
        if mudou
        else (
            {"metadados_pdf_alterados": True}
            if emissao is not AUSENTE or beneficiario is not AUSENTE
            else {}
        )
    )
