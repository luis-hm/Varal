"""Additional native-password and session isolation coverage; not yet integrated/run."""

import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.test import Client

from apps.contas_usuario.models import Usuario
from apps.privacidade.models import IntencaoExclusao

AUTH = "/api/auth/browser/v1/"
PASSWORD = "Secure-family-pass-726!"


def browser():
    client = Client(enforce_csrf_checks=True)
    assert client.get(AUTH + "config").status_code == 200
    return client


def post(client, path, data):
    return client.post(
        path,
        json.dumps(data),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    )


@pytest.mark.django_db(transaction=True)
def test_rn30_reauth_nativa_limite_e_intencao_por_sessao():
    user = Usuario.objects.create_user(
        username="native-boundary", email="native@example.com", password=PASSWORD
    )
    a, b = browser(), browser()
    for c in (a, b):
        r = post(c, AUTH + "auth/login", {"email": user.email, "password": PASSWORD})
        assert r.status_code == 200, r.content
        r = post(c, "/api/me/exclusao/intencoes/", {})
        assert r.status_code == 401 and r.json()["code"] == "reauth_required"
    r = post(a, AUTH + "auth/reauthenticate", {"password": PASSWORD})
    assert r.status_code == 200, r.content
    records = a.session["account_authentication_methods"]
    stamp = records[-1]["at"]
    assert records[-1]["reauthenticated"] is True
    from allauth.account.internal.flows import reauthentication

    with patch.object(reauthentication, "time", SimpleNamespace(time=lambda: stamp + 299)):
        r = post(a, "/api/me/exclusao/intencoes/", {})
        assert r.status_code == 201, r.content
        intent = r.json()
    with patch.object(reauthentication, "time", SimpleNamespace(time=lambda: stamp + 300)):
        r = post(a, "/api/me/exclusao/intencoes/", {})
        assert r.status_code == 401 and r.json()["code"] == "reauth_required"
    assert post(b, "/api/me/exclusao/intencoes/", {}).status_code == 401
    assert post(b, AUTH + "auth/reauthenticate", {"password": PASSWORD}).status_code == 200
    payload = {"id": intent["id"], "segredo": intent["segredo"], "confirmar": True}
    denied = b.delete(
        "/api/me/",
        json.dumps(payload),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=b.cookies["csrftoken"].value,
    )
    assert denied.status_code == 409
    no_csrf = a.delete("/api/me/", json.dumps(payload), content_type="application/json")
    assert no_csrf.status_code == 403
    assert IntencaoExclusao.objects.filter(
        pk=intent["id"], usuario=user, consumida_em__isnull=True
    ).exists()
    assert Usuario.objects.filter(pk=user.pk).exists()
