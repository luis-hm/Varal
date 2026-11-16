from django.urls import path

from .views import ArquivoPDFView, ContaPDFView, DocumentoPDFView, LerView, UploadPDFView

urlpatterns = [
    path("boletos/ler/", LerView.as_view(), name="boletos_ler"),
    path(
        "espacos/<uuid:espaco_id>/boletos/pdf/", UploadPDFView.as_view(), name="boletos_pdf_upload"
    ),
    path(
        "boletos/pdfs/<uuid:documento_id>/", DocumentoPDFView.as_view(), name="boletos_pdf_detalhe"
    ),
    path(
        "boletos/pdfs/<uuid:documento_id>/arquivo/",
        ArquivoPDFView.as_view(),
        name="boletos_pdf_arquivo",
    ),
    path("lancamentos/<uuid:lancamento_id>/pdf/", ContaPDFView.as_view(), name="lancamentos_pdf"),
]
