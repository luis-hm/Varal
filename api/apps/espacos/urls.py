from django.urls import path

from . import views

urlpatterns = [
    path("grupos/", views.GruposView.as_view(), name="grupos"),
    path("grupos/<uuid:grupo_id>/", views.GrupoView.as_view(), name="grupo"),
    path("grupos/<uuid:grupo_id>/sair/", views.SairView.as_view(), name="grupo_sair"),
    path("grupos/<uuid:grupo_id>/convites/", views.ConvitesView.as_view(), name="convites"),
    path(
        "grupos/<uuid:grupo_id>/convites/<uuid:convite_id>/",
        views.ConviteView.as_view(),
        name="convite",
    ),
    path(
        "grupos/<uuid:grupo_id>/membros/<uuid:membro_id>/",
        views.MembroView.as_view(),
        name="membro",
    ),
    path("grupos/<uuid:grupo_id>/subgrupos/", views.SubgruposView.as_view(), name="casas"),
    path(
        "grupos/<uuid:grupo_id>/subgrupos/<uuid:casa_id>/",
        views.SubgrupoView.as_view(),
        name="casa",
    ),
    path(
        "grupos/<uuid:grupo_id>/subgrupos/<uuid:casa_id>/arquivamento/",
        views.ArquivamentoPreviewView.as_view(),
        name="casa_arquivamento_preview",
    ),
    path("convites/<str:token>/", views.ConvitePublicoView.as_view(), name="convite_publico"),
    path(
        "convites/<str:token>/aceitar/", views.AceitarConviteView.as_view(), name="convite_aceitar"
    ),
]
