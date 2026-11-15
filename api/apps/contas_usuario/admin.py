from allauth.socialaccount.models import SocialApp
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.db import transaction

from apps.espacos.models import Convite, Espaco, Membro, Subgrupo
from apps.espacos.servicos import (
    Conflito,
    grupos_sem_outro_admin,
    restritas_de_quem_sai,
)
from apps.lancamentos.models import Historico, Lancamento

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """RN04/RN32: the delete pages refuse a group's only admin, or the last person who sees an
    open restricted bill, with a message instead of a 500."""

    def get_deleted_objects(self, objs, request):
        to_delete, model_count, perms_needed, protected = super().get_deleted_objects(objs, request)
        # The espacos models are read-only in the admin, but deleting an account cascades to
        # its personal space and memberships by design (RN30).
        somente_leitura = (Espaco, Membro, Convite, Subgrupo, Lancamento, Historico)
        perms_needed -= {m._meta.verbose_name for m in somente_leitura}
        for usuario in objs:
            for grupo in grupos_sem_outro_admin(usuario, travar=False):
                protected.append(f"{usuario}: único admin do grupo “{grupo}”")
            for conta in restritas_de_quem_sai(usuario, travar=False):
                protected.append(
                    f"{usuario}: única pessoa que vê a conta restrita “{conta}” ({conta.espaco})"
                )
        return to_delete, model_count, perms_needed, protected

    # The pre_delete guard still runs at delete time (race after the confirmation page).
    def delete_model(self, request, obj):
        self._apagar(request, lambda: super(UsuarioAdmin, self).delete_model(request, obj))

    def delete_queryset(self, request, queryset):
        self._apagar(request, lambda: super(UsuarioAdmin, self).delete_queryset(request, queryset))

    def _apagar(self, request, apagar):
        try:
            with transaction.atomic():
                apagar()
        except Conflito as exc:  # RN04 or RN32 raised by the pre_delete guards
            messages.error(request, str(exc))


admin.site.unregister(SocialApp)
