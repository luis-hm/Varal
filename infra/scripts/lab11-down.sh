#!/bin/sh
set -eu
base_dir=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
lab_dir=${1:?pass the directory printed by lab11-init.sh}
case "$lab_dir" in /tmp/varal11-stack.*) ;; *) echo 'invalid laboratory directory' >&2; exit 1 ;; esac
[ -f "$lab_dir/project" ] && [ -f "$lab_dir/lab.env" ] || exit 1
project=$(cat "$lab_dir/project")
expected=$(basename "$lab_dir" | tr '.A-Z' '-a-z')
case "$project" in varal11-stack-*) ;; *) exit 1 ;; esac
[ "$project" = "$expected" ] || exit 1
exec 9>"$lab_dir/operation.lock"
flock -n 9 || { echo 'another laboratory operation is running' >&2; exit 1; }
[ ! -e "$lab_dir/ACTIVE_RESTORE" ] && [ ! -e "$lab_dir/CUTOVER" ] || { echo 'restored primary active: base compose shutdown forbidden' >&2; exit 1; }
if [ -f "$lab_dir/relay.pid" ]; then
    python3 "$base_dir/infra/scripts/lab11-relay-stop.py" "$lab_dir"
fi
docker compose --env-file "$lab_dir/lab.env" -f "$base_dir/infra/lab/compose.yml" -p "$project" down --remove-orphans
printf 'Laboratory stopped; its volumes and keys are retained: %s\n' "$project"
