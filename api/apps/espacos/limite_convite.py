"""Atomic RN31 acceptance limit. Keys never contain an IP or user identifier."""

import hashlib
import hmac
import ipaddress
import uuid

import redis
from django.conf import settings
from rest_framework.exceptions import APIException, Throttled


class LimitadorIndisponivel(APIException):
    status_code = 503
    default_detail = "Não foi possível verificar o limite. Tente novamente."


_LUA = """
local now = redis.call('TIME')
local ms = now[1] * 1000 + math.floor(now[2] / 1000)
for i = 1, 2 do
  redis.call('ZREMRANGEBYSCORE', KEYS[i], '-inf', ms - 3600000)
end
for i = 1, 2 do
  if redis.call('ZCARD', KEYS[i]) >= 10 then return 0 end
end
for i = 1, 2 do
  redis.call('ZADD', KEYS[i], ms, ARGV[1])
  redis.call('PEXPIRE', KEYS[i], 3600001)
end
return 1
"""


def endereco(request):
    try:
        remote = ipaddress.ip_address(request.META["REMOTE_ADDR"])
        count = settings.VARAL_TRUSTED_PROXY_COUNT
        redes = [ipaddress.ip_network(s) for s in settings.VARAL_TRUSTED_PROXY_CIDRS]
        trusted = count == 1 and any(remote in network for network in redes)
        if trusted:
            xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
            if "," in xff or not xff:
                raise ValueError
            remote = ipaddress.ip_address(xff.strip())
        if remote.ipv4_mapped if isinstance(remote, ipaddress.IPv6Address) else False:
            remote = remote.ipv4_mapped
        return str(remote)
    except (KeyError, ValueError):
        raise LimitadorIndisponivel() from None


def verificar(request):
    ip = endereco(request)
    secret = settings.SECRET_KEY.encode()

    def chave(tipo, valor):
        digest = hmac.new(secret, f"{tipo}:{valor}".encode(), hashlib.sha256).hexdigest()
        # Tests can isolate their own counters without disabling the real Redis limiter.
        namespace = getattr(settings, "RN31_TEST_NAMESPACE", "") if settings.DEBUG else ""
        return f"varal:rn31:{namespace}:{tipo}:{digest}"

    try:
        client = redis.Redis.from_url(
            settings.CELERY_BROKER_URL, socket_timeout=2, socket_connect_timeout=2
        )
        resultado = client.eval(
            _LUA, 2, chave("ip", ip), chave("usuario", request.user.pk), str(uuid.uuid4())
        )
    except (redis.RedisError, ValueError, TypeError):
        raise LimitadorIndisponivel() from None
    if resultado != 1:
        raise Throttled(wait=3600)
