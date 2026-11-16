"""Group domain operations. Every write runs inside a transaction."""

import hashlib
import secrets
from collections import Counter
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import APIException, NotFound, ValidationError

from .models import Convite, Espaco, Membro, Papel, Subgrupo

VALIDADE_CONVITE = timedelta(days=7)  # RN24


class Conflito(APIException):
    status_code = 409
    default_code = "conflito"


class UltimoAdmin(Conflito):
    default_detail = "O grupo precisa de pelo menos um admin. Promova outra pessoa a admin antes."
    default_code = "ultimo_admin"


class ContaRestritaSemQuemVeja(Conflito):
    """RN32 when the person acts (leave, delete own account): 409 listing the bills, which the
    person sees, and who could be chosen to see them (names only)."""

    default_code = "conta_restrita_orfa"
    SAIR = (
        "Você é a única pessoa que vê estas contas restritas. Para cada uma, escolha outra "
        "pessoa para ver ou cancele a conta; depois saia do grupo."
    )
    EXCLUIR = (
        "Há contas restritas abertas que só você vê. Saia desses grupos resolvendo cada conta "
        "(escolher outra pessoa para ver ou cancelar) antes de excluir a conta."
    )

    def __init__(self, contas, pessoas=(), mensagem=SAIR):
        self.mensagem = mensagem
        super().__init__(
            {
                "detail": mensagem,
                "code": self.default_code,
                "contas": [{"id": str(c.pk), "descricao": c.descricao} for c in contas],
                "pessoas": [{"id": str(p["id"]), "nome": p["nome"]} for p in pessoas],
            }
        )

    def __str__(self):
        return self.mensagem


class ConviteInvalido(APIException):
    # Same answer for missing, expired, used or revoked (RN31): nothing is revealed.
    status_code = 410
    default_detail = "Este convite não vale mais. Peça um novo a quem convidou."
    default_code = "convite_invalido"


def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def _admins_travados(espaco_ids):
    """RN04: lock the admin rows (fixed order, no deadlock) so concurrent changes see a
    stable set. Returns (espaco_id, membro_id, usuario_id) tuples."""
    return list(
        Membro.objects.select_for_update()
        .filter(espaco_id__in=espaco_ids, papel=Papel.ADMIN)
        .order_by("pk")
        .values_list("espaco_id", "pk", "usuario_id")
    )


def grupos_sem_outro_admin(usuario, travar=True):
    """RN04: groups where `usuario` is the only admin. `travar` needs a transaction."""
    seus = Membro.objects.filter(usuario=usuario).values("espaco_id")
    if travar:
        # Account deletion must serialize with bill creation in every group, including
        # groups where this person is a member/payer/chosen user rather than an admin.
        admins = _admins_travados(seus)
    else:
        admins = Membro.objects.filter(espaco_id__in=seus, papel=Papel.ADMIN).values_list(
            "espaco_id", "pk", "usuario_id"
        )
    total = Counter(espaco_id for espaco_id, _, _ in admins)
    sozinho = [e for e, _, u in admins if u == usuario.pk and total[e] == 1]
    return Espaco.objects.filter(pk__in=sozinho).order_by("nome")


@receiver(pre_delete, sender="contas_usuario.Usuario")
def proteger_ultimo_admin(sender, instance, **kwargs):
    """RN04/RN30: an account that is a group's only admin cannot be deleted. pre_delete runs
    inside the Collector transaction for obj.delete(), queryset.delete() and the admin."""
    grupos = grupos_sem_outro_admin(instance)
    if grupos:
        nomes = ", ".join(g.nome for g in grupos)
        raise UltimoAdmin(
            f"{instance.email} é o único admin de: {nomes}. Promova outra pessoa antes de "
            "excluir a conta."
        )


def restritas_de_quem_sai(usuario, travar=True):
    """RN32 for deleting the account: every group of the user, as if they left it."""
    from apps.lancamentos.servicos import restritas_sem_quem_veja

    if travar:  # M1: member rows before bills, the order `_desligar` uses
        list(
            Membro.objects.select_for_update()
            .filter(usuario=usuario)
            .order_by("pk")
            .values_list("pk", flat=True)
        )
    grupos = Espaco.objects.filter(membros__usuario=usuario).order_by("pk")
    return [c for g in grupos for c in restritas_sem_quem_veja(g, usuario, travar)]


@receiver(pre_delete, sender="contas_usuario.Usuario")
def proteger_conta_restrita(sender, instance, **kwargs):
    """RN32/ADR 0006: deleting one's own account is the person acting, so it is blocked like
    leaving (no resolutions here: those exist only in the exit, ADR 0007). Runs after the RN04
    guard, so locks keep the order admins -> member -> bills."""
    orfas = restritas_de_quem_sai(instance)
    if orfas:
        raise ContaRestritaSemQuemVeja(orfas, mensagem=ContaRestritaSemQuemVeja.EXCLUIR)


def criar_grupo(usuario, nome, casas=()):
    with transaction.atomic():
        grupo = Espaco.objects.create(tipo=Espaco.Tipo.GRUPO, nome=nome)
        Membro.objects.create(espaco=grupo, usuario=usuario, papel=Papel.ADMIN)
        Subgrupo.objects.bulk_create(Subgrupo(espaco=grupo, nome=casa) for casa in casas)
    return grupo


def gerar_convite(admin, grupo, papel):
    """Returns (convite, token). The plain token exists only here (RN31)."""
    if grupo.tipo != Espaco.Tipo.GRUPO:
        raise Conflito("O espaço pessoal não aceita membros nem convites.")  # RN03
    token = secrets.token_urlsafe(32)
    convite = Convite.objects.create(
        espaco=grupo,
        papel=papel,
        token_hash=hash_token(token),
        expira_em=timezone.now() + VALIDADE_CONVITE,
        criado_por=admin,
    )
    return convite, token


def convites_pendentes(grupo):
    return grupo.convites.filter(
        usado_em__isnull=True, revogado_em__isnull=True, expira_em__gt=timezone.now()
    )


def convite_valido(token, travar=False):
    convites = Convite.objects.filter(
        token_hash=hash_token(token),
        espaco__tipo=Espaco.Tipo.GRUPO,
        usado_em__isnull=True,
        revogado_em__isnull=True,
        expira_em__gt=timezone.now(),
    )
    if travar:
        convites = convites.select_for_update(of=("self",))
    convite = convites.select_related("espaco").first()
    if convite is None:
        raise ConviteInvalido()
    return convite


def revogar_convite(grupo, convite_id):
    with transaction.atomic():
        convite = get_object_or_404(convites_pendentes(grupo).select_for_update(), pk=convite_id)
        convite.revogado_em = timezone.now()
        convite.save(update_fields=["revogado_em"])


def aceitar_convite(usuario, token):
    with transaction.atomic():
        # The row lock makes acceptance single-use under concurrency (RN24).
        convite = convite_valido(token, travar=True)
        if Membro.objects.filter(espaco_id=convite.espaco_id, usuario=usuario).exists():
            # Existing members keep their role and do not consume the link (CA06).
            raise Conflito("Você já participa deste grupo.")
        try:
            membro = Membro.objects.create(
                espaco_id=convite.espaco_id, usuario=usuario, papel=convite.papel
            )
        except IntegrityError as exc:  # same user accepting two links at once
            raise Conflito("Você já participa deste grupo.") from exc
        convite.usado_por = usuario
        convite.usado_em = timezone.now()
        convite.save(update_fields=["usado_por", "usado_em"])
    return membro


def alterar_papel(grupo, membro_id, papel):
    from apps.lancamentos.servicos import preservar_acesso

    with transaction.atomic():
        admins = {pk for _, pk, _ in _admins_travados([grupo.pk])}
        membro = get_object_or_404(Membro.objects.select_for_update(), espaco=grupo, pk=membro_id)
        if papel != Papel.ADMIN and admins == {membro.pk}:
            raise UltimoAdmin()
        if papel != Papel.ADMIN:
            _revogar_convites_de(grupo, membro.usuario_id)
        if papel == Papel.PAGADOR and membro.papel != Papel.PAGADOR:
            preservar_acesso(grupo, membro.usuario)  # ADR 0008, before the role changes
        membro.papel = papel
        membro.save(update_fields=["papel"])
    return membro


def _revogar_convites_de(grupo, usuario_id):
    # RN21/RN31: someone who stops being admin cannot come back through a link they generated.
    convites_pendentes(grupo).filter(criado_por_id=usuario_id).update(revogado_em=timezone.now())


def _desligar(grupo, voluntario, resolucoes=(), por=None, **filtro):
    """Single exit point for RN21 and RN32 (Etapa 09 adds the notices). Locks: admins ->
    member -> bills by pk, the same order as `alterar_papel`.

    `voluntario` (leaving): applies the ADR 0007 resolutions, then 409 if any open restricted
    bill would still be left without anyone who sees it; the raise rolls everything back.
    Admin removal never blocks: those bills are cancelled automatically and the admin gets the
    same answer as any removal (the orphan query always runs; no shortcut depends on it)."""
    from apps.lancamentos import servicos as contas

    with transaction.atomic():
        admins = {pk for _, pk, _ in _admins_travados([grupo.pk])}
        # of=self: locking the joined Usuario row too would deadlock with an edit's deferred FK
        # check on "Quem vê" (it holds the bill this exit waits for).
        membro = get_object_or_404(
            Membro.objects.select_for_update(of=("self",)).select_related("usuario"),
            espaco=grupo,
            **filtro,
        )
        if admins == {membro.pk}:
            raise UltimoAdmin()
        usuario = membro.usuario
        voluntario = voluntario or usuario == por  # an admin removing themselves is leaving
        # Lock templates before bills. Drop explicit grants and responsibility on departure;
        # The author remains recorded, and can regain access through current membership.
        from apps.recorrencias.models import Recorrencia

        afetadas = (
            Recorrencia.objects.filter(espaco=grupo)
            .filter(Q(criador=usuario) | Q(pagador=usuario) | Q(acesso=usuario))
            .distinct()
        )
        modelos_ids = list(afetadas.values_list("pk", flat=True))
        casas_ids = list(
            afetadas.exclude(subgrupo__isnull=True).values_list("subgrupo_id", flat=True)
        )
        list(
            Subgrupo.objects.select_for_update()
            .filter(pk__in=casas_ids)
            .order_by("pk")
            .values_list("pk", flat=True)
        )
        list(
            Recorrencia.objects.select_for_update()
            .filter(pk__in=modelos_ids)
            .order_by("pk")
            .values_list("pk", flat=True)
        )
        Recorrencia.objects.filter(pk__in=modelos_ids, pagador=usuario).update(pagador=None)
        Recorrencia.acesso.through.objects.filter(
            recorrencia_id__in=modelos_ids, usuario=usuario
        ).delete()
        orfas = contas.restritas_sem_quem_veja(grupo, usuario)
        if voluntario:
            contas.resolver_na_saida(usuario, grupo, resolucoes, orfas)
            if contas.restritas_sem_quem_veja(grupo, usuario):
                raise ContaRestritaSemQuemVeja(orfas, contas.pessoas_para_escolher(grupo, usuario))
        else:
            contas.cancelar_orfas(usuario, orfas)
        contas.desligar_das_contas(usuario, grupo)
        _revogar_convites_de(grupo, membro.usuario_id)
        membro.delete()


def remover_membro(grupo, membro_id, por=None):
    _desligar(grupo, voluntario=False, por=por, pk=membro_id)


def sair(usuario, grupo, resolucoes=()):
    _desligar(grupo, voluntario=True, resolucoes=resolucoes, usuario=usuario)


def arquivar_casa(usuario, grupo, casa_id, destino_id):
    from apps.espacos.acesso import espaco_ou_404, lancamentos_visiveis, recorrencias_visiveis
    from apps.lancamentos.models import ABERTOS, Acao, Lancamento
    from apps.lancamentos.servicos import _historico
    from apps.recorrencias.models import Recorrencia
    from apps.recorrencias.servicos import travar_espaco

    with transaction.atomic():
        travar_espaco(usuario, grupo)
        grupo = espaco_ou_404(usuario, grupo.pk, "gerenciar_grupo")
        ids = [casa_id] + ([destino_id] if destino_id else [])
        casas = {
            c.pk: c
            for c in Subgrupo.objects.select_for_update()
            .filter(espaco=grupo, pk__in=ids)
            .order_by("pk")
        }
        casa = casas.get(casa_id)
        if casa is None:
            raise NotFound()
        if casa.arquivado:
            raise Conflito("Casa já arquivada.")
        destino = casas.get(destino_id) if destino_id else None
        if destino_id and (not destino or destino.arquivado or destino.pk == casa.pk):
            raise ValidationError({"destino_subgrupo": ["Escolha outra casa ativa deste grupo."]})
        modelos_ids = list(
            recorrencias_visiveis(usuario, grupo)
            .filter(subgrupo=casa)
            .exclude(estado="encerrada")
            .order_by("pk")
            .values_list("pk", flat=True)
        )
        modelos = list(
            Recorrencia.objects.select_for_update().filter(pk__in=modelos_ids).order_by("pk")
        )
        conta_ids = list(
            lancamentos_visiveis(usuario, grupo)
            .filter(subgrupo=casa, status__in=ABERTOS)
            .order_by("pk")
            .values_list("pk", flat=True)
        )
        contas = list(
            Lancamento.objects.select_for_update().filter(pk__in=conta_ids).order_by("pk")
        )
        for modelo in modelos:
            modelo.subgrupo = destino
            modelo.save(update_fields=["subgrupo", "atualizado_em"])
        for conta in contas:
            conta.subgrupo = destino
            conta.save(update_fields=["subgrupo", "atualizado_em"])
            _historico(
                conta,
                usuario,
                Acao.EDITADA,
                {"subgrupo": [casa.nome, destino.nome if destino else None]},
            )
        casa.arquivado = True
        casa.save(update_fields=["arquivado"])
        return casa
