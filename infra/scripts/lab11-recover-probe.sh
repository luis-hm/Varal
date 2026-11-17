#!/usr/bin/env bash
set -euo pipefail
# Synthetic PITR proof only. No ports, workers, dispatch, or user traffic.
lab_dir=${1:?laboratory directory required}
restore_id=${2:?restore ID required}
target_lsn=${3:?target LSN required}
case "$lab_dir" in /tmp/varal11-stack.*) ;; *) exit 1 ;; esac
[[ "$restore_id" =~ ^[0-9a-f]{32}$ && "$target_lsn" =~ ^[0-9A-F]+/[0-9A-F]+$ ]] || exit 1
project=$(cat "$lab_dir/project")
expected=$(basename "$lab_dir" | tr '.A-Z' '-a-z')
[[ "$project" == varal11-stack-* && "$project" == "$expected" ]] || exit 1
pg_volume="${project}_restore_pg_${restore_id}"
wal_volume="${project}_restore_wal_${restore_id}"
for volume in "$pg_volume" "$wal_volume"; do
    [[ $(docker volume inspect --format '{{ index .Labels "varal.restore" }}' "$volume") == "$restore_id" ]] || exit 1
    [[ $(docker volume inspect --format '{{ index .Labels "varal.parent" }}' "$volume") == "$project" ]] || exit 1
done
exec 9>"$lab_dir/operation.lock"
flock -n 9 || { echo 'another laboratory operation is running' >&2; exit 1; }
image=varal11-postgres-lab:local
name="${project}-restore-${restore_id}"
if docker inspect "$name" >/dev/null 2>&1; then echo 'restore container exists; refusing' >&2; exit 1; fi
docker run --rm --network none --user 70:70 -v "$pg_volume:/restore" --entrypoint sh "$image" -c 'set -eu; test ! -e /restore/postmaster.pid; test ! -e /restore/recovery.signal; touch /restore/recovery.signal'
container_id=
cleanup() {
    if [[ -n "$container_id" ]]; then docker stop --timeout 30 "$container_id" >/dev/null 2>&1 || :; fi
}
trap cleanup EXIT HUP INT TERM
container_id=$(docker run -d --name "$name" --label "varal.restore=$restore_id" --network none \
    -v "$pg_volume:/var/lib/postgresql/data" -v "$wal_volume:/wal:ro" "$image" postgres \
    -c "restore_command=cp /wal/%f %p" -c "recovery_target_lsn=$target_lsn" \
    -c recovery_target_action=pause -c "listen_addresses=")
attempt=0
until docker exec "$container_id" pg_isready -U varal_admin -d varal_lab >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    [[ "$attempt" -lt 120 ]] || { echo 'recovery did not become queryable' >&2; exit 1; }
    sleep 1
done
result=$(docker exec "$container_id" psql -U varal_admin -d varal_lab -t -A -v ON_ERROR_STOP=1 \
    -c "SELECT pg_is_in_recovery(), pg_last_wal_replay_lsn() >= '$target_lsn'::pg_lsn, count(*) = 1 FROM pitr_lab_probe WHERE marker='post-base'")
[[ "$result" == 't|t|t' ]] || { echo 'PITR target or synthetic post-base commit not verified' >&2; exit 1; }
printf '%s\n' 'isolated PostgreSQL PITR reached target and recovered post-base synthetic commit; traffic remains closed'
