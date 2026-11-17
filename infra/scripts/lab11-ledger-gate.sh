#!/usr/bin/env bash
set -euo pipefail
# Laboratory-only cutover gate: compare complete authoritative delivery state before dispatch.
base_dir=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
lab_dir=${1:?lab directory required}
restore_id=${2:?restore volume ID required}
operation=${3:?restore operation UUID required}
case "$lab_dir" in /tmp/varal11-stack.*) ;; *) exit 1 ;; esac
[[ "$restore_id" =~ ^[0-9a-f]{32}$ && "$operation" =~ ^[0-9a-f-]{36}$ ]] || exit 1
project=$(cat "$lab_dir/project")
[[ "$project" == "$(basename "$lab_dir" | tr '.A-Z' '-a-z')" && "$project" == varal11-stack-* ]] || exit 1
source_pg="$project-postgres-1"
clone_pg="$project-restore-pg-$restore_id"
[[ $(docker inspect --format '{{ index .Config.Labels "com.docker.compose.project" }}' "$source_pg") == "$project" ]] || exit 1
if [[ -f "$lab_dir/ACTIVE_RESTORE" ]]; then
    active_id=$(python3 - "$lab_dir/ACTIVE_RESTORE" "$project" <<'PY'
import json,re,sys
d=json.load(open(sys.argv[1]))
if d.get('project')!=sys.argv[2] or d.get('state')!='cutover' or not re.fullmatch(r'[0-9a-f]{32}',d.get('restore_id','')): raise SystemExit(1)
print(d['restore_id'])
PY
)
    [[ $(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Name}}{{end}}{{end}}' "$source_pg") == "${project}_restore_pg_${active_id}" ]] || exit 1
fi
[[ $(docker inspect --format '{{ index .Config.Labels "varal.restore" }}' "$clone_pg") == "$restore_id" ]] || exit 1
[[ $(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Name}}{{end}}{{end}}' "$clone_pg") == "${project}_restore_pg_${restore_id}" ]] || exit 1
exec 9>"$lab_dir/operation.lock"
flock -n 9 || exit 1
if [[ -n "${active_id:-}" ]]; then
    [[ $(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["restore_id"])' "$lab_dir/ACTIVE_RESTORE") == "$active_id" ]] || exit 1
fi
for service in api worker beat edge web ssr; do
    [[ -z $(docker ps -q --filter "label=com.docker.compose.project=$project" --filter "label=com.docker.compose.service=$service") ]] || exit 1
done
[[ $(docker exec "$source_pg" psql -U varal_admin -d varal_lab -t -A -v ON_ERROR_STOP=1 -c 'SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()') == 0 ]] || exit 1
umask 077
work=$(mktemp -d "$lab_dir/ledger.XXXXXXXX")
trap 'rm -rf "$work"' EXIT HUP INT TERM
query="COPY (SELECT 'delivery' AS kind,id::text AS id,notificacao_id::text AS parent,canal AS binding,estado,tentativas,coalesce(token::text,'') AS token,coalesce(lease_ate::text,'') AS lease FROM notificacoes_entreganotificacao UNION ALL SELECT 'push',id::text,entrega_id::text,inscricao_id::text || ':' || geracao::text,estado,tentativas,coalesce(token::text,''),coalesce(lease_ate::text,'') FROM notificacoes_entregapushdispositivo ORDER BY 1,2) TO STDOUT WITH CSV"
inventory() { docker exec "$1" psql -U varal_admin -d varal_lab -q -v ON_ERROR_STOP=1 -c "SET TIME ZONE 'UTC'; $query"; }
inventory "$source_pg" > "$work/source"
inventory "$clone_pg" > "$work/clone"
cmp -s "$work/source" "$work/clone" || { echo 'delivery ledger differs; dispatch remains closed' >&2; exit 1; }
source_id=$(docker exec "$source_pg" psql -U varal_admin -d varal_lab -t -A -v ON_ERROR_STOP=1 -c 'SELECT system_identifier::text FROM pg_control_system()')
clone_id=$(docker exec "$clone_pg" psql -U varal_admin -d varal_lab -t -A -v ON_ERROR_STOP=1 -c 'SELECT system_identifier::text FROM pg_control_system()')
[[ "$source_id" =~ ^[0-9]+$ && "$source_id" == "$clone_id" ]] || exit 1
# Force a real WAL record: pg_switch_wal is a no-op on an otherwise empty segment.
docker exec "$source_pg" psql -U varal_admin -d varal_lab -q -v ON_ERROR_STOP=1 -c "SELECT pg_create_restore_point('varal_lab_ledger')" >/dev/null
watermark=$(docker exec "$source_pg" psql -U varal_admin -d varal_lab -t -A -v ON_ERROR_STOP=1 -c 'SELECT pg_current_wal_insert_lsn()::text')
[[ "$watermark" =~ ^[0-9A-F]+/[0-9A-F]+$ ]] || exit 1
segment=$(docker exec "$source_pg" psql -U varal_admin -d varal_lab -t -A -v ON_ERROR_STOP=1 -c "SELECT pg_walfile_name('$watermark'::pg_lsn)")
[[ "$segment" =~ ^[0-9A-F]{24}$ ]] || exit 1
docker exec "$source_pg" psql -U varal_admin -d varal_lab -q -v ON_ERROR_STOP=1 -c 'SELECT pg_switch_wal()' >/dev/null
for attempt in $(seq 1 120); do
    docker exec "$source_pg" test -f "/varal/wal-acks/$segment.ack" && break
    [[ "$attempt" -lt 120 ]] || exit 1
    sleep 1
done
epoch=$(sed -n 's/^LAB_JOURNAL_EPOCH=//p' "$lab_dir/lab.env")
docker run --rm --network none --entrypoint python -v "${project}_wal_archive:/varal/wal-archive:ro" -v "${project}_wal_anchor:/varal/wal-anchor:ro" \
    -v "$lab_dir/keys/wal-cipher:/run/keys/cipher:ro" -v "$lab_dir/keys/wal-witness:/run/keys/witness:ro" \
    -v "$base_dir/infra/wal/attest-range.py:/srv/attest-range.py:ro" varal11-wal-lab:local /srv/attest-range.py \
    /varal/wal-archive /varal/wal-anchor "$epoch" "$source_id" /run/keys/cipher /run/keys/witness "$segment" "$segment" > "$work/wal"
inventory "$source_pg" > "$work/source-again"
cmp -s "$work/source" "$work/source-again" || exit 1
[[ $(docker exec "$source_pg" psql -U varal_admin -d varal_lab -t -A -v ON_ERROR_STOP=1 -c 'SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()') == 0 ]] || exit 1
proof="$lab_dir/restore-proof-$operation.json"
fence_file="$lab_dir/fence-$(cat "$lab_dir/restore-fence-id")-SEAL.json"
[[ -f "$proof" && -f "$fence_file" && -f "$lab_dir/keys/restore-proof" ]] || exit 1
network="$project-restore-$restore_id"
docker run --rm -i --user 0 --network "$network" --env-file "$lab_dir/restore-maintenance.env" -e DJANGO_SETTINGS_MODULE=config.settings \
    -v "$lab_dir/keys/restore:/keys/restore:ro" -v "$lab_dir/keys/chain:/keys/chain:ro" \
    -v "$lab_dir/keys/checkpoint:/keys/checkpoint:ro" -v "$lab_dir/keys/receipt:/keys/receipt:ro" \
    -v "$lab_dir/restore-journal-anchor.json:/proof/anchor:ro" varal11-api-final:local \
    python - /proof/anchor < "$base_dir/infra/lab/restore-journal-verify.py" > "$work/fresh-fence"
python3 - "$fence_file" "$work/fresh-fence" <<'PY'
import json, sys
from pathlib import Path
if json.loads(Path(sys.argv[1]).read_bytes()) != json.loads(Path(sys.argv[2]).read_bytes()): raise ValueError('fence changed')
PY
python3 - "$work" "$proof" "$fence_file" "$lab_dir/keys/restore-proof" "$operation" "$watermark" "$source_id" <<'PY'
import hashlib, hmac, json, sys
from pathlib import Path
work, proof_file, fence_file, key_file, operation, watermark, system_id = sys.argv[1:]
canonical=lambda obj: json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
key=Path(key_file).read_bytes().rstrip()
proof=json.loads(Path(proof_file).read_bytes())
mac=proof.pop('mac')
if not hmac.compare_digest(mac,hmac.new(key,b'varal-restore-proof-v1\n'+canonical(proof),hashlib.sha256).hexdigest()): raise ValueError('invalid proof')
fence=json.loads(Path(fence_file).read_bytes())
if proof['operation_id'] != operation or proof['system_identifier'] != system_id or (proof['fence_id'],proof['journal_seq'],proof['journal_record_mac']) != (fence['fence_id'],fence['seq'],fence['record_mac']): raise ValueError('wrong proof or fence')
wal=json.loads((Path(work)/'wal').read_bytes())
gate=dict(version=1,operation_id=operation,fence_id=fence['fence_id'],epoch=fence['epoch'],system_identifier=system_id,watermark_lsn=watermark,ledger_sha256=hashlib.sha256((Path(work)/'source').read_bytes()).hexdigest(),wal_checkpoint_seq=wal['sequence'],wal_chain_mac=wal['chain_mac'],key_id='restore-proof-v1')
gate['mac']=hmac.new(key,b'varal-restore-ledger-gate-v1\n'+canonical(gate),hashlib.sha256).hexdigest()
(Path(work)/'gate.json').write_bytes(canonical(gate))
PY
[[ ! -e "$lab_dir/restore-ledger-$operation.json" ]] || exit 1
cp "$work/gate.json" "$lab_dir/restore-ledger-$operation.json"
printf 'Source and clone complete delivery ledgers match; watermark independently archived. Dispatch remains closed.\n'
