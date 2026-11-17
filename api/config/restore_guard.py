from django.conf import settings
from django.http import JsonResponse


class RestoreGuardMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.VARAL_RESTORE_MODE:
            response = JsonResponse({"status": "indisponivel"}, status=503)
            response["Cache-Control"] = "no-store"
            return response
        return self.get_response(request)
