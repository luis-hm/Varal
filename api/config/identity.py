"""Bind a browser's private requests to the user of the actual session cookie."""

import uuid

from django.http import JsonResponse
from django.utils.cache import patch_cache_control


class IdentidadePrivadaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        # Explicit identity transitions and bearer-key confirmation do not carry the
        # previous private context. Authenticated account actions, notably logout,
        # remain fenced when the client supplies an expected identity.
        transition = path in {
            "/api/auth/browser/v1/auth/login",
            "/api/auth/browser/v1/auth/signup",
            "/api/auth/browser/v1/auth/email/verify",
        } or path.startswith("/api/auth/browser/v1/auth/provider/")
        private_api = (
            path.startswith("/api/")
            and not transition
            and path not in {"/api/health/", "/api/schema/", "/api/docs/"}
        )
        if not private_api:
            return self.get_response(request)
        user = request.user
        prior_identity = str(user.pk) if user.is_authenticated else None
        privacy_route = (
            path == "/api/me/"
            or path.startswith("/api/me/exportacoes/")
            or path.startswith("/api/me/exclusao/")
            or path == "/api/auth/google/tickets/consumir/"
        )
        if privacy_route and not user.is_authenticated:
            response = JsonResponse(
                {"status": 401, "meta": {"is_authenticated": False}}, status=401
            )
            patch_cache_control(response, private=True, no_store=True)
            return response
        expected = request.headers.get("X-Varal-Identidade-Esperada")
        if expected is not None and user.is_authenticated:
            try:
                valid = str(uuid.UUID(expected)) == expected and str(user.pk) == expected
            except (ValueError, AttributeError, TypeError):
                valid = False
            if not valid:
                response = JsonResponse({"detail": "Sessão divergente."}, status=409)
                patch_cache_control(response, private=True, no_store=True)
                if user.is_authenticated:
                    response["X-Varal-Identidade"] = str(user.pk)
                return response
        response = self.get_response(request)
        if request.user.is_authenticated:
            response["X-Varal-Identidade"] = str(request.user.pk)
            patch_cache_control(response, private=True, no_store=True)
        elif (
            prior_identity
            and request.method == "DELETE"
            and (
                (
                    path == "/api/auth/browser/v1/auth/session"
                    and response.status_code in (200, 204, 401)
                )
                or (path == "/api/me/" and response.status_code == 204)
            )
        ):
            response["X-Varal-Identidade"] = prior_identity
            patch_cache_control(response, private=True, no_store=True)
        return response
