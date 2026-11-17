#!/usr/bin/env bash
set -euo pipefail
base_dir=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
lab_dir=${1:?laboratory directory required}
action=${2:?DRAIN, SEAL or RELEASE required}
fence_id=${3:?fence UUID required}
case "$lab_dir" in /tmp/varal11-stack.*) ;; *) exit 1 ;; esac
[[ "$action" == DRAIN || "$action" == SEAL || "$action" == RELEASE ]] || exit 1
[[ "$fence_id" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]] || exit 1
project=$(cat "$lab_dir/project")
expected=$(basename "$lab_dir" | tr '.A-Z' '-a-z')
[[ "$project" == varal11-stack-* && "$project" == "$expected" ]] || exit 1
compose=(docker compose --env-file "$lab_dir/lab.env" -f "$base_dir/infra/lab/compose.yml" -p "$project")
exec 9>"$lab_dir/operation.lock"
flock -n 9 || { echo 'another laboratory operation is running' >&2; exit 1; }
if [[ "$action" != RELEASE ]]; then
    # There must be no app entrypoint or worker, including one-off compose runs.
    for service in api worker beat edge web ssr; do
        running=$(docker ps -q --filter "label=com.docker.compose.project=$project" --filter "label=com.docker.compose.service=$service")
        [[ -z "$running" ]] || { echo 'source services must be stopped before fencing' >&2; exit 1; }
    done
fi
epoch=$(python3 - "$lab_dir/lab.env" <<'PY'
import sys
with open(sys.argv[1]) as source:
    for line in source:
        if line.startswith('LAB_JOURNAL_EPOCH='):
            print(line.strip().split('=', 1)[1]); break
PY
)
umask 077
receipt_tmp=$(mktemp "$lab_dir/.fence.XXXXXXXX")
trap 'rm -f "$receipt_tmp"' EXIT HUP INT TERM
"${compose[@]}" exec -T journal python - "$epoch" "$fence_id" "$action" < "$base_dir/infra/lab/journal-fence-control.py" > "$receipt_tmp"
mv "$receipt_tmp" "$lab_dir/fence-$fence_id-$action.json"
printf 'Fence transition %s recorded; laboratory remains isolated.\n' "$action"
