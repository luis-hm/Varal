"""Untrusted Web Push credentials and destination validation."""

import base64
import hashlib
import hmac
import ipaddress
import json
import re
import socket
from urllib.parse import unquote, urlsplit

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import ec
from django.conf import settings
from rest_framework.exceptions import APIException, ValidationError


class PushIndisponivel(APIException):
    status_code = 503
    default_detail = "Inscrição de notificações indisponível."


def _fernet():
    key = settings.NOTIFICACOES_STORAGE_KEY
    if not key and settings.DEBUG:
        key = base64.urlsafe_b64encode(
            hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        ).decode()
    if not key:
        raise PushIndisponivel()
    try:
        return Fernet(key.encode())
    except (TypeError, ValueError):
        raise PushIndisponivel() from None


def validar_endpoint(endpoint):
    if not isinstance(endpoint, str) or not 1 <= len(endpoint) <= 2048:
        raise ValidationError({"endpoint": ["Endereço de inscrição inválido."]})
    if (
        not endpoint.isascii()
        or any(ord(c) <= 32 or ord(c) == 127 for c in endpoint)
        or "\\" in endpoint
        or "#" in endpoint
    ):
        raise ValidationError({"endpoint": ["Endereço de inscrição inválido."]})
    try:
        url = urlsplit(endpoint)
        host = url.hostname
        if re.search(r"%(?![0-9A-Fa-f]{2})", endpoint) or any(
            parte in (".", "..") for parte in unquote(url.path).split("/")
        ):
            raise ValueError
        if (
            url.scheme != "https"
            or not host
            or host not in settings.WEBPUSH_ALLOWED_HOSTS
            or url.username is not None
            or url.password is not None
            or url.fragment
            or url.port not in (None, 443)
            or "%" in url.netloc
            or url.netloc.lower() not in (host, f"{host}:443")
        ):
            raise ValueError
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            raise ValueError
    except ValueError:
        raise ValidationError({"endpoint": ["Endereço de inscrição inválido."]}) from None
    return host


def _decodificar(valor, tamanho):
    if not isinstance(valor, str) or not re.fullmatch(r"[A-Za-z0-9_-]+={0,2}", valor):
        raise ValueError
    raw = base64.b64decode(
        valor.rstrip("=") + "=" * (-len(valor.rstrip("=")) % 4), altchars=b"-_", validate=True
    )
    if len(raw) != tamanho:
        raise ValueError
    return raw


def validar_chaves(p256dh, auth):
    try:
        chave = _decodificar(p256dh, 65)
        _decodificar(auth, 16)
        if chave[0] != 4:
            raise ValueError
        ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), chave)
    except (ValueError, TypeError):
        raise ValidationError({"keys": ["Chaves de inscrição inválidas."]}) from None


def cifrar(endpoint, p256dh, auth):
    return _fernet().encrypt(
        json.dumps(
            {"endpoint": endpoint, "keys": {"p256dh": p256dh, "auth": auth}}, separators=(",", ":")
        ).encode()
    )


def decifrar(segredo):
    return json.loads(_fernet().decrypt(bytes(segredo)))


def _identidade_endpoint(endpoint):
    url = urlsplit(endpoint)
    # Normalize equivalent percent-encodings for ownership, without rewriting the sent URL.
    unreserved = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"

    def canonico(match):
        char = chr(int(match.group(1), 16))
        return char if char in unreserved else "%" + match.group(1).upper()

    path = re.sub(r"%([0-9A-Fa-f]{2})", canonico, url.path or "/")
    query = re.sub(r"%([0-9A-Fa-f]{2})", canonico, url.query)
    return "https://" + url.hostname + path + ("?" + query if query else "")


def fingerprint(endpoint):
    # Fixed secret-derived fingerprint permits ownership checks without disclosing endpoint.
    key = settings.NOTIFICACOES_STORAGE_KEY or (settings.SECRET_KEY if settings.DEBUG else "")
    if not key:
        raise PushIndisponivel()
    return hmac.new(
        key.encode(), _identidade_endpoint(endpoint).encode(), hashlib.sha256
    ).hexdigest()


def resolver_publico(host):
    resultados = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    enderecos = {item[4][0] for item in resultados}
    if not enderecos:
        raise ValueError("empty DNS response")
    for endereco in enderecos:
        ip = ipaddress.ip_address(endereco)
        if not ip.is_global or ip.is_multicast or getattr(ip, "ipv4_mapped", None):
            raise ValueError("non-public DNS response")
    return sorted(enderecos)[0]
