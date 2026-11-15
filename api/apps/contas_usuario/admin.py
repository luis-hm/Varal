from allauth.socialaccount.models import SocialApp
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.db import transaction

from apps.espacos.models import Convite, Espaco, Membro, Subgrupo
from apps.espacos.servicos import UltimoAdmin, grupos_sem_outro_admin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """RN04: the delete pages refuse a group's only admin with a message instead of a 500."""

    def get_deleted_objects(self, objs, request):
        to_delete, model_count, perms_needed, protected = super().get_deleted_objects(objs, request)
        # The espacos models are read-only in the admin, but deleting an account cascades to
        # its personal space and memberships by design (RN30).
        perms_needed -= {m._meta.verbose_name for m in (Espaco, Membro, Convite, Subgrupo)}
        for usuario in objs:
            for grupo in grupos_sem_outro_admin(usuario, travar=False):
                protected.append(f"{usuario}: único admin do grupo “{grupo}”")
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
        except UltimoAdmin as exc:
            messages.error(request, str(exc.detail))


admin.site.unregister(SocialApp)
