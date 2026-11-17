#!/usr/bin/env bash
set -euo pipefail
base_dir=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
lab_dir=${1:?laboratory directory required}
action=${2:?config, up-core, up or stop required}
case "$lab_dir" in /tmp/varal11-stack.*) ;; *) exit 1 ;; esac
[[ "$action" == config || "$action" == up-core || "$action" == up || "$action" == stop ]] || exit 1
project=$(cat "$lab_dir/project")
[[ "$project" == "$(basename "$lab_dir" | tr '.A-Z' '-a-z')" && "$project" == varal11-stack-* ]] || exit 1
restore_id=$(python3 - "$lab_dir/ACTIVE_RESTORE" "$project" <<'PY'
import json,re,sys,uuid
data=json.load(open(sys.argv[1]))
if set(data)!={'version','project','restore_id','operation_id','state'} or data['version']!=1 or data['project']!=sys.argv[2] or data['state']!='cutover' or not re.fullmatch(r'[0-9a-f]{32}',data['restore_id']) or str(uuid.UUID(data['operation_id']))!=data['operation_id']: raise SystemExit(1)
print(data['restore_id'])
PY
)
export LAB_ACTIVE_POSTGRES_VOLUME="${project}_restore_pg_${restore_id}"
export LAB_ACTIVE_OBJECTS_VOLUME="${project}_restore_objects_${restore_id}"
export LAB_ACTIVE_STAGING_VOLUME="${project}_restore_staging_${restore_id}"
export LAB_ACTIVE_BEAT_VOLUME="${project}_restore_beat_${restore_id}"
compose=(docker compose --env-file "$lab_dir/lab.env" -f "$base_dir/infra/lab/compose.yml" -f "$base_dir/infra/lab/compose.active-restore.yml" -p "$project")
if [[ "$action" == config ]]; then
    "${compose[@]}" config --quiet
    exit
fi
exec 9>"$lab_dir/operation.lock"
flock -n 9 || exit 1
[[ $(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["restore_id"])' "$lab_dir/ACTIVE_RESTORE") == "$restore_id" ]] || { echo 'active restore changed during lock acquisition' >&2; exit 1; }
for volume in "$LAB_ACTIVE_POSTGRES_VOLUME" "$LAB_ACTIVE_OBJECTS_VOLUME" "$LAB_ACTIVE_STAGING_VOLUME"; do
    [[ $(docker volume inspect --format '{{ index .Labels "varal.restore" }}' "$volume") == "$restore_id" ]] || exit 1
    [[ $(docker volume inspect --format '{{ index .Labels "varal.parent" }}' "$volume") == "$project" ]] || exit 1
done
if [[ "$action" == up || "$action" == up-core ]]; then
    for role in pg storage api worker beat; do
        name="$project-restore-$role-$restore_id"
        [[ $(docker inspect --format '{{.State.Running}}' "$name" 2>/dev/null || :) != true ]] || { echo 'manual clone must be stopped first' >&2; exit 1; }
    done
    if [[ "$action" == up-core ]]; then
        "${compose[@]}" up --no-build -d postgres redis storage wal-archive journal smtp-capture
    else
        [[ ! -e "$lab_dir/CA08_GATE_PENDING" && ! -e "$lab_dir/ACL_GATE_PENDING" ]] || { echo 'restore gate pending: public runtime forbidden' >&2; exit 1; }
        "${compose[@]}" up --no-build -d
        edge_id=$(docker inspect --format '{{.Id}}' "$project-edge-1")
        if [[ -f "$lab_dir/relay.pid" ]]; then
            stored_id=$(sed -n '2p' "$lab_dir/relay.pid")
            pid=$(sed -n '1p' "$lab_dir/relay.pid")
            [[ "$pid" =~ ^[0-9]+$ ]] || exit 1
            if [[ "$stored_id" != "$edge_id" || ! -d "/proc/$pid" ]] || ! python3 - "$pid" "$edge_id" <<'PY'
from pathlib import Path
import sys
cmd=Path('/proc',sys.argv[1],'cmdline').read_bytes().split(b'\0')
if not any(Path(x.decode(errors='ignore')).name=='lab11-loopback.py' for x in cmd) or sys.argv[2].encode() not in cmd: raise SystemExit(1)
PY
            then
                python3 "$base_dir/infra/scripts/lab11-relay-stop.py" "$lab_dir"
            fi
        fi
        if [[ ! -f "$lab_dir/relay.pid" ]]; then
            python3 "$base_dir/infra/scripts/lab11-relay-start.py" "$lab_dir"
        fi
    fi
else
    [[ $(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Name}}{{end}}{{end}}' "$project-postgres-1") == "$LAB_ACTIVE_POSTGRES_VOLUME" ]] || { echo 'active compose primary is not running' >&2; exit 1; }
    if [[ -f "$lab_dir/relay.pid" ]]; then
        python3 "$base_dir/infra/scripts/lab11-relay-stop.py" "$lab_dir"
    fi
    "${compose[@]}" stop
fi
