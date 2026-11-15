"""Group domain operations. Every write runs inside a transaction."""

import hashlib
import secrets
from collections import Counter
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import APIException

from .models import Convite, Espaco, Membro, Papel, Subgrupo

VALIDADE_CONVITE = timedelta(days=7)  # RN24


class Conflito(APIException):
    status_code = 409
    default_code = "conflito"


class UltimoAdmin(Conflito):
    default_detail = "O grupo precisa de pelo menos um admin. Promova outra pessoa a admin antes."
    default_code = "ultimo_admin"


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
    seus = Membro.objects.filter(usuario=usuario, papel=Papel.ADMIN).values("espaco_id")
    if travar:
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
    with transaction.atomic():
        admins = {pk for _, pk, _ in _admins_travados([grupo.pk])}
        membro = get_object_or_404(Membro.objects.select_for_update(), espaco=grupo, pk=membro_id)
        if papel != Papel.ADMIN and admins == {membro.pk}:
            raise UltimoAdmin()
        membro.papel = papel
        membro.save(update_fields=["papel"])
    return membro


def _desligar(grupo, **filtro):
    """Single exit point for RN21 (Etapa 04: bills lose the payer; Etapa 09: admin notice)."""
    with transaction.atomic():
        admins = {pk for _, pk, _ in _admins_travados([grupo.pk])}
        membro = get_object_or_404(Membro.objects.select_for_update(), espaco=grupo, **filtro)
        if admins == {membro.pk}:
            raise UltimoAdmin()
        membro.delete()


def remover_membro(grupo, membro_id):
    _desligar(grupo, pk=membro_id)


def sair(usuario, grupo):
    _desligar(grupo, usuario=usuario)
