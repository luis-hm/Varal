from django.urls import path

from . import views

urlpatterns = [
    path(
        "lancamentos/<uuid:lancamento_id>/pagamentos/",
        views.MarcarView.as_view(),
        name="pagamentos_marcar",
    ),
    path(
        "lancamentos/<uuid:lancamento_id>/comprovantes/",
        views.UploadView.as_view(),
        name="comprovantes_upload",
    ),
    path(
        "lancamentos/<uuid:lancamento_id>/pagamentos/<uuid:pagamento_id>/desfazer/",
        views.DesfazerView.as_view(),
        name="pagamentos_desfazer",
    ),
    path(
        "lancamentos/<uuid:lancamento_id>/pagamentos/<uuid:pagamento_id>/comprovante/",
        views.AnexarView.as_view(),
        name="pagamentos_anexar",
    ),
    path(
        "comprovantes/<uuid:documento_id>/",
        views.DocumentoView.as_view(),
        name="comprovantes_detalhe",
    ),
    path(
        "comprovantes/<uuid:documento_id>/arquivo/",
        views.ArquivoView.as_view(),
        name="comprovantes_arquivo",
    ),
]
