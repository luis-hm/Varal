#!/usr/bin/env bash
set -euo pipefail
# Validate synthetic object and ACL on a new restored volume, without publishing a port.
lab_dir=${1:?laboratory directory required}
restore_id=${2:?restore ID required}
case "$lab_dir" in /tmp/varal11-stack.*) ;; *) exit 1 ;; esac
[[ "$restore_id" =~ ^[0-9a-f]{32}$ ]] || exit 1
project=$(cat "$lab_dir/project")
expected=$(basename "$lab_dir" | tr '.A-Z' '-a-z')
[[ "$project" == varal11-stack-* && "$project" == "$expected" ]] || exit 1
volume="${project}_restore_objects_${restore_id}"
[[ $(docker volume inspect --format '{{ index .Labels "varal.restore" }}' "$volume") == "$restore_id" ]] || exit 1
[[ $(docker volume inspect --format '{{ index .Labels "varal.parent" }}' "$volume") == "$project" ]] || exit 1
exec 9>"$lab_dir/operation.lock"
flock -n 9 || { echo 'another laboratory operation is running' >&2; exit 1; }
work=$(mktemp -d "$lab_dir/object-probe.XXXXXXXX")
net_id=
container_id=
cleanup() {
    if [[ -n "$container_id" ]]; then docker rm -f "$container_id" >/dev/null 2>&1 || :; fi
    if [[ -n "$net_id" ]]; then docker network rm "$net_id" >/dev/null 2>&1 || :; fi
    rm -rf "$work"
}
trap cleanup EXIT HUP INT TERM
python3 - "$lab_dir/lab.env" "$work" <<'PY'
import sys
from pathlib import Path
values=dict(line.split('=',1) for line in Path(sys.argv[1]).read_text().splitlines() if '=' in line)
root=Path(sys.argv[2])
(root/'server.env').write_text('MINIO_ROOT_USER='+values['LAB_STORAGE_USER']+'\nMINIO_ROOT_PASSWORD='+values['LAB_STORAGE_PASSWORD']+'\n')
(root/'client.env').write_text('APP_USER='+values['LAB_STORAGE_APP_USER']+'\nAPP_PASSWORD='+values['LAB_STORAGE_APP_PASSWORD']+'\n')
(root/'server.env').chmod(0o600)
(root/'client.env').chmod(0o600)
PY
net_id=$(docker network create --internal --label "varal.restore=$restore_id" "${project}-restore-net-${restore_id}")
image=pgsty/silo:RELEASE.2026-11-12T00-00-00Z@sha256:c20d112390b9a9ce8c11b8af95ad35bcaa62f4759663c09c936cd8d2b511f329
container_id=$(docker run -d --network "$net_id" --network-alias storage --env-file "$work/server.env" -v "$volume:/data" "$image" server /data)
attempt=0
until docker exec "$container_id" curl --fail --silent http://127.0.0.1:9000/minio/health/ready >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    [[ "$attempt" -lt 60 ]] || { echo 'restored storage not ready' >&2; exit 1; }
    sleep 1
done
docker run --rm --network "$net_id" --tmpfs /tmp:mode=0700 --env-file "$work/client.env" --entrypoint sh "$image" -c '
set -eu
export MC_CONFIG_DIR=/tmp/mc
mc alias set app http://storage:9000 "$APP_USER" "$APP_PASSWORD" >/dev/null 2>&1
content=$(mc cat app/varal-lab-private/pitr-probe.pdf)
[ "$content" = synthetic-pitr-document ]
if mc admin info app >/dev/null 2>&1; then exit 1; fi
code=$(curl --silent --output /dev/null --write-out "%{http_code}" http://storage:9000/varal-lab-private/pitr-probe.pdf)
[ "$code" = 403 ]
'
printf '%s\n' 'isolated restored object bytes, private bucket and non-admin access: ok'
