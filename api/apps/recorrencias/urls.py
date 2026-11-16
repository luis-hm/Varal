from django.urls import path

from . import views

urlpatterns = [
    path(
        "espacos/<uuid:espaco_id>/recorrencias/",
        views.RecorrenciasView.as_view(),
        name="recorrencias",
    ),
    path(
        "recorrencias/<uuid:recorrencia_id>/", views.RecorrenciaView.as_view(), name="recorrencia"
    ),
    path(
        "recorrencias/<uuid:recorrencia_id>/pausar/",
        views.PausarView.as_view(),
        name="recorrencia_pausar",
    ),
    path(
        "recorrencias/<uuid:recorrencia_id>/retomar/",
        views.RetomarView.as_view(),
        name="recorrencia_retomar",
    ),
    path(
        "recorrencias/<uuid:recorrencia_id>/encerrar/",
        views.EncerrarView.as_view(),
        name="recorrencia_encerrar",
    ),
]
