from allauth.socialaccount.providers.google.provider import GoogleProvider as BaseGoogleProvider
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter as BaseGoogleAdapter
from allauth.socialaccount.providers.oauth2.views import OAuth2CallbackView
from django.conf import settings


class GoogleOAuth2Adapter(BaseGoogleAdapter):
    def get_callback_url(self, request, app):
        # The browser starts through the Next proxy, whose host/port is different.
        return f"{settings.API_PUBLIC_URL}/accounts/google/login/callback/"


class GoogleProvider(BaseGoogleProvider):
    oauth2_adapter_class = GoogleOAuth2Adapter

    @classmethod
    def get_package(cls):
        return "allauth.socialaccount.providers.google"


callback = OAuth2CallbackView.adapter_view(GoogleOAuth2Adapter)
