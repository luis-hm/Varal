#!/usr/bin/env bash
set -euo pipefail
# Bind a later, archived PITR point to a quarantined backup. This does not open a restore.
base_dir=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
lab_dir=${1:?laboratory directory required}
snapshot=${2:?snapshot directory required}
key_file=${3:?backup passphrase file required}
target_lsn=${4:?target LSN required}
case "$lab_dir" in /tmp/varal11-stack.*) ;; *) exit 1 ;; esac
[[ "$target_lsn" =~ ^[0-9A-F]+/[0-9A-F]+$ && $(stat -c '%a' "$key_file") == 600 ]] || exit 1
project=$(cat "$lab_dir/project")
[[ "$project" == "$(basename "$lab_dir" | tr '.A-Z' '-a-z')" && "$project" == varal11-stack-* ]] || exit 1
snapshot=$(realpath -e "$snapshot")
case "$snapshot" in "$lab_dir"/backups/snapshot.*) ;; *) exit 1 ;; esac
[[ -f "$snapshot/NOT_RESTORABLE" && ! -e "$snapshot/cut.gpg" ]] || exit 1
compose=(docker compose --env-file "$lab_dir/lab.env" -f "$base_dir/infra/lab/compose.yml" -p "$project")
exec 9>"$lab_dir/operation.lock"
flock -n 9 || exit 1
if [[ -f "$lab_dir/ACTIVE_RESTORE" ]]; then
    active_id=$(python3 - "$lab_dir/ACTIVE_RESTORE" "$project" <<'PY'
import json,re,sys
d=json.load(open(sys.argv[1]))
if d.get('project')!=sys.argv[2] or d.get('state')!='cutover' or not re.fullmatch(r'[0-9a-f]{32}',d.get('restore_id','')): raise SystemExit(1)
print(d['restore_id'])
PY
)
    [[ $(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Name}}{{end}}{{end}}' "$project-postgres-1") == "${project}_restore_pg_${active_id}" ]] || exit 1
fi
for service in api worker beat edge web ssr; do
    [[ -z $(docker ps -q --filter "label=com.docker.compose.project=$project" --filter "label=com.docker.compose.service=$service") ]] || { echo 'stop source writers first' >&2; exit 1; }
done
export GNUPGHOME="$lab_dir/gpg"
umask 077
work=$(mktemp -d "$lab_dir/cut.XXXXXXXX")
trap 'rm -rf "$work"' EXIT HUP INT TERM
gpg --quiet --batch --pinentry-mode loopback --passphrase-file "$key_file" --decrypt "$snapshot/metadata.gpg" > "$work/metadata"
snapshot_id=$(sed -n 's/^snapshot_id=//p' "$work/metadata")
base_lsn=$(sed -n 's/^target_lsn=//p' "$work/metadata")
system_id=$(sed -n 's/^system_identifier=//p' "$work/metadata")
[[ "$snapshot_id" =~ ^[0-9a-f-]{36}$ && "$base_lsn" =~ ^[0-9A-F]+/[0-9A-F]+$ && "$system_id" =~ ^[0-9]+$ ]] || exit 1
actual_id=$("${compose[@]}" exec -T postgres cat /varal/wal-spool/cluster.id)
[[ "$actual_id" == "$system_id" ]] || exit 1
segment=$("${compose[@]}" exec -T postgres sh -c 'psql -q -t -A -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT CASE WHEN '\''"$1"'\''::pg_lsn >= '\''"$2"'\''::pg_lsn AND '\''"$1"'\''::pg_lsn <= pg_current_wal_insert_lsn() THEN pg_walfile_name('\''"$1"'\''::pg_lsn) END"' sh "$target_lsn" "$base_lsn")
[[ "$segment" =~ ^[0-9A-F]{24}$ ]] || exit 1
# Archive ACK alone is not the restore proof: export verifies the full chain and all bytes.
"${compose[@]}" exec -T postgres test -f "/varal/wal-acks/$segment.ack"
metadata_hash=$(sha256sum "$snapshot/metadata.gpg" | cut -d ' ' -f 1)
printf 'snapshot_id=%s\nmetadata_cipher_sha256=%s\ntarget_lsn=%s\ntarget_segment=%s\nsystem_identifier=%s\n' "$snapshot_id" "$metadata_hash" "$target_lsn" "$segment" "$system_id" |
    gpg --quiet --batch --yes --pinentry-mode loopback --passphrase-file "$key_file" --symmetric --cipher-algo AES256 --output "$work/cut.gpg"
mv -n "$work/cut.gpg" "$snapshot/cut.gpg"
[[ ! -e "$work/cut.gpg" ]] || exit 1
printf 'Archived later PITR cut bound to quarantined snapshot; restore remains closed.\n'
