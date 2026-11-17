"""Consume authenticated ledger gate in a dedicated isolated restore clone only.

Run with cloned DB, VARAL_RESTORE_MODE=1 and lab worker/beat/dispatch stopped.
Supervisor must hold the operation flock and keep the journal fence sealed until
cutover. Arguments: gate.json, HMAC key file, expected operation UUID, lab DB name.
Does not release fence, open traffic or contact a delivery transport.
"""
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
import uuid
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.conf import settings
from django.db import connection, transaction
from apps.privacidade.journal import _chave, canonico, ler_fence
from apps.privacidade.models import ExecucaoRestauracao, MarcaRestauracao
from apps.privacidade.restore import validar_fence
from apps.solicitacoes.coordenacao import barreira

if len(sys.argv) != 5:
    raise SystemExit('Expected gate, key, operation UUID and dedicated lab database name')
gate_path, key_path, operation_arg, lab_db = sys.argv[1:]
operation = str(uuid.UUID(operation_arg))
if (os.environ.get('VARAL_LAB_FIXTURE') != 'isolated' or not settings.VARAL_RESTORE_MODE
        or not lab_db or connection.settings_dict['NAME'] != lab_db):
    raise SystemExit('Isolated lab restore mode required')
raw = Path(gate_path).read_bytes()
if len(raw) > 16384:
    raise SystemExit('Invalid ledger gate')
gate = json.loads(raw)
fields = {'version','operation_id','fence_id','epoch','system_identifier','watermark_lsn',
          'ledger_sha256','wal_checkpoint_seq','wal_chain_mac','key_id','mac'}
if not isinstance(gate, dict) or set(gate) != fields or canonico(gate) != raw.strip():
    raise SystemExit('Invalid ledger gate')
key = _chave(key_path)
expected = hmac.new(key, b'varal-restore-ledger-gate-v1\n' +
                    canonico({k:v for k,v in gate.items() if k != 'mac'}), hashlib.sha256).hexdigest()
try:
    valid = (type(gate['version']) is int and gate['version'] == 1
             and gate['operation_id'] == operation and str(uuid.UUID(gate['fence_id'])) == gate['fence_id']
             and str(uuid.UUID(gate['epoch'])) == gate['epoch']
             and gate['epoch'] == str(uuid.UUID(settings.JOURNAL_EPOCH))
             and re.fullmatch(r'[0-9]+', gate['system_identifier'])
             and re.fullmatch(r'[0-9A-F]{1,8}/[0-9A-F]{1,8}', gate['watermark_lsn'])
             and re.fullmatch(r'[0-9a-f]{64}', gate['ledger_sha256'])
             and re.fullmatch(r'[0-9a-f]{64}', gate['wal_chain_mac'])
             and type(gate['wal_checkpoint_seq']) is int and gate['wal_checkpoint_seq'] > 0
             and gate['key_id'] == 'restore-proof-v1'
             and isinstance(gate['mac'], str) and hmac.compare_digest(expected, gate['mac']))
except (ValueError, TypeError, KeyError):
    valid = False
if not valid:
    raise SystemExit('Invalid ledger gate')
nonce = secrets.token_hex(32)
fence = validar_fence(ler_fence(nonce), nonce)
if fence['fence_id'] != gate['fence_id'] or fence['epoch'] != gate['epoch']:
    raise SystemExit('Fence mismatch')
with connection.cursor() as cursor:
    cursor.execute('SELECT system_identifier::text FROM pg_control_system()')
    if cursor.fetchone()[0] != gate['system_identifier']:
        raise SystemExit('Cluster mismatch')
gate_digest = hashlib.sha256(canonico(gate)).hexdigest()
copy_query = """COPY (SELECT 'delivery' AS kind,id::text AS id,notificacao_id::text AS parent,
canal AS binding,estado,tentativas,coalesce(token::text,'') AS token,coalesce(lease_ate::text,'') AS lease
FROM notificacoes_entreganotificacao UNION ALL
SELECT 'push',id::text,entrega_id::text,inscricao_id::text || ':' || geracao::text,estado,tentativas,
coalesce(token::text,''),coalesce(lease_ate::text,'') FROM notificacoes_entregapushdispositivo
ORDER BY 1,2) TO STDOUT WITH CSV"""

def inventory_hash(cursor):
    digest = hashlib.sha256()
    with cursor.cursor.copy(copy_query) as copy:
        for data in copy:
            digest.update(data)
    return digest.hexdigest()

with transaction.atomic():
    barreira()
    execution = ExecucaoRestauracao.objects.select_for_update().filter(operation_id=operation).first()
    if (not execution or not MarcaRestauracao.objects.filter(operation_id=operation).exists()
            or str(execution.fence_id) != fence['fence_id']
            or execution.journal_seq != fence['seq'] or execution.journal_record_mac != fence['record_mac']):
        raise RuntimeError('Reconciliation binding missing')
    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL TIME ZONE 'UTC'")
        cursor.execute('LOCK TABLE notificacoes_entreganotificacao, notificacoes_entregapushdispositivo IN SHARE ROW EXCLUSIVE MODE')
        cursor.execute('CREATE TABLE IF NOT EXISTS public.varal_restore_ledger_receipt '
                       '(operation_id uuid PRIMARY KEY, gate_sha256 char(64) NOT NULL, '
                       'after_sha256 char(64) NOT NULL)')
        cursor.execute('SELECT gate_sha256, after_sha256 FROM public.varal_restore_ledger_receipt '
                       'WHERE operation_id=%s FOR UPDATE', [operation])
        receipt = cursor.fetchone()
        current = inventory_hash(cursor)
        if receipt:
            if receipt != (gate_digest, current):
                raise RuntimeError('Prior conversion does not match the gate or current ledger')
        else:
            if current != gate['ledger_sha256']:
                raise RuntimeError('Cloned ledger changed after comparison')
            cursor.execute("UPDATE notificacoes_entreganotificacao SET estado='incerta', "
                           "resultado='restore_sem_reenvio', token=NULL, lease_ate=NULL WHERE estado='iniciada'")
            cursor.execute("UPDATE notificacoes_entregapushdispositivo SET estado='incerta', "
                           "resultado='restore_sem_reenvio', token=NULL, lease_ate=NULL WHERE estado='iniciada'")
            after = inventory_hash(cursor)
            cursor.execute('INSERT INTO public.varal_restore_ledger_receipt VALUES (%s,%s,%s)',
                           [operation, gate_digest, after])
nonce = secrets.token_hex(32)
if validar_fence(ler_fence(nonce), nonce) != fence:
    raise RuntimeError('Fence changed; dispatch remains closed')
print('ledger_iniciadas_incerta=True dispatch_closed=True', flush=True)
