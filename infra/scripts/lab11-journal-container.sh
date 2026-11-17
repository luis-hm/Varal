#!/bin/sh
set -eu
base_dir=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
tmp_dir=$(mktemp -d /tmp/varal11-journal.XXXXXXXX)
lab_id=$(basename "$tmp_dir" | tr '.' '-')
net_id=
writer_id=
data_volume=
anchor_volume=
cleanup() {
    if [ -n "$writer_id" ]; then docker rm -f "$writer_id" >/dev/null 2>&1 || :; fi
    if [ -n "$net_id" ]; then docker network rm "$net_id" >/dev/null 2>&1 || :; fi
    for owned_volume in "$data_volume" "$anchor_volume"; do
        if [ -n "$owned_volume" ] && [ "$(docker volume inspect --format '{{ index .Labels "varal.lab" }}' "$owned_volume" 2>/dev/null || :)" = "$lab_id" ]; then
            docker volume rm "$owned_volume" >/dev/null 2>&1 || :
        fi
    done
    rm -rf "$tmp_dir"
}
trap cleanup EXIT HUP INT TERM
mkdir "$tmp_dir/keys"
for name in chain receipt checkpoint writer restore fence; do
    openssl rand -hex 32 > "$tmp_dir/keys/$name"
    chmod 444 "$tmp_dir/keys/$name"
done
epoch=$(python3 -c 'import uuid; print(uuid.uuid4())')
operation=$(python3 -c 'import uuid; print(uuid.uuid4())')
owner=$(python3 -c 'import uuid; print(uuid.uuid4())')
fence_id=$(python3 -c 'import uuid; print(uuid.uuid4())')
if docker volume inspect "$lab_id-data" >/dev/null 2>&1 || docker volume inspect "$lab_id-anchor" >/dev/null 2>&1; then
    printf '%s\n' 'refusing existing lab volume' >&2
    exit 1
fi
data_volume=$(docker volume create --label "varal.lab=$lab_id" "$lab_id-data")
anchor_volume=$(docker volume create --label "varal.lab=$lab_id" "$lab_id-anchor")
for volume in "$data_volume" "$anchor_volume"; do
    test "$(docker volume inspect --format '{{ index .Labels "varal.lab" }}' "$volume")" = "$lab_id" || exit 1
done
net_id=$(docker network create --internal --label "varal.lab=$lab_id" "$lab_id-net")
set -- --directory /varal/journal --checkpoint-directory /varal/checkpoint --epoch "$epoch" --chain-key-file /run/keys/chain --receipt-key-file /run/keys/receipt --checkpoint-key-file /run/keys/checkpoint --writer-key-file /run/keys/writer --restore-key-file /run/keys/restore --fence-key-file /run/keys/fence
docker run --rm --network none -v "$data_volume:/varal/journal" -v "$anchor_volume:/varal/checkpoint" -v "$tmp_dir/keys:/run/keys:ro" varal11-journal-lab:local "$@" --init
writer_id=$(docker run -d --label "varal.lab=$lab_id" --network "$net_id" --network-alias journal -v "$data_volume:/varal/journal" -v "$anchor_volume:/varal/checkpoint" -v "$tmp_dir/keys:/run/keys:ro" varal11-journal-lab:local "$@" --listen 0.0.0.0)
probe() {
    docker run --rm --network "$net_id" -e "LAB_EPOCH=$epoch" -e "LAB_OPERATION=$operation" -e "LAB_OWNER=$owner" -v "$base_dir/infra/lab/journal-probe.py:/probe.py:ro" -v "$tmp_dir/keys:/run/keys:ro" python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b python /probe.py
}
attempt=0
until probe > "$tmp_dir/first.json" 2>/dev/null; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 10 ]; then exit 1; fi
    sleep 1
done
docker restart "$writer_id" >/dev/null
attempt=0
until probe > "$tmp_dir/second.json" 2>/dev/null; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 10 ]; then exit 1; fi
    sleep 1
done
cmp "$tmp_dir/first.json" "$tmp_dir/second.json"
fence_probe() {
    docker run --rm --network "$net_id" -e "LAB_EPOCH=$epoch" -e "LAB_OPERATION=$operation" -e "LAB_OWNER=$owner" -e "LAB_FENCE=$fence_id" -v "$base_dir/infra/lab/journal-fence-probe.py:/probe.py:ro" -v "$tmp_dir/keys:/run/keys:ro" python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b python /probe.py "$1"
}
fence_probe seal
docker restart "$writer_id" >/dev/null
attempt=0
until fence_probe restart 2>/dev/null; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 10 ]; then exit 1; fi
    sleep 1
done
printf '%s\n' 'isolated journal: replay, durable fence, nonce freshness and restricted release: ok'
