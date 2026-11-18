import uuid

import pytest
from django.core.cache import cache

REGISTROS = []


@pytest.fixture(autouse=True)
def local_auth_settings(settings, monkeypatch):
    settings.DEBUG = True
    settings.SECURE_SSL_REDIRECT = False
    settings.SESSION_COOKIE_SECURE = False
    settings.CSRF_COOKIE_SECURE = False
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    settings.RN31_TEST_NAMESPACE = str(uuid.uuid4())
    # Deletion records go to S3 in production (ADR 0018); tests keep them in memory.
    monkeypatch.setattr("apps.privacidade.exclusao.registro", REGISTROS.append)
    REGISTROS.clear()
    settings.CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def sem_agendamento_celery_concorrente(monkeypatch):
    """Do not execute eager Celery tasks concurrently inside one test process.

    Celery's eager join guard is process-global, whereas real workers are isolated
    processes. These tests exercise database interleavings, not task dispatch.
    """
    monkeypatch.setattr("celery.app.task.Task.apply_async", lambda *args, **kwargs: None)
