#!/usr/bin/env bash
set -euo pipefail
# Only a sealed, isolated clone may consume a verified ledger gate.
base_dir=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
lab_dir=${1:?lab directory required}
restore_id=${2:?restore volume ID required}
operation=${3:?restore operation UUID required}
case "$lab_dir" in /tmp/varal11-stack.*) ;; *) exit 1 ;; esac
[[ "$restore_id" =~ ^[0-9a-f]{32}$ && "$operation" =~ ^[0-9a-f-]{36}$ ]] || exit 1
project=$(cat "$lab_dir/project")
[[ "$project" == "$(basename "$lab_dir" | tr '.A-Z' '-a-z')" && "$project" == varal11-stack-* ]] || exit 1
exec 9>"$lab_dir/operation.lock"
flock -n 9 || exit 1
for service in api worker beat edge web ssr; do
    [[ -z $(docker ps -q --filter "label=com.docker.compose.project=$project" --filter "label=com.docker.compose.service=$service") ]] || exit 1
done
for role in api worker beat; do
    name="$project-restore-$role-$restore_id"
    if [[ $(docker inspect --format '{{.State.Running}}' "$name" 2>/dev/null || :) == true ]]; then
        echo 'clone entrypoints and workers must remain stopped' >&2
        exit 1
    fi
done
pg="$project-restore-pg-$restore_id"
network="$project-restore-$restore_id"
[[ $(docker inspect --format '{{ index .Config.Labels "varal.restore" }}' "$pg") == "$restore_id" ]] || exit 1
[[ $(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Name}}{{end}}{{end}}' "$pg") == "${project}_restore_pg_${restore_id}" ]] || exit 1
[[ $(docker network inspect --format '{{.Internal}}' "$network") == true ]] || exit 1
pg_ip=$(docker inspect --format "{{(index .NetworkSettings.Networks \"$network\").IPAddress}}" "$pg")
[[ "$pg_ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || exit 1
gate="$lab_dir/restore-ledger-$operation.json"
[[ -f "$gate" && -f "$lab_dir/keys/restore-proof" ]] || exit 1
docker run --rm --user 0 --network "$network" --env-file "$lab_dir/restore-maintenance.env" \
    -e PYTHONPATH=/app -e VARAL_LAB_FIXTURE=isolated -e VARAL_RESTORE_MODE=1 -e "POSTGRES_HOST=$pg_ip" -e POSTGRES_DB=varal_lab \
    -v "$base_dir/infra/lab/restore-ledger-consumer.py:/proof/consumer.py:ro" -v "$gate:/proof/gate.json:ro" \
    -v "$lab_dir/keys/restore-proof:/proof/key:ro" -v "$lab_dir/keys/restore:/keys/restore:ro" -v "$lab_dir/keys/receipt:/keys/receipt:ro" \
    varal11-api-final:local python /proof/consumer.py /proof/gate.json /proof/key "$operation" varal_lab
