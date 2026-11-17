#!/usr/bin/env bash
set -euo pipefail
base_dir=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
lab_dir=${1:?pass the laboratory directory}
case "$lab_dir" in /tmp/varal11-stack.*) ;; *) echo 'invalid laboratory directory' >&2; exit 1 ;; esac
[[ -f "$lab_dir/project" && -f "$lab_dir/lab.env" ]] || exit 1
project=$(cat "$lab_dir/project")
expected=$(basename "$lab_dir" | tr '.A-Z' '-a-z')
[[ "$project" == varal11-stack-* && "$project" == "$expected" ]] || exit 1
compose=(docker compose --env-file "$lab_dir/lab.env" -f "$base_dir/infra/lab/compose.yml" -p "$project")
exec 9>"$lab_dir/operation.lock"
flock -n 9 || { echo 'another laboratory operation is running' >&2; exit 1; }
# Separate psql invocations guarantee that this synthetic INSERT has committed before LSN is read.
"${compose[@]}" exec -T postgres sh -c 'PGPASSWORD="$MIGRATE_PASSWORD" psql -q -v ON_ERROR_STOP=1 -h 127.0.0.1 -U "$MIGRATE_USER" -d "$POSTGRES_DB" -c "CREATE TABLE IF NOT EXISTS wal_witness_probe (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY)"' >/dev/null
"${compose[@]}" exec -T postgres sh -c 'PGPASSWORD="$APP_PASSWORD" psql -q -v ON_ERROR_STOP=1 -h 127.0.0.1 -U "$APP_USER" -d "$POSTGRES_DB" -c "INSERT INTO wal_witness_probe DEFAULT VALUES"' >/dev/null
segment=$("${compose[@]}" exec -T postgres sh -c 'PGPASSWORD="$APP_PASSWORD" psql -q -t -A -v ON_ERROR_STOP=1 -h 127.0.0.1 -U "$APP_USER" -d "$POSTGRES_DB" -c "SELECT pg_walfile_name(pg_current_wal_insert_lsn())"')
[[ "$segment" =~ ^[0-9A-F]{24}$ ]] || exit 1
"${compose[@]}" exec -T postgres sh -c 'PGPASSWORD="$APP_PASSWORD" psql -q -t -A -v ON_ERROR_STOP=1 -h 127.0.0.1 -U "$APP_USER" -d "$POSTGRES_DB" -c "SELECT pg_switch_wal()"' >/dev/null
attempt=0
until "${compose[@]}" exec -T wal-archive test -f "/varal/wal-acks/$segment.ack"; do
    attempt=$((attempt + 1))
    if [[ "$attempt" -ge 60 ]]; then echo 'WAL witness timed out' >&2; exit 1; fi
    sleep 1
done
"${compose[@]}" exec -T wal-archive python - "$segment" <<'PY'
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0, '/srv')
from archive import sign
segment=sys.argv[1]
receipt=json.loads((Path('/varal/wal-acks') / (segment+'.ack')).read_bytes())
key=Path('/run/keys/wal-witness').read_bytes().rstrip()
signature=receipt.pop('mac')
assert signature == sign(key, 'varal-wal-witness-v1', receipt)
assert receipt['segment'] == segment and receipt['timeline'] == segment[:8]
ciphertext=(Path('/varal/wal-archive') / (segment+'.gcm')).read_bytes()
assert hashlib.sha256(ciphertext).hexdigest() == receipt['ciphertext_sha256']
PY
printf '%s\n' 'committed PostgreSQL WAL, forced switch, encrypted archive and authenticated witness: ok'
