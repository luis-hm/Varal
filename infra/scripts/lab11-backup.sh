#!/usr/bin/env bash
set -euo pipefail
# Backup is quarantined until the independent delivery ledger and restore checks exist.
base_dir=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
lab_dir=${1:?pass a laboratory directory}
key_file=${2:?pass a protected file containing a synthetic backup passphrase}
probe_mode=${3:-}
[[ -z "$probe_mode" || "$probe_mode" == '--synthetic-pitr-probe' || "$probe_mode" == '--active-primary' ]] || exit 1
case "$lab_dir" in /tmp/varal11-stack.*) ;; *) echo 'invalid laboratory directory' >&2; exit 1 ;; esac
[[ -f "$lab_dir/project" && -f "$lab_dir/lab.env" && -f "$key_file" ]] || exit 1
project=$(cat "$lab_dir/project")
expected=$(basename "$lab_dir" | tr '.A-Z' '-a-z')
[[ "$project" == varal11-stack-* && "$project" == "$expected" ]] || exit 1
if [[ "$probe_mode" != '--active-primary' ]]; then
    [[ ! -e "$lab_dir/ACTIVE_RESTORE" && ! -e "$lab_dir/CUTOVER" ]] || { echo 'restored primary active: base compose backup forbidden' >&2; exit 1; }
fi
[[ $(stat -c '%a' "$key_file") == 600 ]] || { echo 'passphrase file must have mode 600' >&2; exit 1; }
volume="${project}_objects"
compose=(docker compose --env-file "$lab_dir/lab.env" -f "$base_dir/infra/lab/compose.yml")
if [[ "$probe_mode" == '--active-primary' ]]; then
    restore_id=$(python3 - "$lab_dir/ACTIVE_RESTORE" "$project" <<'PY'
import json,re,sys,uuid
d=json.load(open(sys.argv[1]))
if set(d)!={'version','project','restore_id','operation_id','state'} or d['version']!=1 or d['project']!=sys.argv[2] or d['state']!='cutover' or not re.fullmatch(r'[0-9a-f]{32}',d['restore_id']) or str(uuid.UUID(d['operation_id']))!=d['operation_id']: raise SystemExit(1)
print(d['restore_id'])
PY
)
    export LAB_ACTIVE_POSTGRES_VOLUME="${project}_restore_pg_${restore_id}"
    export LAB_ACTIVE_OBJECTS_VOLUME="${project}_restore_objects_${restore_id}"
    export LAB_ACTIVE_STAGING_VOLUME="${project}_restore_staging_${restore_id}"
    export LAB_ACTIVE_BEAT_VOLUME="${project}_restore_beat_${restore_id}"
    volume="$LAB_ACTIVE_OBJECTS_VOLUME"
    for active_volume in "$LAB_ACTIVE_POSTGRES_VOLUME" "$LAB_ACTIVE_OBJECTS_VOLUME" "$LAB_ACTIVE_STAGING_VOLUME"; do
        [[ $(docker volume inspect --format '{{ index .Labels "varal.restore" }}' "$active_volume") == "$restore_id" && $(docker volume inspect --format '{{ index .Labels "varal.parent" }}' "$active_volume") == "$project" ]] || exit 1
    done
    [[ $(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Name}}{{end}}{{end}}' "$project-postgres-1") == "$LAB_ACTIVE_POSTGRES_VOLUME" ]] || exit 1
    [[ $(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Name}}{{end}}{{end}}' "$project-storage-1") == "$LAB_ACTIVE_OBJECTS_VOLUME" ]] || exit 1
    compose+=(-f "$base_dir/infra/lab/compose.active-restore.yml")
else
    [[ $(docker volume inspect --format '{{ index .Labels "com.docker.compose.project" }}' "$volume") == "$project" ]] || { echo 'object volume is not owned by lab' >&2; exit 1; }
    [[ $(docker volume inspect --format '{{ index .Labels "com.docker.compose.volume" }}' "$volume") == objects ]] || exit 1
fi
compose+=(-p "$project")
exec 9>"$lab_dir/operation.lock"
flock -n 9 || { echo 'another laboratory operation is running' >&2; exit 1; }
if [[ "$probe_mode" != '--active-primary' ]]; then
    [[ ! -e "$lab_dir/ACTIVE_RESTORE" && ! -e "$lab_dir/CUTOVER" ]] || { echo 'restored primary active: base compose backup forbidden' >&2; exit 1; }
else
    [[ $(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["restore_id"])' "$lab_dir/ACTIVE_RESTORE") == "$restore_id" ]] || { echo 'active restore changed during lock acquisition' >&2; exit 1; }
    [[ $(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Name}}{{end}}{{end}}' "$project-postgres-1") == "$LAB_ACTIVE_POSTGRES_VOLUME" ]] || exit 1
    [[ $(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Name}}{{end}}{{end}}' "$project-storage-1") == "$LAB_ACTIVE_OBJECTS_VOLUME" ]] || exit 1
fi
# Stop all normal entry points and writers before snapshotting; leave journal and Postgres alive.
"${compose[@]}" stop edge web ssr worker beat api
mkdir -p -m 700 "$lab_dir/backups" "$lab_dir/gpg"
export GNUPGHOME="$lab_dir/gpg"
backup_dir=$(mktemp -d "$lab_dir/backups/snapshot.XXXXXXXX")
chmod 700 "$backup_dir"
status_file="$backup_dir/NOT_RESTORABLE"
printf '%s\n' 'Quarantined: journal, pending pins and independent delivery ledger must be reconciled before any restore can be opened.' > "$status_file"
if [[ "$probe_mode" == '--synthetic-pitr-probe' ]]; then
    "${compose[@]}" exec -T postgres sh -c 'PGPASSWORD="$MIGRATE_PASSWORD" psql -q -v ON_ERROR_STOP=1 -h 127.0.0.1 -U "$MIGRATE_USER" -d "$POSTGRES_DB" -c "CREATE TABLE IF NOT EXISTS pitr_lab_probe (marker text PRIMARY KEY); DELETE FROM pitr_lab_probe WHERE marker=\$\$post-base\$\$"' >/dev/null
fi
snapshot_id=$(python3 -c 'import uuid; print(uuid.uuid4())')
started=$(date -u +%Y-%m-%dT%H:%M:%SZ)
# Historical checkpoint is encrypted evidence only; it never replaces the independent live anchor.
"${compose[@]}" exec -T journal cat /varal/checkpoint/checkpoint.json |
    gpg --quiet --batch --yes --pinentry-mode loopback --passphrase-file "$key_file" --symmetric --cipher-algo AES256 --output "$backup_dir/journal-anchor.gpg"
# Capture every object hash after writers stop, before stopping the S3 service.
"${compose[@]}" run --rm --no-deps -T --entrypoint python api - < "$base_dir/infra/lab/s3-manifest.py" |
    gpg --quiet --batch --yes --pinentry-mode loopback --passphrase-file "$key_file" --symmetric --cipher-algo AES256 --output "$backup_dir/object-manifest.gpg"
"${compose[@]}" stop storage
"${compose[@]}" exec -T postgres sh -c 'export PGPASSWORD="$POSTGRES_PASSWORD"; exec pg_basebackup -h 127.0.0.1 -U "$POSTGRES_USER" -D - --format=tar --wal-method=none --checkpoint=fast --no-password' |
    gpg --quiet --batch --yes --pinentry-mode loopback --passphrase-file "$key_file" --symmetric --cipher-algo AES256 --output "$backup_dir/basebackup.gpg"
if [[ "$probe_mode" == '--synthetic-pitr-probe' ]]; then
    # This fixed synthetic commit happens after the physical base backup; production paths cannot invoke it implicitly.
    "${compose[@]}" exec -T postgres sh -c 'PGPASSWORD="$APP_PASSWORD" psql -q -v ON_ERROR_STOP=1 -h 127.0.0.1 -U "$APP_USER" -d "$POSTGRES_DB" -c "INSERT INTO pitr_lab_probe VALUES (\$\$post-base\$\$)"' >/dev/null
fi
# Capture a WAL boundary after the base backup and require its archived witness.
# A restore point forces a WAL record even when the current segment is empty;
# otherwise pg_switch_wal() may be a no-op and no witness can appear.
"${compose[@]}" exec -T postgres sh -c 'psql -q -t -A -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT pg_create_restore_point('\''varal_lab_backup'\'')"' >/dev/null
target_lsn=$("${compose[@]}" exec -T postgres sh -c 'psql -q -t -A -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT pg_current_wal_insert_lsn()"')
[[ "$target_lsn" =~ ^[0-9A-F]+/[0-9A-F]+$ ]] || exit 1
target_segment=$("${compose[@]}" exec -T postgres sh -c 'psql -q -t -A -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT pg_walfile_name(pg_current_wal_insert_lsn())"')
[[ "$target_segment" =~ ^[0-9A-F]{24}$ ]] || exit 1
"${compose[@]}" exec -T postgres sh -c 'psql -q -t -A -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT pg_switch_wal()"' >/dev/null
attempt=0
until "${compose[@]}" exec -T postgres test -f "/varal/wal-acks/$target_segment.ack"; do
    attempt=$((attempt + 1))
    [[ "$attempt" -lt 120 ]] || { echo 'WAL archive witness unavailable' >&2; exit 1; }
    sleep 1
done
system_id=$("${compose[@]}" exec -T postgres cat /varal/wal-spool/cluster.id)
[[ "$system_id" =~ ^[0-9]{1,20}$ ]] || exit 1
docker run --rm --network none -v "$volume:/data:ro" python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b tar -C /data -cf - . |
    gpg --quiet --batch --yes --pinentry-mode loopback --passphrase-file "$key_file" --symmetric --cipher-algo AES256 --output "$backup_dir/objects.gpg"
finished=$(date -u +%Y-%m-%dT%H:%M:%SZ)
base_hash=$(sha256sum "$backup_dir/basebackup.gpg" | cut -d ' ' -f 1)
objects_hash=$(sha256sum "$backup_dir/objects.gpg" | cut -d ' ' -f 1)
manifest_hash=$(sha256sum "$backup_dir/object-manifest.gpg" | cut -d ' ' -f 1)
anchor_hash=$(sha256sum "$backup_dir/journal-anchor.gpg" | cut -d ' ' -f 1)
printf 'snapshot_id=%s\nsnapshot_started=%s\nsnapshot_finished=%s\ntarget_lsn=%s\ntarget_segment=%s\nsystem_identifier=%s\nbase_cipher_sha256=%s\nobjects_cipher_sha256=%s\nobject_manifest_cipher_sha256=%s\njournal_anchor_cipher_sha256=%s\nstatus=quarantined\n' "$snapshot_id" "$started" "$finished" "$target_lsn" "$target_segment" "$system_id" "$base_hash" "$objects_hash" "$manifest_hash" "$anchor_hash" |
    gpg --quiet --batch --yes --pinentry-mode loopback --passphrase-file "$key_file" --symmetric --cipher-algo AES256 --output "$backup_dir/metadata.gpg"
chmod 600 "$backup_dir"/*
printf 'Encrypted snapshot quarantined at %s; lab writers remain stopped. Restore and dispatch are not authorized until reconciliation is implemented.\n' "$backup_dir"
