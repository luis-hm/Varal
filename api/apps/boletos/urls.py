from django.urls import path

from .views import LerView

urlpatterns = [path("boletos/ler/", LerView.as_view(), name="boletos_ler")]
