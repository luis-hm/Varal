from django.urls import path

from . import views

urlpatterns = [
    path(
        "espacos/<uuid:espaco_id>/lancamentos/simples/",
        views.ListaSimplesView.as_view(),
        name="lancamentos_simples",
    ),
    path(
        "espacos/<uuid:espaco_id>/lancamentos/",
        views.LancamentosView.as_view(),
        name="lancamentos",
    ),
    path("espacos/<uuid:espaco_id>/resumo/", views.ResumoView.as_view(), name="resumo"),
    path("lancamentos/<uuid:lancamento_id>/", views.LancamentoView.as_view(), name="lancamento"),
    path(
        "lancamentos/<uuid:lancamento_id>/cancelar/",
        views.CancelarView.as_view(),
        name="lancamento_cancelar",
    ),
]
