"""Discard forwarded client addresses from peers outside the declared proxy boundary."""

import ipaddress

from django.conf import settings


class TrustedProxyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.networks = tuple(
            ipaddress.ip_network(cidr) for cidr in settings.VARAL_TRUSTED_PROXY_CIDRS
        )

    def __call__(self, request):
        try:
            peer = ipaddress.ip_address(request.META.get("REMOTE_ADDR", ""))
            trusted = settings.VARAL_TRUSTED_PROXY_COUNT == 1 and any(
                peer in network for network in self.networks
            )
        except ValueError:
            trusted = False
        if not trusted:
            request.META.pop("HTTP_X_FORWARDED_FOR", None)
            request.META.pop("HTTP_X_FORWARDED_PROTO", None)
            request.META.pop("HTTP_X_FORWARDED_HOST", None)
            request.META.pop("HTTP_FORWARDED", None)
        return self.get_response(request)
