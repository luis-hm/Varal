#!/bin/sh
set -eu
base_dir=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
lab_dir=${1:?pass the directory printed by lab11-init.sh}
case "$lab_dir" in /tmp/varal11-stack.*) ;; *) echo 'invalid laboratory directory' >&2; exit 1 ;; esac
[ -f "$lab_dir/project" ] && [ -f "$lab_dir/lab.env" ] || exit 1
project=$(cat "$lab_dir/project")
case "$project" in varal11-stack-*) ;; *) echo 'invalid laboratory project' >&2; exit 1 ;; esac
expected=$(basename "$lab_dir" | tr '.A-Z' '-a-z')
[ "$project" = "$expected" ] || exit 1
exec 9>"$lab_dir/operation.lock"
flock -n 9 || { echo 'another laboratory operation is running' >&2; exit 1; }
[ ! -e "$lab_dir/ACTIVE_RESTORE" ] && [ ! -e "$lab_dir/CUTOVER" ] || { echo 'restored primary active: base compose startup forbidden' >&2; exit 1; }
compose_file="$base_dir/infra/lab/compose.yml"
docker compose --env-file "$lab_dir/lab.env" -f "$compose_file" -p "$project" config --quiet
docker compose --env-file "$lab_dir/lab.env" -f "$compose_file" -p "$project" up --no-build -d
printf 'Laboratory started: %s\n' "$project"
