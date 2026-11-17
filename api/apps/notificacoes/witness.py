"""Require an independently archived WAL segment before external delivery."""

import hashlib
import hmac
import json
import re
import time
import uuid
from pathlib import Path

from django.conf import settings
from django.db import connection


class WitnessIndisponivel(Exception):
    pass


def _canonico(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _pares_unicos(pares):
    result = {}
    for key, value in pares:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _validar(raw, segmento, epoch, key):
    if len(raw) > 4096:
        raise WitnessIndisponivel()
    try:
        ack = json.loads(raw, object_pairs_hook=_pares_unicos)
        campos = {
            "version",
            "epoch",
            "segment",
            "timeline",
            "plaintext_sha256",
            "ciphertext_sha256",
            "nonce",
            "key_id",
            "mac",
        }
        if not isinstance(ack, dict) or set(ack) != campos:
            raise ValueError
        if (
            type(ack["version"]) is not int
            or ack["version"] != 1
            or ack["epoch"] != epoch
            or ack["segment"] != segmento
            or ack["timeline"] != segmento[:8]
            or ack["key_id"] != "wal-v1"
            or not re.fullmatch(r"[0-9a-f]{64}", ack["plaintext_sha256"])
            or not re.fullmatch(r"[0-9a-f]{64}", ack["ciphertext_sha256"])
            or not re.fullmatch(r"[0-9a-f]{24}", ack["nonce"])
            or not re.fullmatch(r"[0-9a-f]{64}", ack["mac"])
        ):
            raise ValueError
        unsigned = {name: value for name, value in ack.items() if name != "mac"}
        signature = hmac.new(
            key, b"varal-wal-witness-v1\n" + _canonico(unsigned), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, ack["mac"]):
            raise ValueError
    except (TypeError, ValueError, KeyError, json.JSONDecodeError):
        raise WitnessIndisponivel() from None


def testemunhar():
    if connection.in_atomic_block:
        raise RuntimeError("WAL witness must run outside a transaction and domain barrier")
    if settings.VARAL_RESTORE_MODE:
        raise WitnessIndisponivel()
    try:
        epoch = str(uuid.UUID(settings.VARAL_WAL_WITNESS_EPOCH))
        key = Path(settings.VARAL_WAL_WITNESS_KEY_FILE).read_bytes().rstrip()
        if len(key) < 32:
            raise ValueError
        directory = Path(settings.VARAL_WAL_WITNESS_DIR)
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_current_wal_insert_lsn()")
            lsn = cursor.fetchone()[0]
            cursor.execute("SELECT pg_walfile_name(%s::pg_lsn)", [lsn])
            segmento = cursor.fetchone()[0]
            if not re.fullmatch(r"[0-9A-F]{24}", segmento):
                raise ValueError
            cursor.execute("SELECT pg_switch_wal()")
        limite = time.monotonic() + settings.VARAL_WAL_WITNESS_TIMEOUT
        path = directory / f"{segmento}.ack"
        while True:
            try:
                raw = path.read_bytes()
            except FileNotFoundError:
                if time.monotonic() >= limite:
                    raise WitnessIndisponivel() from None
                time.sleep(0.1)
                continue
            _validar(raw, segmento, epoch, key)
            return
    except WitnessIndisponivel:
        raise
    except Exception:
        raise WitnessIndisponivel() from None
