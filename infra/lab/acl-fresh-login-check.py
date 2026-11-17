"""Synthetic post-cutover check: fresh native login must not restore revoked access."""
import json
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client, override_settings

if (
    os.environ.get("VARAL_LAB_FIXTURE") != "isolated"
    or not os.environ.get("VARAL_LAB_DB")
    or connection.settings_dict["NAME"] != os.environ["VARAL_LAB_DB"]
    or settings.VARAL_RESTORE_MODE
):
    raise RuntimeError("Dedicated active lab required")
fixture = json.loads(os.environ["FIXTURE_DATA"])
user = get_user_model().objects.get(pk=fixture["person"])
if not user.is_active or not user.email.endswith("@example.invalid") or not user.username.startswith("acl-removed-"):
    raise RuntimeError("Synthetic user required")
password = "Synthetic-fresh-acl-46!"
user.set_password(password)
user.save(update_fields=["password"])
with override_settings(ALLOWED_HOSTS=[*settings.ALLOWED_HOSTS, "lab-fixture.invalid"]):
    client = Client(enforce_csrf_checks=True, HTTP_HOST="lab-fixture.invalid", HTTP_ORIGIN="https://lab-fixture.invalid")
    assert client.get("/api/auth/browser/v1/config", secure=True).status_code == 200
    response = client.post(
        "/api/auth/browser/v1/auth/login",
        json.dumps({"email": user.email, "password": password}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
        secure=True,
    )
    assert response.status_code == 200
    assert client.get(f"/api/lancamentos/{fixture['account']}/", secure=True).status_code == 404
print("fresh_login_ok=True revoked_access_404=True", flush=True)
