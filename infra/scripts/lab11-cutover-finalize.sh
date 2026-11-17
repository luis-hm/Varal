#!/usr/bin/env bash
set -euo pipefail
# Recheck both signed gates and current DB under the sealed fence after restart.
base_dir=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
lab=${1:?lab directory required}
case "$lab" in /tmp/varal11-stack.*) ;; *) exit 1 ;; esac
project=$(cat "$lab/project")
[[ "$project" == "$(basename "$lab" | tr '.A-Z' '-a-z')" && "$project" == varal11-stack-* ]] || exit 1
[[ -f "$lab/CA08_GATE_PENDING" || -f "$lab/ACL_GATE_PENDING" ]] || exit 1
read -r id operation < <(python3 - "$lab/ACTIVE_RESTORE" "$project" <<'PY'
import json,re,sys,uuid
d=json.load(open(sys.argv[1]))
if set(d)!={'version','project','restore_id','operation_id','state'} or d['version']!=1 or d['project']!=sys.argv[2] or d['state']!='cutover' or not re.fullmatch(r'[0-9a-f]{32}',d['restore_id']) or str(uuid.UUID(d['operation_id']))!=d['operation_id']: raise SystemExit(1)
print(d['restore_id'],d['operation_id'])
PY
)
exec 9>"$lab/operation.lock"
flock -n 9 || exit 1
[[ $(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d["restore_id"],d["operation_id"])' "$lab/ACTIVE_RESTORE") == "$id $operation" ]] || exit 1
for service in api worker beat edge web ssr; do
    [[ -z $(docker ps -q --filter "label=com.docker.compose.project=$project" --filter "label=com.docker.compose.service=$service") ]] || exit 1
done
[[ $(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Name}}{{end}}{{end}}' "$project-postgres-1") == "${project}_restore_pg_${id}" ]] || exit 1
[[ $(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Name}}{{end}}{{end}}' "$project-storage-1") == "${project}_restore_objects_${id}" ]] || exit 1
for network in "${project}_data" "${project}_journal"; do [[ $(docker network inspect --format '{{.Internal}}' "$network") == true ]] || exit 1; done
pg_ip=$(docker inspect --format "{{(index .NetworkSettings.Networks \"${project}_data\").IPAddress}}" "$project-postgres-1")
[[ "$pg_ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || exit 1
container=
tmp=
cleanup() {
    if [[ -n "$container" ]]; then docker rm -f "$container" >/dev/null 2>&1 || :; fi
    if [[ -n "$tmp" ]]; then rm -f "$tmp"; fi
}
trap cleanup EXIT HUP INT TERM
container=$(docker create --user 0 --network "${project}_data" --env-file "$lab/restore-maintenance.env" -e PYTHONPATH=/app -e VARAL_LAB_FIXTURE=isolated -e VARAL_RESTORE_MODE=1 -e "POSTGRES_HOST=$pg_ip" -e POSTGRES_DB=varal_lab \
 -v "$base_dir/infra/lab/restore-cutover-verify.py:/proof/verify.py:ro" -v "$base_dir/infra/lab/restore-rights-inventory.sql:/proof/rights.sql:ro" -v "$base_dir/infra/lab/restore-acl-inventory.sql:/proof/acl.sql:ro" \
 -v "$lab/restore-proof-$operation.json:/proof/proof.json:ro" -v "$lab/restore-ledger-$operation.json:/proof/ledger.json:ro" -v "$lab/restore-rights-$operation.json:/proof/rights.json:ro" -v "$lab/keys/restore-proof:/proof/key:ro" \
 -v "$lab/keys/restore:/keys/restore:ro" -v "$lab/keys/receipt:/keys/receipt:ro" \
 varal11-api-final:local python /proof/verify.py /proof/proof.json /proof/ledger.json /proof/rights.json /proof/key /proof/rights.sql /proof/acl.sql "$operation")
docker network connect "${project}_journal" "$container"
docker start -a "$container"
docker rm "$container" >/dev/null
container=
epoch=$(sed -n 's/^LAB_JOURNAL_EPOCH=//p' "$lab/lab.env")
fence=$(cat "$lab/restore-fence-id")
umask 077
tmp=$(mktemp "$lab/.cutover-release.XXXXXXXX")
docker exec -i "$project-journal-1" python - "$epoch" "$fence" RELEASE < "$base_dir/infra/lab/journal-fence-control.py" > "$tmp"
mv "$tmp" "$lab/fence-$fence-RELEASE.json"
tmp=
rm -f "$lab/CA08_GATE_PENDING" "$lab/ACL_GATE_PENDING"
python3 - "$lab" <<'PY'
import os,sys
fd=os.open(sys.argv[1],os.O_RDONLY|os.O_DIRECTORY)
try: os.fsync(fd)
finally: os.close(fd)
PY
printf 'Both gates revalidated; fence released and active runtime may start.\n'
