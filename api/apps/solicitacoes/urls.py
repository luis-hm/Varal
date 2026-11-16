from django.urls import path

from . import views

urlpatterns = [
    path("lancamentos/<uuid:origem_id>/solicitacoes/opcoes/", views.OpcoesView.as_view()),
    path("lancamentos/<uuid:origem_id>/solicitacoes/", views.CriarView.as_view()),
    path(
        "lancamentos/<uuid:origem_id>/solicitacoes/nonce/<uuid:nonce>/",
        views.RecuperarView.as_view(),
    ),
]
