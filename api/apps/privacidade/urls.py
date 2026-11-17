from django.urls import path

from .download import ExportacaoDownloadView
from .views import ExportacaoView, ExportacoesView, IntencaoView

urlpatterns = [
    path("me/exportacoes/", ExportacoesView.as_view(), name="exportacoes"),
    path("me/exportacoes/<uuid:exportacao_id>/", ExportacaoView.as_view(), name="exportacao"),
    path(
        "me/exportacoes/<uuid:exportacao_id>/download/",
        ExportacaoDownloadView.as_view(),
        name="exportacao_download",
    ),
    path("me/exclusao/intencoes/", IntencaoView.as_view(), name="exclusao_intencao"),
]
