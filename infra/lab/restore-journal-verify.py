"""Validate a fresh sealed journal and its complete chain in the isolated clone."""
import json
import secrets
import sys
from pathlib import Path

import django

django.setup()
from apps.privacidade.journal import canonico, ler_fence  # noqa: E402
from apps.privacidade.restore import validar_fence, validar_journal  # noqa: E402

raw = Path(sys.argv[1]).read_bytes()
anchor = json.loads(raw)
if canonico(anchor) != raw.strip():
    raise ValueError("invalid anchor")
nonce = secrets.token_hex(32)
fence = validar_fence(ler_fence(nonce), nonce)
_, checkpoint = validar_journal(anchor, com_checkpoint=True)
nonce = secrets.token_hex(32)
if validar_fence(ler_fence(nonce), nonce) != fence:
    raise ValueError("fence changed")
if (fence["seq"], fence["record_mac"]) != (checkpoint["seq"], checkpoint["mac"]):
    raise ValueError("fence and checkpoint differ")
print(json.dumps(fence, sort_keys=True, separators=(",", ":")))
