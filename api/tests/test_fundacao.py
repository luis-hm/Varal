import pytest
from rest_framework.test import APIClient

from config.celery import ping


@pytest.mark.django_db
def test_health_ok():
    response = APIClient().get("/api/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_schema_documents_health():
    response = APIClient().get("/api/schema/", HTTP_ACCEPT="application/json")
    assert response.status_code == 200
    assert "/api/health/" in response.json()["paths"]


def test_celery_ping_task():
    assert ping.apply().get() == "pong"
