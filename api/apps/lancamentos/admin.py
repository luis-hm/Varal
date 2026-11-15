from django.contrib import admin

from apps.espacos.admin import SomenteLeitura

from .models import Historico, Lancamento


@admin.register(Lancamento)
class LancamentoAdmin(SomenteLeitura):
    list_display = ["descricao", "espaco", "valor_centavos", "vencimento", "status"]
    list_filter = ["status", "visibilidade"]


@admin.register(Historico)
class HistoricoAdmin(SomenteLeitura):
    list_display = ["lancamento", "acao", "usuario", "criado_em"]
    list_filter = ["acao"]
