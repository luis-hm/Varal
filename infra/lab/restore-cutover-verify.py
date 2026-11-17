"""Verify all operation-bound cutover receipts against the quiescent clone."""
import hashlib
import hmac
import json
import os
import secrets
import sys
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()
from django.conf import settings  # noqa: E402
from django.db import connection, transaction  # noqa: E402
from apps.privacidade.journal import _chave, canonico, ler_fence  # noqa: E402
from apps.privacidade.models import ExecucaoRestauracao, MarcaRestauracao  # noqa: E402
from apps.privacidade.restore import validar_fence  # noqa: E402
from apps.solicitacoes.coordenacao import barreira  # noqa: E402

if len(sys.argv) != 8 or os.environ.get("VARAL_LAB_FIXTURE") != "isolated" or not settings.VARAL_RESTORE_MODE:
    raise SystemExit("Isolated restore required")
proof_path, ledger_path, rights_path, key_path, sql_path, acl_path, operation = sys.argv[1:]
key = _chave(key_path)


def verified(path, domain):
    raw = Path(path).read_bytes()
    obj = json.loads(raw)
    if canonico(obj) != raw.strip():
        raise ValueError("noncanonical receipt")
    mac = obj.pop("mac")
    if not hmac.compare_digest(mac, hmac.new(key, domain + canonico(obj), hashlib.sha256).hexdigest()):
        raise ValueError("invalid receipt")
    obj["mac"] = mac
    return obj


proof = verified(proof_path, b"varal-restore-proof-v1\n")
ledger = verified(ledger_path, b"varal-restore-ledger-gate-v1\n")
rights = verified(rights_path, b"varal-restore-rights-gate-v1\n")
if any(item["operation_id"] != operation for item in (proof, ledger, rights)):
    raise ValueError("operation mismatch")
for field in ("epoch", "fence_id", "system_identifier"):
    if proof[field] != ledger[field] or proof[field] != rights[field]:
        raise ValueError("receipt mismatch")
for field in ("watermark_lsn", "wal_checkpoint_seq", "wal_chain_mac"):
    if ledger[field] != rights[field]:
        raise ValueError("watermark mismatch")
nonce = secrets.token_hex(32)
fence = validar_fence(ler_fence(nonce), nonce)
if (fence["epoch"], fence["fence_id"], fence["seq"], fence["record_mac"]) != (
    proof["epoch"], proof["fence_id"], proof["journal_seq"], proof["journal_record_mac"]
):
    raise ValueError("fence mismatch")
ledger_digest = hashlib.sha256(canonico(ledger)).hexdigest()
rights_sql = Path(sql_path).read_text().split("COPY (", 1)[1]
rights_sql = "COPY (" + rights_sql
acl_sql = "COPY (" + Path(acl_path).read_text().split("COPY (", 1)[1]
ledger_sql = """COPY (SELECT 'delivery' AS kind,id::text AS id,notificacao_id::text AS parent,
canal AS binding,estado,tentativas,coalesce(token::text,'') AS token,coalesce(lease_ate::text,'') AS lease
FROM notificacoes_entreganotificacao UNION ALL SELECT 'push',id::text,entrega_id::text,
inscricao_id::text || ':' || geracao::text,estado,tentativas,coalesce(token::text,''),
coalesce(lease_ate::text,'') FROM notificacoes_entregapushdispositivo ORDER BY 1,2) TO STDOUT WITH CSV"""
with transaction.atomic():
    barreira()
    execution = ExecucaoRestauracao.objects.select_for_update().filter(operation_id=operation).first()
    if not execution or not MarcaRestauracao.objects.filter(operation_id=operation).exists():
        raise ValueError("missing restoration execution")
    if str(execution.fence_id) != fence["fence_id"] or execution.journal_seq != fence["seq"] or execution.journal_record_mac != fence["record_mac"]:
        raise ValueError("execution mismatch")
    with connection.cursor() as cursor:
        cursor.execute("SELECT system_identifier::text FROM pg_control_system()")
        if cursor.fetchone()[0] != proof["system_identifier"]:
            raise ValueError("cluster mismatch")
        cursor.execute("SET LOCAL TIME ZONE 'UTC'")
        cursor.execute("SELECT gate_sha256,after_sha256 FROM public.varal_restore_ledger_receipt WHERE operation_id=%s", [operation])
        receipt = cursor.fetchone()
        if not receipt or receipt[0] != ledger_digest:
            raise ValueError("ledger was not consumed")
        digest = hashlib.sha256()
        with cursor.cursor.copy(ledger_sql) as copy:
            for data in copy:
                digest.update(data)
        if digest.hexdigest() != receipt[1]:
            raise ValueError("delivery ledger changed")
        digest = hashlib.sha256()
        with cursor.cursor.copy(rights_sql) as copy:
            for data in copy:
                digest.update(data)
        if digest.hexdigest() != rights["rights_sha256"]:
            raise ValueError("protected rights changed")
        digest = hashlib.sha256()
        with cursor.cursor.copy(acl_sql) as copy:
            for data in copy:
                digest.update(data)
        if digest.hexdigest() != rights["acl_sha256"]:
            raise ValueError("authentication or access state changed")
nonce = secrets.token_hex(32)
if validar_fence(ler_fence(nonce), nonce) != fence:
    raise ValueError("fence changed")
print("cutover_receipts_verified=True", flush=True)
