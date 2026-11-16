from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.contas_usuario.google import callback
from apps.contas_usuario.views import me

from .views import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/me/", me, name="me"),
    path("api/", include("apps.espacos.urls")),
    path("api/", include("apps.lancamentos.urls")),
    path("api/", include("apps.boletos.urls")),
    path("api/", include("apps.pagamentos.urls")),
    path("api/", include("apps.recorrencias.urls")),
    path("api/", include("apps.notificacoes.urls")),
    path("api/", include("apps.solicitacoes.urls")),
    path("api/auth/", include("allauth.headless.urls")),
    path("accounts/google/login/callback/", callback, name="google_callback"),
    path("accounts/", include("allauth.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
