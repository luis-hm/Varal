#!/usr/bin/env bash
set -euo pipefail
# Verify all receipts in the live sealed clone before changing the active volume pointer.
base_dir=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
lab=${1:?lab directory required}
id=${2:?restore ID required}
operation=${3:?operation UUID required}
case "$lab" in /tmp/varal11-stack.*) ;; *) exit 1 ;; esac
[[ "$id" =~ ^[0-9a-f]{32}$ && "$operation" =~ ^[0-9a-f-]{36}$ ]] || exit 1
[[ -f "$lab/CA08_GATE_PENDING" || -f "$lab/ACL_GATE_PENDING" ]] || exit 1
project=$(cat "$lab/project")
[[ "$project" == "$(basename "$lab" | tr '.A-Z' '-a-z')" && "$project" == varal11-stack-* ]] || exit 1
network="$project-restore-$id"
clone_pg="$project-restore-pg-$id"
clone_storage="$project-restore-storage-$id"
exec 9>"$lab/operation.lock"
flock -n 9 || exit 1
for service in api worker beat edge web ssr; do
    [[ -z $(docker ps -q --filter "label=com.docker.compose.project=$project" --filter "label=com.docker.compose.service=$service") ]] || exit 1
done
source_id=$(python3 - "$lab/ACTIVE_RESTORE" "$project" <<'PY'
import json,re,sys
d=json.load(open(sys.argv[1]))
if d.get('project')!=sys.argv[2] or d.get('state')!='cutover' or not re.fullmatch(r'[0-9a-f]{32}',d.get('restore_id','')): raise SystemExit(1)
print(d['restore_id'])
PY
)
[[ "$source_id" != "$id" ]] || exit 1
[[ $(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Name}}{{end}}{{end}}' "$project-postgres-1") == "${project}_restore_pg_${source_id}" ]] || exit 1
[[ $(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Name}}{{end}}{{end}}' "$project-storage-1") == "${project}_restore_objects_${source_id}" ]] || exit 1
for role in api worker beat; do
    [[ $(docker inspect --format '{{.State.Running}}' "$project-restore-$role-$id" 2>/dev/null || :) != true ]] || exit 1
done
for name in "$clone_pg" "$clone_storage"; do
    [[ $(docker inspect --format '{{ index .Config.Labels "varal.restore" }}' "$name") == "$id" ]] || exit 1
done
[[ $(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Name}}{{end}}{{end}}' "$clone_pg") == "${project}_restore_pg_${id}" ]] || exit 1
[[ $(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Name}}{{end}}{{end}}' "$clone_storage") == "${project}_restore_objects_${id}" ]] || exit 1
[[ $(docker network inspect --format '{{.Internal}}' "$network") == true ]] || exit 1
pg_ip=$(docker inspect --format "{{(index .NetworkSettings.Networks \"$network\").IPAddress}}" "$clone_pg")
[[ "$pg_ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || exit 1
docker run --rm --user 0 --network "$network" --env-file "$lab/restore-maintenance.env" -e PYTHONPATH=/app -e VARAL_LAB_FIXTURE=isolated -e VARAL_RESTORE_MODE=1 -e "POSTGRES_HOST=$pg_ip" -e POSTGRES_DB=varal_lab \
 -v "$base_dir/infra/lab/restore-cutover-verify.py:/proof/verify.py:ro" -v "$base_dir/infra/lab/restore-rights-inventory.sql:/proof/rights.sql:ro" -v "$base_dir/infra/lab/restore-acl-inventory.sql:/proof/acl.sql:ro" \
 -v "$lab/restore-proof-$operation.json:/proof/proof.json:ro" -v "$lab/restore-ledger-$operation.json:/proof/ledger.json:ro" -v "$lab/restore-rights-$operation.json:/proof/rights.json:ro" -v "$lab/keys/restore-proof:/proof/key:ro" \
 -v "$lab/keys/restore:/keys/restore:ro" -v "$lab/keys/receipt:/keys/receipt:ro" \
 varal11-api-final:local python /proof/verify.py /proof/proof.json /proof/ledger.json /proof/rights.json /proof/key /proof/rights.sql /proof/acl.sql "$operation"
staging="${project}_restore_staging_${id}"
if docker volume inspect "$staging" >/dev/null 2>&1; then echo 'staging volume already exists' >&2; exit 1; fi
docker volume create --label "varal.restore=$id" --label "varal.parent=$project" "$staging" >/dev/null
# The source and clone are both network-isolated; stop them before moving the pointer.
docker stop --timeout 30 "$project-postgres-1" "$project-storage-1" "$clone_pg" "$clone_storage" >/dev/null
docker rm "$clone_pg" "$clone_storage" >/dev/null
python3 - "$lab" "$project" "$id" "$operation" <<'PY'
import json,os,sys,tempfile
from pathlib import Path
lab=Path(sys.argv[1])
data={'version':1,'project':sys.argv[2],'restore_id':sys.argv[3],'operation_id':sys.argv[4],'state':'cutover'}
fd,path=tempfile.mkstemp(prefix='.active-',dir=lab)
with os.fdopen(fd,'w') as f:
 json.dump(data,f,sort_keys=True,separators=(',',':')); f.write('\n'); f.flush(); os.fsync(f.fileno())
os.replace(path,lab/'ACTIVE_RESTORE')
fd=os.open(lab,os.O_RDONLY|os.O_DIRECTORY)
try: os.fsync(fd)
finally: os.close(fd)
PY
printf 'Cutover pointer changed after all gates; public runtime remains closed.\n'
