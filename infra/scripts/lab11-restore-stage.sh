#!/usr/bin/env bash
set -euo pipefail
# Staging only: creates new volumes, no network/service, never authorizes reopening.
lab_dir=${1:?laboratory directory required}
snapshot=${2:?quarantined snapshot directory required}
key_file=${3:?protected backup passphrase file required}
case "$lab_dir" in /tmp/varal11-stack.*) ;; *) echo 'invalid laboratory directory' >&2; exit 1 ;; esac
project=$(cat "$lab_dir/project")
expected=$(basename "$lab_dir" | tr '.A-Z' '-a-z')
[[ "$project" == varal11-stack-* && "$project" == "$expected" ]] || exit 1
snapshot=$(realpath -e "$snapshot")
case "$snapshot" in "$lab_dir"/backups/snapshot.*) ;; *) echo 'snapshot outside laboratory' >&2; exit 1 ;; esac
[[ -f "$snapshot/NOT_RESTORABLE" && -f "$key_file" && $(stat -c '%a' "$key_file") == 600 ]] || exit 1
mkdir -p -m 700 "$lab_dir/gpg"
export GNUPGHOME="$lab_dir/gpg"
exec 9>"$lab_dir/operation.lock"
flock -n 9 || { echo 'another laboratory operation is running' >&2; exit 1; }
work=$(mktemp -d "$lab_dir/restore-meta.XXXXXXXX")
trap 'rm -rf "$work"' EXIT HUP INT TERM
gpg --quiet --batch --pinentry-mode loopback --passphrase-file "$key_file" --decrypt "$snapshot/metadata.gpg" > "$work/metadata"
chmod 600 "$work/metadata"
get_field() { sed -n "s/^$1=//p" "$work/metadata"; }
target_lsn=$(get_field target_lsn)
target_segment=$(get_field target_segment)
system_id=$(get_field system_identifier)
base_hash=$(get_field base_cipher_sha256)
objects_hash=$(get_field objects_cipher_sha256)
manifest_hash=$(get_field object_manifest_cipher_sha256)
anchor_hash=$(get_field journal_anchor_cipher_sha256)
snapshot_id=$(get_field snapshot_id)
if [[ -e "$snapshot/cut.gpg" ]]; then
    gpg --quiet --batch --pinentry-mode loopback --passphrase-file "$key_file" --decrypt "$snapshot/cut.gpg" > "$work/cut"
    cut_field() { sed -n "s/^$1=//p" "$work/cut"; }
    [[ $(cut_field snapshot_id) == "$snapshot_id" && $(cut_field system_identifier) == "$system_id" && $(cut_field metadata_cipher_sha256) == "$(sha256sum "$snapshot/metadata.gpg" | cut -d ' ' -f 1)" ]] || exit 1
    target_lsn=$(cut_field target_lsn)
    target_segment=$(cut_field target_segment)
fi
[[ "$target_lsn" =~ ^[0-9A-F]+/[0-9A-F]+$ && "$target_segment" =~ ^[0-9A-F]{24}$ && "$system_id" =~ ^[0-9]{1,20}$ && "$base_hash" =~ ^[0-9a-f]{64}$ && "$objects_hash" =~ ^[0-9a-f]{64}$ && "$manifest_hash" =~ ^[0-9a-f]{64}$ && "$anchor_hash" =~ ^[0-9a-f]{64}$ && "$snapshot_id" =~ ^[0-9a-f-]{36}$ ]] || exit 1
[[ $(sha256sum "$snapshot/basebackup.gpg" | cut -d ' ' -f 1) == "$base_hash" ]] || exit 1
[[ $(sha256sum "$snapshot/objects.gpg" | cut -d ' ' -f 1) == "$objects_hash" ]] || exit 1
[[ $(sha256sum "$snapshot/object-manifest.gpg" | cut -d ' ' -f 1) == "$manifest_hash" ]] || exit 1
[[ $(sha256sum "$snapshot/journal-anchor.gpg" | cut -d ' ' -f 1) == "$anchor_hash" ]] || exit 1
gpg --quiet --batch --pinentry-mode loopback --passphrase-file "$key_file" --decrypt "$snapshot/object-manifest.gpg" > /dev/null
gpg --quiet --batch --pinentry-mode loopback --passphrase-file "$key_file" --decrypt "$snapshot/journal-anchor.gpg" > /dev/null
restore_id=$(python3 -c 'import uuid; print(uuid.uuid4().hex)')
pg_volume="${project}_restore_pg_${restore_id}"
objects_volume="${project}_restore_objects_${restore_id}"
wal_volume="${project}_restore_wal_${restore_id}"
for volume in "$pg_volume" "$objects_volume" "$wal_volume"; do
    if docker volume inspect "$volume" >/dev/null 2>&1; then echo 'restore volume exists; refusing' >&2; exit 1; fi
    docker volume create --label "varal.restore=$restore_id" --label "varal.parent=$project" "$volume" >/dev/null
    [[ $(docker volume inspect --format '{{ index .Labels "varal.restore" }}' "$volume") == "$restore_id" ]] || exit 1
done
printf 'Isolated restore volumes: %s %s %s\n' "$pg_volume" "$objects_volume" "$wal_volume"
python_image=python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b
for volume in "$pg_volume" "$wal_volume"; do
    docker run --rm --network none -v "$volume:/restore" --entrypoint chown "$python_image" 70:70 /restore
done
gpg --quiet --batch --pinentry-mode loopback --passphrase-file "$key_file" --decrypt "$snapshot/basebackup.gpg" |
    docker run --rm -i --network none --user 70:70 -v "$pg_volume:/restore" "$python_image" tar -xf - -C /restore
gpg --quiet --batch --pinentry-mode loopback --passphrase-file "$key_file" --decrypt "$snapshot/objects.gpg" |
    docker run --rm -i --network none -v "$objects_volume:/restore" "$python_image" tar -xf - -C /restore
actual_id=$(docker run --rm --network none --user 70:70 -v "$pg_volume:/var/lib/postgresql/data:ro" --entrypoint pg_controldata varal11-postgres-lab:local /var/lib/postgresql/data | sed -n 's/^Database system identifier:[[:space:]]*//p')
[[ "$actual_id" == "$system_id" ]] || { echo 'restored cluster identity mismatch' >&2; exit 1; }
first_segment=$(docker run --rm --network none --user 70:70 -v "$pg_volume:/restore:ro" --entrypoint cat "$python_image" /restore/backup_label | sed -n 's/^START WAL LOCATION:.*(file \([0-9A-F]*\)).*/\1/p')
[[ "$first_segment" =~ ^[0-9A-F]{24}$ ]] || { echo 'backup start WAL missing' >&2; exit 1; }
epoch=$(python3 - "$lab_dir/lab.env" <<'PY'
import sys
with open(sys.argv[1]) as source:
    for line in source:
        if line.startswith('LAB_JOURNAL_EPOCH='):
            print(line.strip().split('=', 1)[1]); break
PY
)
for name in wal_archive wal_anchor; do
    [[ $(docker volume inspect --format '{{ index .Labels "com.docker.compose.project" }}' "${project}_$name") == "$project" ]] || exit 1
done
docker run --rm --network none --entrypoint python \
    -v "${project}_wal_archive:/varal/wal-archive:ro" -v "${project}_wal_anchor:/varal/wal-anchor:ro" -v "$wal_volume:/varal/restore-wal" \
    -v "$lab_dir/keys/wal-cipher:/run/keys/wal-cipher:ro" -v "$lab_dir/keys/wal-witness:/run/keys/wal-witness:ro" \
    varal11-wal-lab:local /srv/export.py --archive /varal/wal-archive --anchor /varal/wal-anchor --output /varal/restore-wal \
    --epoch "$epoch" --system-identifier "$system_id" --cipher-key /run/keys/wal-cipher --witness-key /run/keys/wal-witness \
    --first "$first_segment" --last "$target_segment"
printf 'Staged isolated restore %s; target LSN %s; no database, user traffic or dispatch started.\n' "$restore_id" "$target_lsn"
