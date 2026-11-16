"""Django settings for the Varal API. Every environment-specific value comes from env vars."""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
env = os.environ.get

DEBUG = env("DJANGO_DEBUG", "0") == "1"
SECRET_KEY = env("DJANGO_SECRET_KEY") or ("dev-insecure-key" if DEBUG else None)
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY is required when DJANGO_DEBUG is off")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

DOMAIN_APPS = [
    "apps.contas_usuario",
    "apps.espacos",
    "apps.lancamentos",
    "apps.boletos",
    "apps.pagamentos",
    "apps.recorrencias",
    "apps.notificacoes",
]
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.headless",
    *DOMAIN_APPS,
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "varal"),
        "USER": env("POSTGRES_USER", "varal"),
        "PASSWORD": env("POSTGRES_PASSWORD", ""),
        "HOST": env("POSTGRES_HOST", "localhost"),
        "PORT": env("POSTGRES_PORT", "5432"),
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "contas_usuario.Usuario"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

FRONTEND_URL = env("FRONTEND_URL", "http://localhost:3000").rstrip("/")
API_PUBLIC_URL = env("API_PUBLIC_URL", "http://localhost:8000").rstrip("/")
CSRF_TRUSTED_ORIGINS = [FRONTEND_URL]
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

HEADLESS_ONLY = True
HEADLESS_CLIENTS = ["browser"]
HEADLESS_SERVE_SPECIFICATION = True
HEADLESS_ADAPTER = "apps.contas_usuario.adapters.HeadlessAdapter"
HEADLESS_FRONTEND_URLS = {
    "account_confirm_email": f"{FRONTEND_URL}/entrar",
    "account_reset_password": f"{FRONTEND_URL}/recuperar-senha",
    "account_reset_password_from_key": f"{FRONTEND_URL}/recuperar-senha/{{key}}",
    "account_signup": f"{FRONTEND_URL}/criar-conta",
    "socialaccount_login_error": f"{FRONTEND_URL}/entrar/retorno",
}
ACCOUNT_ADAPTER = "apps.contas_usuario.adapters.AccountAdapter"
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*"]
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS = False
ACCOUNT_LOGIN_ON_PASSWORD_RESET = False
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True
ACCOUNT_EMAIL_NOTIFICATIONS = True
# allauth merges this dict over its defaults. Only `make e2e`/CI set the env (many signups from
# one IP); unset keeps allauth's signup limit (20/m/ip) and every other limit.
_signup_rl = env("ACCOUNT_RATE_LIMIT_SIGNUP")
ACCOUNT_RATE_LIMITS = {"signup": _signup_rl} if _signup_rl else {}
SOCIALACCOUNT_ADAPTER = "apps.contas_usuario.adapters.SocialAccountAdapter"
SOCIALACCOUNT_EMAIL_AUTHENTICATION = False
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = False
SOCIALACCOUNT_STORE_TOKENS = False
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "provider_class": "apps.contas_usuario.google.GoogleProvider",
        "SCOPE": ["profile", "email"],
        "OAUTH_PKCE_ENABLED": True,
        "APPS": [
            {
                "client_id": env("GOOGLE_CLIENT_ID", ""),
                "secret": env("GOOGLE_CLIENT_SECRET", ""),
                "key": "",
            }
        ]
        if env("GOOGLE_CLIENT_ID") and env("GOOGLE_CLIENT_SECRET")
        else [],
    }
}
LOGIN_REDIRECT_URL = f"{FRONTEND_URL}/"
ACCOUNT_LOGOUT_REDIRECT_URL = f"{FRONTEND_URL}/entrar"

EMAIL_BACKEND = env("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", "localhost")
EMAIL_PORT = int(env("EMAIL_PORT", "587"))
EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env("EMAIL_USE_TLS", "1") == "1"
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "Varal <nao-responda@varal.local>")

# RNF11: stored in UTC, displayed in America/Fortaleza.
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Fortaleza"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    # Session only: DRF's default also accepts HTTP Basic, which bypasses allauth's
    # login rate limit and CSRF (security review, stage 03).
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    # Scoped throttles key on the user id and live in the default (Redis) cache.
    "DEFAULT_THROTTLE_RATES": {"convite_aceite": "10/hour"},  # RN31
}
SPECTACULAR_SETTINGS = {
    "TITLE": "Varal API",
    "DESCRIPTION": "Contas (boletos e Pix) no espaço pessoal e em grupos familiares.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "DEFAULT_GENERATOR_CLASS": "config.schema.CombinedSchemaGenerator",
    "ENUM_NAME_OVERRIDES": {
        "PapelEnum": "apps.espacos.models.Papel",
        "TipoEspacoEnum": "apps.espacos.models.Espaco.Tipo",
        "TipoInstrumentoEnum": "apps.boletos.models.TipoInstrumento",
    },
}

CELERY_BROKER_URL = env("REDIS_URL", "redis://localhost:6379/0")
CELERY_TIMEZONE = TIME_ZONE
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL", "redis://localhost:6379/0"),
        "KEY_PREFIX": "varal-cache",
    }
}
