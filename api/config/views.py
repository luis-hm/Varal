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
