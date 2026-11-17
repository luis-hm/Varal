from allauth.socialaccount.models import SocialApp
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import PermissionDenied

from apps.espacos.models import Convite, Espaco, Membro, Subgrupo
from apps.espacos.servicos import (
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
        # Django's cascade preview includes personal bills and their histories even when the
        # corresponding ModelAdmin scopes its queryset. Do not expose those objects/counts.
        to_delete = [str(usuario) for usuario in objs]
        model_count = {Usuario._meta.verbose_name_plural: len(objs)}
        if protected:
            protected = ["Há dados protegidos que impedem esta exclusão."]
        # The espacos models are read-only in the admin, but deleting an account cascades to
        # its personal space and memberships by design (RN30).
        somente_leitura = (Espaco, Membro, Convite, Subgrupo, Lancamento, Historico)
        perms_needed -= {m._meta.verbose_name for m in somente_leitura}
        for usuario in objs:
            for grupo in grupos_sem_outro_admin(usuario, travar=False):
                protected.append(f"{usuario}: único admin do grupo “{grupo}”")
            if restritas_de_quem_sai(usuario, travar=False):
                protected.append("O titular precisa resolver pendências antes da exclusão.")
        return to_delete, model_count, perms_needed, protected

    # The pre_delete guard still runs at delete time (race after the confirmation page).
    def delete_model(self, request, obj):
        raise PermissionDenied("A exclusão deve ser feita pelo titular em Perfil.")

    def delete_queryset(self, request, queryset):
        raise PermissionDenied("A exclusão deve ser feita pelo titular em Perfil.")


admin.site.unregister(SocialApp)
