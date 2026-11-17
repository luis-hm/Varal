#!/bin/sh
set -eu
base_dir=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
lab_dir=${1:?pass the laboratory directory}
case "$lab_dir" in /tmp/varal11-stack.*) ;; *) echo 'invalid laboratory directory' >&2; exit 1 ;; esac
[ -f "$lab_dir/project" ] && [ -f "$lab_dir/lab.env" ] || exit 1
project=$(cat "$lab_dir/project")
expected=$(basename "$lab_dir" | tr '.A-Z' '-a-z')
case "$project" in varal11-stack-*) ;; *) exit 1 ;; esac
[ "$project" = "$expected" ] || exit 1
volume="${project}_wal_acks"
[ "$(docker volume inspect --format '{{ index .Labels "com.docker.compose.project" }}' "$volume")" = "$project" ] || exit 1
exec 9>"$lab_dir/operation.lock"
flock -n 9 || { echo 'another laboratory operation is running' >&2; exit 1; }
tmp_dir=$(mktemp -d "$lab_dir/witness-probe.XXXXXXXX")
trap 'rm -rf "$tmp_dir"' EXIT HUP INT TERM
cp "$base_dir/api/apps/notificacoes/witness.py" "$tmp_dir/witness.py"
printf '%064d\n' 0 > "$tmp_dir/wrong"
chmod 444 "$tmp_dir/witness.py" "$tmp_dir/wrong"
docker run --rm --network "${project}_data" --env-file "$lab_dir/lab.env" --entrypoint python \
    -v "$volume:/run/wal-witness:ro" \
    -v "$lab_dir/keys/wal-witness:/run/keys/witness:ro" \
    -v "$tmp_dir/wrong:/run/keys/wrong:ro" \
    -v "$tmp_dir/witness.py:/probe/witness.py:ro" \
    -v "$base_dir/infra/lab/witness-probe.py:/probe/main.py:ro" \
    varal11-wal-lab:local /probe/main.py
