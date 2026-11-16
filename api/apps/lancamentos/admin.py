from django.contrib import admin
from django.http import Http404

from apps.espacos.acesso import lancamentos_do_usuario
from apps.espacos.admin import SomenteLeitura

from .models import Historico, Lancamento


class ContaSomenteLeitura(SomenteLeitura):
    def get_object(self, request, object_id, from_field=None):
        obj = super().get_object(request, object_id, from_field)
        if obj is None:
            raise Http404
        return obj


@admin.register(Lancamento)
class LancamentoAdmin(ContaSomenteLeitura):
    list_display = ["descricao", "espaco", "valor_centavos", "vencimento", "status"]
    list_filter = ["status", "visibilidade"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(pk__in=lancamentos_do_usuario(request.user).values("pk"))
        )


@admin.register(Historico)
class HistoricoAdmin(ContaSomenteLeitura):
    list_display = ["lancamento", "acao", "usuario", "criado_em"]
    list_filter = ["acao"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(lancamento__in=lancamentos_do_usuario(request.user).values("pk"))
        )
