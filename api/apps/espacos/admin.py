from django.contrib import admin

from .models import Convite, Espaco, Membro, Subgrupo


class SomenteLeitura(admin.ModelAdmin):
    """Changes go through the API services (RN04, RN31); the admin only inspects."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Espaco)
class EspacoAdmin(SomenteLeitura):
    list_display = ["nome", "tipo", "dono"]
    list_filter = ["tipo"]


@admin.register(Membro)
class MembroAdmin(SomenteLeitura):
    list_display = ["usuario", "espaco", "papel", "criado_em"]
    list_filter = ["papel"]


@admin.register(Convite)
class ConviteAdmin(SomenteLeitura):
    exclude = ["token_hash"]
    list_display = ["espaco", "papel", "expira_em", "usado_em", "revogado_em"]


@admin.register(Subgrupo)
class SubgrupoAdmin(SomenteLeitura):
    list_display = ["nome", "espaco", "arquivado"]
