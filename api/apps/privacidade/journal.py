"""Authenticated journal client. All calls happen outside a domain transaction."""

import hashlib
import hmac
import json
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from django.conf import settings
from django.db import connection


class JournalIndisponivel(Exception):
    """The result is unknown or cannot be authenticated; do not delete personal data."""


class JournalConflito(JournalIndisponivel):
    pass


def canonico(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _chave(path):
    try:
        value = Path(path).read_bytes().rstrip()
    except OSError:
        raise JournalIndisponivel() from None
    if len(value) < 32:
        raise JournalIndisponivel()
    return value


def _mac(key, prefix, value):
    return hmac.new(key, prefix + value, hashlib.sha256).hexdigest()


def validar_recibo(receipt, requisicao):
    fields = {
        "version",
        "epoch",
        "operation_id",
        "owner_id",
        "kind",
        "fence",
        "prepare_seq",
        "request_digest",
        "seq",
        "record_mac",
        "checkpoint_seq",
        "checkpoint_mac",
        "receipt_key_id",
        "receipt_mac",
    }
    if not isinstance(receipt, dict) or set(receipt) != fields:
        raise JournalIndisponivel()
    if any(receipt.get(k) != v for k, v in requisicao.items()):
        raise JournalIndisponivel()
    if receipt["request_digest"] != hashlib.sha256(canonico(requisicao)).hexdigest():
        raise JournalIndisponivel()
    if (
        type(receipt["seq"]) is not int
        or receipt["seq"] < 1
        or type(receipt["checkpoint_seq"]) is not int
        or receipt["checkpoint_seq"] < receipt["seq"]
        or receipt["receipt_key_id"] != settings.JOURNAL_RECEIPT_KEY_ID
    ):
        raise JournalIndisponivel()
    if requisicao["kind"] != "PREPARE" and receipt["seq"] <= requisicao["prepare_seq"]:
        raise JournalIndisponivel()
    unsigned = {k: v for k, v in receipt.items() if k != "receipt_mac"}
    mac = _mac(
        _chave(settings.JOURNAL_RECEIPT_KEY_FILE), b"varal-journal-receipt-v1\n", canonico(unsigned)
    )
    if not isinstance(receipt["receipt_mac"], str) or not hmac.compare_digest(
        receipt["receipt_mac"], mac
    ):
        raise JournalIndisponivel()
    return receipt


class _SemRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def registrar(operation_id, owner_id, kind, fence, prepare_seq=None):
    if connection.in_atomic_block:
        raise RuntimeError("Journal I/O is forbidden inside a database transaction")
    if kind not in {"PREPARE", "COMMIT", "ABORT"} or type(fence) is not int or fence < 1:
        raise ValueError("Invalid journal operation")
    if (kind == "PREPARE" and prepare_seq is not None) or (
        kind != "PREPARE" and (type(prepare_seq) is not int or prepare_seq < 1)
    ):
        raise ValueError("Invalid prepare sequence")
    body_obj = {
        "version": 1,
        "epoch": str(uuid.UUID(settings.JOURNAL_EPOCH)),
        "operation_id": str(uuid.UUID(str(operation_id))),
        "owner_id": str(uuid.UUID(str(owner_id))),
        "kind": kind,
        "fence": fence,
        "prepare_seq": prepare_seq,
    }
    body = canonico(body_obj)
    digest = hashlib.sha256(body).hexdigest()
    key_id = settings.JOURNAL_CLIENT_KEY_ID
    path = "/v1/records"
    signature = _mac(
        _chave(settings.JOURNAL_CLIENT_KEY_FILE),
        b"",
        f"varal-journal-request-v1\nPOST\n{path}\n{digest}\n{key_id}".encode(),
    )
    request = urllib.request.Request(
        settings.JOURNAL_URL.rstrip("/") + path,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Varal-Key-Id": key_id,
            "X-Varal-Body-SHA256": digest,
            "X-Varal-Signature": signature,
        },
    )
    try:
        with urllib.request.build_opener(_SemRedirect).open(request, timeout=5) as response:
            data = response.read(16385)
            if response.status not in (200, 201) or len(data) > 16384:
                raise JournalIndisponivel()
        result = json.loads(data)
        if not isinstance(result, dict) or set(result) != {"receipt"}:
            raise JournalIndisponivel()
        return validar_recibo(result["receipt"], body_obj)
    except urllib.error.HTTPError as exc:
        if exc.code == 409:
            raise JournalConflito() from None
        raise JournalIndisponivel() from None
    except (OSError, ValueError, KeyError, TypeError):
        raise JournalIndisponivel() from None


def ler_pagina(after, limit=500):
    """Read a canonical page using the separate, read-only restore credential."""
    if connection.in_atomic_block:
        raise RuntimeError("Journal I/O is forbidden inside a database transaction")
    if type(after) is not int or after < 0 or type(limit) is not int or not 1 <= limit <= 500:
        raise ValueError("Invalid journal page")
    path = f"/v1/records?after={after}&limit={limit}"
    digest = hashlib.sha256(b"").hexdigest()
    key_id = settings.JOURNAL_RESTORE_KEY_ID
    signature = _mac(
        _chave(settings.JOURNAL_RESTORE_KEY_FILE),
        b"",
        f"varal-journal-request-v1\nGET\n{path}\n{digest}\n{key_id}".encode(),
    )
    request = urllib.request.Request(
        settings.JOURNAL_URL.rstrip("/") + path,
        method="GET",
        headers={
            "X-Varal-Key-Id": key_id,
            "X-Varal-Body-SHA256": digest,
            "X-Varal-Signature": signature,
        },
    )
    try:
        with urllib.request.build_opener(_SemRedirect).open(request, timeout=5) as response:
            data = response.read(2_500_001)
            if response.status != 200 or len(data) > 2_500_000:
                raise JournalIndisponivel()
        result = json.loads(data)
        if not isinstance(result, dict) or set(result) != {"records", "checkpoint"}:
            raise JournalIndisponivel()
        return result
    except (OSError, ValueError, KeyError, TypeError):
        raise JournalIndisponivel() from None


def verificar_disponibilidade():
    """Authenticated read probe; a missing fixed UUID is the expected healthy answer."""
    if connection.in_atomic_block:
        raise RuntimeError("Journal I/O is forbidden inside a database transaction")
    try:
        uuid.UUID(settings.JOURNAL_EPOCH)
        if not settings.JOURNAL_CLIENT_KEY_ID or not settings.JOURNAL_RECEIPT_KEY_ID:
            raise ValueError
        _chave(settings.JOURNAL_RECEIPT_KEY_FILE)
    except (AttributeError, ValueError, JournalIndisponivel):
        raise JournalIndisponivel() from None
    path = "/v1/operations/00000000-0000-0000-0000-000000000000"
    digest = hashlib.sha256(b"").hexdigest()
    key_id = settings.JOURNAL_CLIENT_KEY_ID
    signature = _mac(
        _chave(settings.JOURNAL_CLIENT_KEY_FILE),
        b"",
        f"varal-journal-request-v1\nGET\n{path}\n{digest}\n{key_id}".encode(),
    )
    request = urllib.request.Request(
        settings.JOURNAL_URL.rstrip("/") + path,
        method="GET",
        headers={
            "X-Varal-Key-Id": key_id,
            "X-Varal-Body-SHA256": digest,
            "X-Varal-Signature": signature,
        },
    )
    try:
        with urllib.request.build_opener(_SemRedirect).open(request, timeout=5) as response:
            if response.status != 200:
                raise JournalIndisponivel()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return
        raise JournalIndisponivel() from None
    except (OSError, ValueError, KeyError, TypeError):
        raise JournalIndisponivel() from None


def ler_fence(nonce):
    """Read fresh fence state with the read-only restore credential, outside B."""
    if connection.in_atomic_block:
        raise RuntimeError("Journal I/O is forbidden inside a database transaction")
    import re

    if not isinstance(nonce, str) or not re.fullmatch(r"[0-9a-f]{64}", nonce):
        raise ValueError("Invalid fence nonce")
    path = f"/v1/fence?nonce={nonce}"
    digest = hashlib.sha256(b"").hexdigest()
    key_id = settings.JOURNAL_RESTORE_KEY_ID
    signature = _mac(
        _chave(settings.JOURNAL_RESTORE_KEY_FILE),
        b"",
        f"varal-journal-request-v1\nGET\n{path}\n{digest}\n{key_id}".encode(),
    )
    request = urllib.request.Request(
        settings.JOURNAL_URL.rstrip("/") + path,
        method="GET",
        headers={
            "X-Varal-Key-Id": key_id,
            "X-Varal-Body-SHA256": digest,
            "X-Varal-Signature": signature,
        },
    )
    try:
        with urllib.request.build_opener(_SemRedirect).open(request, timeout=5) as response:
            data = response.read(16385)
            if response.status != 200 or len(data) > 16384:
                raise JournalIndisponivel()
        result = json.loads(data)
        if not isinstance(result, dict) or set(result) != {"fence", "freshness"}:
            raise JournalIndisponivel()
        return result
    except (OSError, ValueError, TypeError):
        raise JournalIndisponivel() from None
