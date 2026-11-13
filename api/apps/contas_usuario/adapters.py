from dataclasses import dataclass, field
from urllib.parse import urlsplit

from allauth.account.adapter import DefaultAccountAdapter
from allauth.core import context as allauth_context
from allauth.headless.adapter import DefaultHeadlessAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialApp
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.db import transaction
from django.utils.http import url_has_allowed_host_and_scheme

from .tasks import enviar_email


class AccountAdapter(DefaultAccountAdapter):
    def send_mail(self, template_prefix, email, context):
        # Render while request/site context is available; send only after commit.
        request = allauth_context.request
        ctx = {"request": request, "email": email, "current_site": get_current_site(request)}
        ctx.update(context)
        message = self.render_mail(template_prefix, email, ctx)
        payload = (
            message.subject,
            message.body,
            message.from_email,
            list(message.to),
            [list(alternative) for alternative in message.alternatives],
            message.extra_headers,
        )
        transaction.on_commit(lambda: enviar_email.delay(*payload))

    def is_safe_url(self, url):
        try:
            parsed = urlsplit(url)
        except ValueError:
            return False
        if not parsed.netloc:
            return super().is_safe_url(url)
        frontend = urlsplit(settings.FRONTEND_URL)
        return parsed.scheme == frontend.scheme and url_has_allowed_host_and_scheme(
            url, allowed_hosts={frontend.netloc}, require_https=not settings.DEBUG
        )


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def list_apps(self, request, provider=None, client_id=None):
        # Credentials are exclusively settings/env backed, including when a DB
        # SocialApp exists from an earlier/manual admin configuration.
        if provider not in (None, "google"):
            return []
        apps = []
        for config in settings.SOCIALACCOUNT_PROVIDERS["google"].get("APPS", []):
            if client_id and client_id != config["client_id"]:
                continue
            apps.append(SocialApp(provider="google", **config))
        return apps

    @transaction.atomic
    def save_user(self, request, sociallogin, form=None):
        user = sociallogin.user
        user.nome = user.get_full_name()
        return super().save_user(request, sociallogin, form=form)


@dataclass
class UserData:
    id: str = field(
        metadata={"description": "User UUID", "example": "6fd32f1c-6f80-4b01-b491-25aeb00a180e"}
    )
    display: str = field(metadata={"description": "Display name", "example": "Ana"})
    email: str | None = field(metadata={"description": "Email", "example": "ana@example.com"})
    has_usable_password: bool = field(
        metadata={"description": "Password configured", "example": True}
    )


class HeadlessAdapter(DefaultHeadlessAdapter):
    def get_user_dataclass(self):
        # A stable example also makes repeated OpenAPI exports deterministic.
        return UserData

    def user_as_dataclass(self, user):
        return UserData(
            id=str(user.pk),
            display=user.nome or user.get_full_name() or user.email.split("@")[0],
            email=user.email or None,
            has_usable_password=user.has_usable_password(),
        )
