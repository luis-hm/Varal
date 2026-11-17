#!/usr/bin/env bash
set -euo pipefail
# Compare protected acceptance state after Collector, before any cutover or worker.
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
network="$project-restore-$restore_id"
storage="$project-restore-storage-$restore_id"
exec 9>"$lab_dir/operation.lock"
flock -n 9 || exit 1
for service in api worker beat edge web ssr; do
    [[ -z $(docker ps -q --filter "label=com.docker.compose.project=$project" --filter "label=com.docker.compose.service=$service") ]] || exit 1
done
[[ $(docker inspect --format '{{ index .Config.Labels "varal.restore" }}' "$clone_pg") == "$restore_id" ]] || exit 1
[[ $(docker inspect --format '{{ index .Config.Labels "varal.restore" }}' "$storage") == "$restore_id" ]] || exit 1
active_id=$(python3 - "$lab_dir/ACTIVE_RESTORE" "$project" <<'PY'
import json,re,sys
d=json.load(open(sys.argv[1]))
if d.get('project')!=sys.argv[2] or d.get('state')!='cutover' or not re.fullmatch(r'[0-9a-f]{32}',d.get('restore_id','')): raise SystemExit(1)
print(d['restore_id'])
PY
)
[[ $(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Name}}{{end}}{{end}}' "$source_pg") == "${project}_restore_pg_${active_id}" ]] || exit 1
[[ $(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Name}}{{end}}{{end}}' "$project-storage-1") == "${project}_restore_objects_${active_id}" ]] || exit 1
[[ $(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Name}}{{end}}{{end}}' "$clone_pg") == "${project}_restore_pg_${restore_id}" ]] || exit 1
[[ $(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Name}}{{end}}{{end}}' "$storage") == "${project}_restore_objects_${restore_id}" ]] || exit 1
[[ $(docker network inspect --format '{{.Internal}}' "$network") == true ]] || exit 1
for pg in "$source_pg" "$clone_pg"; do
    [[ $(docker exec "$pg" psql -U varal_admin -d varal_lab -t -A -v ON_ERROR_STOP=1 -c 'SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()') == 0 ]] || exit 1
    [[ $(docker exec "$pg" psql -U varal_admin -d varal_lab -t -A -v ON_ERROR_STOP=1 -c "SELECT count(*) FROM boletos_tentativacopiapdf WHERE estado IN ('ativa','copiando') OR incerta") == 0 ]] || { echo 'copy writer unresolved; restore remains closed' >&2; exit 1; }
done
umask 077
work=$(mktemp -d "$lab_dir/rights.XXXXXXXX")
trap 'rm -rf "$work"' EXIT HUP INT TERM
for pair in "$source_pg:source" "$clone_pg:clone"; do
    pg=${pair%:*}; name=${pair#*:}
    docker exec -i "$pg" psql -U varal_admin -d varal_lab -q -v ON_ERROR_STOP=1 < "$base_dir/infra/lab/restore-rights-inventory.sql" > "$work/$name"
done
cmp -s "$work/source" "$work/clone" || { echo 'protected acceptance state differs; restore remains closed' >&2; exit 1; }
for pair in "$source_pg:source-acl" "$clone_pg:clone-acl"; do
    pg=${pair%:*}; name=${pair#*:}
    docker exec -i "$pg" psql -U varal_admin -d varal_lab -q -v ON_ERROR_STOP=1 < "$base_dir/infra/lab/restore-acl-inventory.sql" > "$work/$name"
done
cmp -s "$work/source-acl" "$work/clone-acl" || { echo 'authentication or access state differs; restore remains closed' >&2; exit 1; }
source_storage="$project-storage-1"
source_ip=$(docker inspect --format "{{(index .NetworkSettings.Networks \"${project}_data\").IPAddress}}" "$source_storage")
clone_ip=$(docker inspect --format "{{(index .NetworkSettings.Networks \"$network\").IPAddress}}" "$storage")
pg_ip=$(docker inspect --format "{{(index .NetworkSettings.Networks \"$network\").IPAddress}}" "$clone_pg")
for value in "$source_ip" "$clone_ip" "$pg_ip"; do [[ "$value" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || exit 1; done
docker run --rm -i --network "${project}_data" --env-file "$lab_dir/runtime.env" -e "S3_ENDPOINT_URL=http://$source_ip:9000" --entrypoint python varal11-api-final:local - < "$base_dir/infra/lab/s3-manifest.py" > "$work/source-objects"
docker run --rm -i --network "$network" --env-file "$lab_dir/restore-maintenance.env" -e "S3_ENDPOINT_URL=http://$clone_ip:9000" --entrypoint python varal11-api-final:local - < "$base_dir/infra/lab/s3-manifest.py" > "$work/clone-objects"
docker run --rm --network "$network" --env-file "$lab_dir/restore-maintenance.env" -e "POSTGRES_HOST=$pg_ip" -e POSTGRES_DB=varal_lab -e "S3_ENDPOINT_URL=http://$clone_ip:9000" varal11-api-final:local python manage.py exportar_manifesto_restore --operacao "$operation" --isolado > "$work/db"
python3 "$base_dir/infra/lab/restore-object-verify.py" "$work/source-objects" "$work/clone-objects" "$work/db" > "$work/objects"
docker exec -i "$source_pg" psql -U varal_admin -d varal_lab -q -v ON_ERROR_STOP=1 < "$base_dir/infra/lab/restore-rights-inventory.sql" > "$work/source-again"
cmp -s "$work/source" "$work/source-again" || exit 1
docker exec -i "$source_pg" psql -U varal_admin -d varal_lab -q -v ON_ERROR_STOP=1 < "$base_dir/infra/lab/restore-acl-inventory.sql" > "$work/source-acl-again"
cmp -s "$work/source-acl" "$work/source-acl-again" || exit 1
for pg in "$source_pg" "$clone_pg"; do
    [[ $(docker exec "$pg" psql -U varal_admin -d varal_lab -t -A -v ON_ERROR_STOP=1 -c 'SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()') == 0 ]] || exit 1
done
ledger="$lab_dir/restore-ledger-$operation.json"
proof="$lab_dir/restore-proof-$operation.json"
[[ -f "$ledger" && -f "$proof" && -f "$lab_dir/keys/restore-proof" ]] || exit 1
docker run --rm -i --user 0 --network "$network" --env-file "$lab_dir/restore-maintenance.env" -e DJANGO_SETTINGS_MODULE=config.settings \
    -v "$lab_dir/keys/restore:/keys/restore:ro" -v "$lab_dir/keys/chain:/keys/chain:ro" -v "$lab_dir/keys/checkpoint:/keys/checkpoint:ro" -v "$lab_dir/keys/receipt:/keys/receipt:ro" \
    -v "$lab_dir/restore-journal-anchor.json:/proof/anchor:ro" varal11-api-final:local python - /proof/anchor < "$base_dir/infra/lab/restore-journal-verify.py" > "$work/fresh-fence"
python3 - "$work" "$ledger" "$proof" "$lab_dir/keys/restore-proof" "$operation" <<'PY'
import hashlib,hmac,json,sys
from pathlib import Path
work,ledger_path,proof_path,key_path,operation=sys.argv[1:]
canon=lambda obj:json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
key=Path(key_path).read_bytes().rstrip()
def checked(path,domain):
 data=json.loads(Path(path).read_bytes()); mac=data.pop('mac')
 if not hmac.compare_digest(mac,hmac.new(key,domain+canon(data),hashlib.sha256).hexdigest()): raise ValueError('invalid receipt')
 return data
ledger=checked(ledger_path,b'varal-restore-ledger-gate-v1\n'); proof=checked(proof_path,b'varal-restore-proof-v1\n')
if ledger['operation_id']!=operation or proof['operation_id']!=operation or any(ledger[k]!=proof[k] for k in ('epoch','fence_id','system_identifier')): raise ValueError('receipt mismatch')
fence=json.loads((Path(work)/'fresh-fence').read_bytes())
if (fence['fence_id'],fence['epoch'],fence['seq'],fence['record_mac']) != (proof['fence_id'],proof['epoch'],proof['journal_seq'],proof['journal_record_mac']): raise ValueError('fence mismatch')
objects=json.loads((Path(work)/'objects').read_bytes())
gate=dict(version=1,operation_id=operation,epoch=ledger['epoch'],fence_id=ledger['fence_id'],system_identifier=ledger['system_identifier'],watermark_lsn=ledger['watermark_lsn'],wal_checkpoint_seq=ledger['wal_checkpoint_seq'],wal_chain_mac=ledger['wal_chain_mac'],rights_sha256=hashlib.sha256((Path(work)/'source').read_bytes()).hexdigest(),acl_sha256=hashlib.sha256((Path(work)/'source-acl').read_bytes()).hexdigest(),**objects,key_id='restore-proof-v1')
gate['mac']=hmac.new(key,b'varal-restore-rights-gate-v1\n'+canon(gate),hashlib.sha256).hexdigest()
(Path(work)/'gate').write_bytes(canon(gate))
PY
[[ ! -e "$lab_dir/restore-rights-$operation.json" ]] || exit 1
cp "$work/gate" "$lab_dir/restore-rights-$operation.json"
printf 'Protected acceptances, pins and objects match; restore remains closed.\n'
