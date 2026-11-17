from django.db import connection
from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@extend_schema(
    operation_id="health",
    responses=inline_serializer("Health", {"status": serializers.CharField()}),
    examples=[OpenApiExample("ok", value={"status": "ok"})],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    connection.ensure_connection()  # raises (500) if the database is unreachable
    return Response({"status": "ok"})


@extend_schema(
    operation_id="readiness",
    responses={200: inline_serializer("Readiness", {"status": serializers.CharField()}), 503: None},
)
@api_view(["GET"])
@permission_classes([AllowAny])
def readiness(request):
    """Fail closed on unavailable primary DB, Redis or private bucket; no domain locks."""
    import redis
    from django.conf import settings

    from apps.boletos.storage import cliente

    try:
        if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
            raise RuntimeError("storage credentials unavailable")
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        redis.Redis.from_url(
            settings.CELERY_BROKER_URL, socket_connect_timeout=2, socket_timeout=2
        ).ping()
        cliente().head_bucket(Bucket=settings.S3_BUCKET_NAME)
    except Exception:
        response = Response({"status": "indisponivel"}, status=503)
    else:
        response = Response({"status": "ok"})
    response["Cache-Control"] = "no-store"
    return response
