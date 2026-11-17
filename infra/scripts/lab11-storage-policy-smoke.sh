#!/bin/sh
set -eu
base_dir=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
tmp_dir=$(mktemp -d /tmp/varal11-storage.XXXXXXXX)
lab_id=$(basename "$tmp_dir" | tr '.' '-')
net_id=
storage_id=
cleanup() {
    if [ -n "$storage_id" ]; then docker rm -f "$storage_id" >/dev/null 2>&1 || :; fi
    if [ -n "$net_id" ]; then docker network rm "$net_id" >/dev/null 2>&1 || :; fi
    rm -rf "$tmp_dir"
}
trap cleanup EXIT HUP INT TERM
docker build -t varal11-storage-init-lab:local -f "$base_dir/infra/lab/storage-init.Dockerfile" "$base_dir/infra/lab" >/dev/null
net_id=$(docker network create --internal --label "varal.lab=$lab_id" "$lab_id-net")
storage_id=$(docker run -d --label "varal.lab=$lab_id" --network "$net_id" --network-alias storage --tmpfs /data -e MINIO_ROOT_USER=synthetic-root -e MINIO_ROOT_PASSWORD=synthetic-root-password pgsty/silo:RELEASE.2026-11-12T00-00-00Z@sha256:c20d112390b9a9ce8c11b8af95ad35bcaa62f4759663c09c936cd8d2b511f329 server /data)
attempt=0
until docker exec "$storage_id" curl --fail --silent http://127.0.0.1:9000/minio/health/ready >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 30 ]; then echo 'storage readiness failed' >&2; exit 1; fi
    sleep 1
done
docker run --rm --network "$net_id" --tmpfs /tmp:mode=0700 -e STORAGE_ADMIN_USER=synthetic-root -e STORAGE_ADMIN_PASSWORD=synthetic-root-password -e STORAGE_APP_USER=synthetic-app -e STORAGE_APP_PASSWORD=synthetic-app-password varal11-storage-init-lab:local
docker run --rm --network "$net_id" --tmpfs /tmp:mode=0700 -e STORAGE_ADMIN_USER=synthetic-root -e STORAGE_ADMIN_PASSWORD=synthetic-root-password -e STORAGE_APP_USER=synthetic-app -e STORAGE_APP_PASSWORD=synthetic-app-password varal11-storage-init-lab:local
docker run --rm --network "$net_id" --tmpfs /tmp:mode=0700 --entrypoint sh pgsty/silo:RELEASE.2026-11-12T00-00-00Z@sha256:c20d112390b9a9ce8c11b8af95ad35bcaa62f4759663c09c936cd8d2b511f329 -c '
set -eu
export MC_CONFIG_DIR=/tmp/mc
mc alias set app http://storage:9000 synthetic-app synthetic-app-password >/dev/null 2>&1
mc ls app/varal-lab-private >/dev/null 2>&1
printf synthetic > /tmp/probe
mc cp /tmp/probe app/varal-lab-private/synthetic-probe >/dev/null 2>&1
result=$(mc cat app/varal-lab-private/synthetic-probe)
[ "$result" = synthetic ]
mc rm app/varal-lab-private/synthetic-probe >/dev/null 2>&1
if mc admin info app >/dev/null 2>&1; then exit 1; fi
if mc mb app/unauthorized-bucket >/dev/null 2>&1; then exit 1; fi
'
printf '%s\n' 'private S3 bucket and non-admin application policy: ok'
