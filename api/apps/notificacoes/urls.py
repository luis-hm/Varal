from django.urls import path

from . import views

urlpatterns = [
    path("notificacoes/", views.NotificacoesView.as_view(), name="notificacoes"),
    path("notificacoes/resumo/", views.ResumoView.as_view(), name="notificacoes_resumo"),
    path("notificacoes/ler-todas/", views.LerTodasView.as_view(), name="notificacoes_ler_todas"),
    path(
        "notificacoes/preferencias/",
        views.PreferenciasView.as_view(),
        name="notificacoes_preferencias",
    ),
    path(
        "notificacoes/push/configuracao/",
        views.PushConfiguracaoView.as_view(),
        name="notificacoes_push_configuracao",
    ),
    path(
        "notificacoes/push/inscricoes/",
        views.InscricoesView.as_view(),
        name="notificacoes_push_inscrever",
    ),
    path(
        "notificacoes/push/instalacoes/<uuid:instalacao_id>/",
        views.InstalacaoView.as_view(),
        name="notificacoes_push_revogar_instalacao",
    ),
    path(
        "notificacoes/<uuid:notificacao_id>/ler/", views.LerView.as_view(), name="notificacoes_ler"
    ),
]
