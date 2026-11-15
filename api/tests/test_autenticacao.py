import json
import runpy
from datetime import timedelta
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit

import pytest
from allauth.account.models import EmailAddress
from allauth.account.utils import user_pk_to_url_str
from allauth.socialaccount.models import SocialAccount, SocialApp
from django.contrib import admin
from django.core import mail
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import Client
from django.utils import timezone

from apps.contas_usuario.models import Usuario
from apps.espacos.models import Espaco

pytestmark = pytest.mark.django_db(transaction=True)
AUTH = "/api/auth/browser/v1/"
PASSWORD = "Secure-family-pass-726!"


def browser():
    client = Client(enforce_csrf_checks=True)
    assert client.get(AUTH + "config").status_code == 200
    return client


def post(client, route, data):
    return client.post(
        AUTH + route,
        json.dumps(data),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    )


def create_user(email="ana@example.com", **kwargs):
    return Usuario.objects.create_user(
        username=email.split("@")[0], email=email, password=PASSWORD, **kwargs
    )


def login(client, email="ana@example.com", password=PASSWORD):
    return post(client, "auth/login", {"email": email, "password": password})


def test_rf01_rf02_ca01_cadastro_email_sessao_hash_e_dois_usuarios():
    for email in ("ana@example.com", "ana@outra.com"):
        client = browser()
        response = post(client, "auth/signup", {"email": email, "password": PASSWORD})
        assert response.status_code == 200, response.content
        assert response.json()["meta"]["is_authenticated"] is True
        user = Usuario.objects.get(email=email)
        assert user.password != PASSWORD and user.check_password(PASSWORD)
        assert Espaco.objects.filter(dono=user, tipo="pessoal").count() == 1
        assert client.get("/api/me/").json()["id"] == str(user.id)
        assert "username" not in response.json()["data"]["user"]
    assert Usuario.objects.values("username").distinct().count() == 2


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "invalido", "password": PASSWORD},
        {"email": "ana@example.com", "password": "1234"},
        {"email": "ana@example.com", "password": "password"},
    ],
)
def test_rf01_ca02_cadastro_invalido_nao_cria_dados(payload):
    response = post(browser(), "auth/signup", payload)
    assert response.status_code == 400
    assert Usuario.objects.count() == Espaco.objects.count() == 0


def test_rf01_ca02_email_duplicado_independente_de_caixa():
    create_user()
    response = post(browser(), "auth/signup", {"email": "ANA@EXAMPLE.COM", "password": PASSWORD})
    assert response.status_code == 400
    assert Usuario.objects.count() == Espaco.objects.count() == 1


def test_rf01_ca03_login_email_sessao_persiste_e_senha_errada():
    create_user()
    client = browser()
    assert login(client, password="wrong").status_code == 400
    assert client.get(AUTH + "auth/session").status_code == 401
    assert login(client).status_code == 200
    assert client.get(AUTH + "auth/session").json()["meta"]["is_authenticated"]
    assert client.cookies["sessionid"]["httponly"]
    assert client.cookies["sessionid"]["samesite"] == "Lax"


def test_rf01_ca03_usuario_inativo_nao_entra():
    create_user(is_active=False)
    client = browser()
    assert login(client).status_code != 200
    assert client.get("/api/me/").status_code == 403


def test_rn03_ca04_repeticao_e_restricoes_do_banco():
    user = create_user()
    original = Espaco.objects.get(dono=user)
    user.save()
    assert Espaco.objects.get(dono=user).id == original.id
    with pytest.raises(IntegrityError), transaction.atomic():
        Espaco.objects.create(dono=user, tipo="pessoal", nome="Duplicado")
    with pytest.raises(IntegrityError), transaction.atomic():
        Espaco.objects.create(tipo="pessoal", nome="Sem dono")
    with pytest.raises(IntegrityError), transaction.atomic():
        Usuario.objects.create(username="outra", email="ANA@EXAMPLE.COM")
    assert Espaco.objects.filter(dono=user).count() == 1
    assert not any(field.name == "membros" for field in Espaco._meta.fields)


def test_rn03_ca04_erro_espaco_reverte_cadastro():
    client = browser()
    with patch.object(Espaco.objects, "get_or_create", side_effect=RuntimeError("failure")):
        with pytest.raises(RuntimeError):
            post(client, "auth/signup", {"email": "ana@example.com", "password": PASSWORD})
    assert Usuario.objects.count() == Espaco.objects.count() == 0
    assert EmailAddress.objects.count() == 0


def test_rn03_ca05_seed_idempotente_preserva_usuario_e_senha():
    output = StringIO()
    call_command("seed", stdout=output)
    user = Usuario.objects.get(username="dev")
    original = (user.id, user.password, Espaco.objects.get(dono=user).id)
    call_command("seed", stdout=output)
    user.refresh_from_db()
    assert (user.id, user.password, Espaco.objects.get(dono=user).id) == original


def google_settings(settings):
    settings.SOCIALACCOUNT_PROVIDERS = {
        "google": {
            "provider_class": "apps.contas_usuario.google.GoogleProvider",
            "SCOPE": ["profile", "email"],
            "OAUTH_PKCE_ENABLED": True,
            "APPS": [{"client_id": "test-client", "secret": "test-secret", "key": ""}],
        }
    }


def start_google(client):
    response = client.post(
        AUTH + "auth/provider/redirect",
        {
            "provider": "google",
            "process": "login",
            "callback_url": "http://localhost:3000/entrar/retorno",
            "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
        },
        HTTP_HOST="localhost:3000",
        HTTP_ORIGIN="http://localhost:3000",
    )
    assert response.status_code == 302, response.content
    location = urlsplit(response["Location"])
    assert location.netloc == "accounts.google.com"
    query = parse_qs(location.query)
    assert query["redirect_uri"] == ["http://localhost:8000/accounts/google/login/callback/"]
    assert query["code_challenge_method"] == ["S256"]
    return query["state"][0]


def finish_google(client, state, email="google@example.com", uid="google-123"):
    token_response = Mock()
    token_response.json.return_value = {"access_token": "external-test-token"}
    token_response.status_code = 200
    token_response.content = b"{}"
    token_response.headers = {"content-type": "application/json"}
    user_response = Mock()
    user_response.ok = True
    user_response.json.return_value = {
        "id": uid,
        "email": email,
        "verified_email": True,
        "name": "Ana Google",
        "given_name": "Ana",
        "family_name": "Google",
    }
    session = Mock()
    session.request.return_value = token_response
    session.get.return_value = user_response
    session.__enter__ = Mock(return_value=session)
    session.__exit__ = Mock(return_value=False)
    with patch(
        "allauth.socialaccount.adapter.DefaultSocialAccountAdapter.get_requests_session",
        return_value=session,
    ):
        response = client.get(
            "/accounts/google/login/callback/",
            {"state": state, "code": "valid-test-code"},
            HTTP_HOST="localhost:8000",
        )
    return response


def test_rf01_rn03_ca06_google_novo_e_existente_sem_duplicacao(settings):
    google_settings(settings)
    for _ in range(2):
        client = browser()
        response = finish_google(client, start_google(client))
        assert response.status_code == 302, response.content
        assert response["Location"].startswith("http://localhost:3000/entrar/retorno")
        assert client.get(AUTH + "auth/session").status_code == 200
    assert Usuario.objects.count() == Espaco.objects.count() == SocialAccount.objects.count() == 1
    user = Usuario.objects.get()
    assert user.nome == "Ana Google"
    assert not user.has_usable_password()


def test_rf01_ca06_google_nao_vincula_email_local_automaticamente(settings):
    google_settings(settings)
    user = create_user(email="google@example.com")
    client = browser()
    finish_google(client, start_google(client))
    assert client.get(AUTH + "auth/session").status_code == 401
    assert SocialAccount.objects.filter(user=user).count() == 0
    assert Usuario.objects.count() == 1


def test_rf01_ca06_google_cancelado_e_state_invalido(settings):
    google_settings(settings)
    client = browser()
    state = start_google(client)
    response = client.get(
        "/accounts/google/login/callback/", {"state": state, "error": "access_denied"}
    )
    assert response.status_code == 302
    assert "entrar/retorno" in response["Location"]
    response = client.get(
        "/accounts/google/login/callback/", {"state": "invalid", "code": "invalid"}
    )
    assert response.status_code == 302
    assert Usuario.objects.count() == 0


def reset_key(user):
    from allauth.account import app_settings

    token = app_settings.PASSWORD_RESET_TOKEN_GENERATOR().make_token(user)
    return f"{user_pk_to_url_str(user)}-{token}"


def test_rf03_ca07_recuperacao_resposta_generica_email_async(settings):
    user = create_user()
    EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=False)
    client = browser()
    with patch("apps.contas_usuario.tasks.enviar_email.delay") as queued:
        found = post(client, "auth/password/request", {"email": user.email})
        assert found.status_code == 200
        assert queued.call_count == 1
        payload = queued.call_args.args
        assert "http://localhost:3000/recuperar-senha/" in payload[1]
        assert payload[3] == [user.email]
        queued.reset_mock()
        unknown = post(client, "auth/password/request", {"email": "unknown@example.com"})
        assert unknown.status_code == found.status_code
        assert unknown.json() == found.json()
        queued.assert_not_called()
    assert mail.outbox == []


def test_rf03_ca08_token_valido_troca_senha_e_nao_reutiliza():
    user = create_user()
    key = reset_key(user)
    client = browser()
    valid = client.get(AUTH + "auth/password/reset", HTTP_X_PASSWORD_RESET_KEY=key)
    assert valid.status_code == 200, valid.content
    new_password = "Different-long-secret-816!"
    response = post(client, "auth/password/reset", {"key": key, "password": new_password})
    assert response.status_code == 401, response.content
    user.refresh_from_db()
    assert user.check_password(new_password)
    assert login(browser(), password=PASSWORD).status_code == 400
    assert login(browser(), password=new_password).status_code == 200
    assert (
        post(browser(), "auth/password/reset", {"key": key, "password": PASSWORD}).status_code
        == 400
    )


def test_rf03_ca08_token_invalido_expirado_e_senha_fraca(settings):
    user = create_user()
    client = browser()
    assert (
        client.get(AUTH + "auth/password/reset", HTTP_X_PASSWORD_RESET_KEY="bad").status_code == 400
    )
    from allauth.account import app_settings

    generator = app_settings.PASSWORD_RESET_TOKEN_GENERATOR()
    with patch.object(
        type(generator),
        "_now",
        return_value=(timezone.now() - timedelta(days=4)).replace(tzinfo=None),
    ):
        expired = f"{user_pk_to_url_str(user)}-{generator.make_token(user)}"
    assert (
        post(client, "auth/password/reset", {"key": expired, "password": PASSWORD}).status_code
        == 400
    )
    assert (
        post(
            client, "auth/password/reset", {"key": reset_key(user), "password": "1234"}
        ).status_code
        == 400
    )
    user.refresh_from_db()
    assert user.check_password(PASSWORD)


def test_rf01_ca09_logout_invalida_sessao():
    create_user()
    client = browser()
    assert login(client).status_code == 200
    stale_session = client.cookies["sessionid"].value
    response = client.delete(
        AUTH + "auth/session", HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value
    )
    assert response.status_code == 401
    assert client.get("/api/me/").status_code == 403
    client.cookies["sessionid"] = stale_session
    assert client.get("/api/me/").status_code == 403


def test_rnf01_ca10_dados_proprios_sem_vazamento():
    ana = create_user()
    other = create_user(email="bia@example.com", nome="Bia")
    client = browser()
    login(client)
    response = client.get(f"/api/me/?usuario_id={other.id}&dono_id={other.id}")
    payload = response.json()
    assert payload == {
        "id": str(ana.id),
        "nome": "",
        "email": ana.email,
        "espaco_pessoal": {
            "id": str(Espaco.objects.get(dono=ana).id),
            "tipo": "pessoal",
            "nome": "Pessoal",
        },
        "grupos": [],
    }
    assert response["Cache-Control"] == "private, no-store"


def test_rnf02_ca11_csrf_exigido_e_rotacionado():
    create_user()
    client = browser()
    old_csrf = client.cookies["csrftoken"].value
    no_csrf = client.post(
        AUTH + "auth/login",
        json.dumps({"email": "ana@example.com", "password": PASSWORD}),
        content_type="application/json",
    )
    assert no_csrf.status_code == 403
    assert login(client).status_code == 200
    assert client.cookies["csrftoken"].value != old_csrf
    assert client.delete(AUTH + "auth/session").status_code == 403
    assert client.delete(AUTH + "auth/session", HTTP_X_CSRFTOKEN=old_csrf).status_code == 403


def test_rnf02_ca11_configuracao_producao_cookies_e_https(monkeypatch):
    monkeypatch.setenv("DJANGO_DEBUG", "0")
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-production-secret-never-used")
    production = runpy.run_path(str(Path(__file__).parents[1] / "config/settings.py"))
    assert production["SESSION_COOKIE_HTTPONLY"]
    assert production["SESSION_COOKIE_SECURE"] and production["CSRF_COOKIE_SECURE"]
    assert production["SECURE_SSL_REDIRECT"]
    assert production["SESSION_COOKIE_SAMESITE"] == "Lax"


def test_rnf02_ca11_login_limitado_apos_tentativas_incorretas(settings):
    settings.ACCOUNT_RATE_LIMITS = {"login_failed": "2/m/key"}
    create_user()
    client = browser()
    assert login(client, password="wrong").status_code == 400
    assert login(client, password="wrong").status_code == 400
    blocked = login(client)
    assert blocked.status_code in (400, 429)
    assert client.get(AUTH + "auth/session").status_code == 401


def test_rf01_ca12_google_ausente_sem_credenciais_nem_admin(settings):
    google_settings(settings)
    settings.SOCIALACCOUNT_PROVIDERS["google"]["APPS"] = []
    SocialApp.objects.create(
        provider="google", name="Forbidden DB app", client_id="db-client", secret="db-secret"
    )
    client = browser()
    response = client.get(AUTH + "config")
    assert response.json()["data"]["socialaccount"]["providers"] == []
    assert "db-secret" not in response.content.decode()
    assert not admin.site.is_registered(SocialApp)
    response = client.post(
        AUTH + "auth/provider/redirect",
        {
            "provider": "google",
            "process": "login",
            "callback_url": "http://localhost:3000/entrar/retorno",
            "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
        },
    )
    assert response.status_code == 302
    assert "entrar/retorno" in response["Location"]


def test_rnf02_ca11_google_callback_aberto_e_origem_estranha_bloqueados(settings):
    google_settings(settings)
    client = browser()
    response = client.post(
        AUTH + "auth/provider/redirect",
        {
            "provider": "google",
            "process": "login",
            "callback_url": "https://evil.example/phish",
            "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
        },
    )
    assert response.status_code == 302
    assert "evil.example" not in response["Location"]
    response = client.post(
        AUTH + "auth/login",
        json.dumps({"email": "ana@example.com", "password": PASSWORD}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
        HTTP_ORIGIN="https://evil.example",
    )
    assert response.status_code == 403


@pytest.mark.parametrize("callback_url", ["http://[", "http://[::1", "http://[invalid]"])
def test_rnf02_ca11_callback_google_malformado_rejeitado_sem_erro_500(settings, callback_url):
    google_settings(settings)
    client = browser()
    response = client.post(
        AUTH + "auth/provider/redirect",
        {
            "provider": "google",
            "process": "login",
            "callback_url": callback_url,
            "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
        },
    )
    assert response.status_code == 302
    assert response["Location"].startswith("http://localhost:3000/entrar/retorno")


def test_rnf12_ca15_schema_completo_e_deterministico(tmp_path):
    first, second = tmp_path / "first.yaml", tmp_path / "second.yaml"
    call_command("export_schema", file=str(first), stdout=StringIO())
    call_command("export_schema", file=str(second), stdout=StringIO())
    assert first.read_bytes() == second.read_bytes()
    text = first.read_text()
    for path in (
        "/api/me/",
        AUTH + "auth/login",
        AUTH + "auth/password/reset",
        AUTH + "auth/session",
        AUTH + "auth/provider/redirect",
    ):
        assert path in text
    assert "test-secret" not in text
    assert "/api/auth/app/" not in text
