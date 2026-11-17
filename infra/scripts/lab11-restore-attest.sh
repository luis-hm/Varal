#!/usr/bin/env bash
set -euo pipefail
# Produce an operation-bound proof only after repeating all checks on the isolated clone.
base_dir=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
lab_dir=${1:?lab directory required}
snapshot=${2:?snapshot directory required}
key_file=${3:?backup passphrase required}
restore_id=${4:?restore volume ID required}
operation=${5:?restore operation UUID required}
case "$lab_dir" in /tmp/varal11-stack.*) ;; *) exit 1 ;; esac
[[ "$restore_id" =~ ^[0-9a-f]{32}$ && "$operation" =~ ^[0-9a-f-]{36}$ && $(stat -c '%a' "$key_file") == 600 ]] || exit 1
project=$(cat "$lab_dir/project")
[[ "$project" == "$(basename "$lab_dir" | tr '.A-Z' '-a-z')" && "$project" == varal11-stack-* ]] || exit 1
snapshot=$(realpath -e "$snapshot")
case "$snapshot" in "$lab_dir"/backups/snapshot.*) ;; *) exit 1 ;; esac
[[ -f "$snapshot/NOT_RESTORABLE" ]] || exit 1
exec 9>"$lab_dir/operation.lock"
flock -n 9 || exit 1
for service in api worker beat edge web ssr; do
    [[ -z $(docker ps -q --filter "label=com.docker.compose.project=$project" --filter "label=com.docker.compose.service=$service") ]] || exit 1
done
for name in pg objects wal; do
    volume="${project}_restore_${name}_${restore_id}"
    [[ $(docker volume inspect --format '{{ index .Labels "varal.restore" }}' "$volume") == "$restore_id" ]] || exit 1
    [[ $(docker volume inspect --format '{{ index .Labels "varal.parent" }}' "$volume") == "$project" ]] || exit 1
done
network="$project-restore-$restore_id"
pg="$project-restore-pg-$restore_id"
storage="$project-restore-storage-$restore_id"
for name in "$pg" "$storage"; do
    [[ $(docker inspect --format '{{ index .Config.Labels "varal.restore" }}' "$name") == "$restore_id" ]] || exit 1
    [[ $(docker inspect --format '{{len .HostConfig.PortBindings}}' "$name") == 0 ]] || exit 1
done
pg_ip=$(docker inspect --format "{{(index .NetworkSettings.Networks \"$network\").IPAddress}}" "$pg")
storage_ip=$(docker inspect --format "{{(index .NetworkSettings.Networks \"$network\").IPAddress}}" "$storage")
[[ "$pg_ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ && "$storage_ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || exit 1
[[ $(docker network inspect --format '{{.Internal}}' "$network") == true ]] || exit 1
[[ $(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Name}}{{end}}{{end}}' "$pg") == "${project}_restore_pg_${restore_id}" ]] || exit 1
[[ $(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Name}}{{end}}{{end}}' "$storage") == "${project}_restore_objects_${restore_id}" ]] || exit 1
for name in "$pg" "$storage"; do
    [[ $(docker inspect --format '{{len .NetworkSettings.Networks}}' "$name") == 1 ]] || exit 1
    [[ $(docker inspect --format "{{index .NetworkSettings.Networks \"$network\" | printf \"%v\"}}" "$name") != '<nil>' ]] || exit 1
done
export GNUPGHOME="$lab_dir/gpg"
umask 077
work=$(mktemp -d "$lab_dir/attest.XXXXXXXX")
chmod 755 "$work"
trap 'rm -rf "$work"' EXIT HUP INT TERM
for name in metadata object-manifest journal-anchor; do
    gpg --quiet --batch --pinentry-mode loopback --passphrase-file "$key_file" --decrypt "$snapshot/$name.gpg" > "$work/$name"
done
chmod 644 "$work/journal-anchor"
field() { sed -n "s/^$2=//p" "$work/$1"; }
snapshot_id=$(field metadata snapshot_id)
system_id=$(field metadata system_identifier)
if [[ -f "$snapshot/cut.gpg" ]]; then
    gpg --quiet --batch --pinentry-mode loopback --passphrase-file "$key_file" --decrypt "$snapshot/cut.gpg" > "$work/cut"
    target=$(field cut target_lsn)
    last=$(field cut target_segment)
    [[ $(field cut snapshot_id) == "$snapshot_id" && $(field cut system_identifier) == "$system_id" && $(field cut metadata_cipher_sha256) == "$(sha256sum "$snapshot/metadata.gpg" | cut -d ' ' -f 1)" ]] || exit 1
else
    target=$(field metadata target_lsn)
    last=$(field metadata target_segment)
fi
for pair in 'basebackup base_cipher_sha256' 'objects objects_cipher_sha256' 'object-manifest object_manifest_cipher_sha256' 'journal-anchor journal_anchor_cipher_sha256'; do
    read -r file property <<< "$pair"
    [[ $(sha256sum "$snapshot/$file.gpg" | cut -d ' ' -f 1) == "$(field metadata "$property")" ]] || exit 1
done
[[ "$target" =~ ^[0-9A-F]+/[0-9A-F]+$ && "$last" =~ ^[0-9A-F]{24}$ ]] || exit 1
first=$(gpg --quiet --batch --pinentry-mode loopback --passphrase-file "$key_file" --decrypt "$snapshot/basebackup.gpg" | tar -xOf - backup_label | sed -n 's/^START WAL LOCATION:.*(file \([0-9A-F]*\)).*/\1/p')
[[ "$first" =~ ^[0-9A-F]{24}$ ]] || exit 1
epoch=$(sed -n 's/^LAB_JOURNAL_EPOCH=//p' "$lab_dir/lab.env")
docker run --rm --network none --entrypoint python \
    -v "${project}_wal_archive:/varal/wal-archive:ro" -v "${project}_wal_anchor:/varal/wal-anchor:ro" \
    -v "$lab_dir/keys/wal-cipher:/run/keys/cipher:ro" -v "$lab_dir/keys/wal-witness:/run/keys/witness:ro" \
    -v "$base_dir/infra/wal/attest-range.py:/srv/attest-range.py:ro" varal11-wal-lab:local /srv/attest-range.py \
    /varal/wal-archive /varal/wal-anchor "$epoch" "$system_id" /run/keys/cipher /run/keys/witness "$first" "$last" > "$work/wal"
db_result=$(docker exec "$pg" psql -U varal_admin -d varal_lab -t -A -v ON_ERROR_STOP=1 -c "SELECT system_identifier::text || '|' || coalesce(pg_last_wal_replay_lsn()::text,'') || '|' || EXISTS(SELECT 1 FROM public.privacidade_marcarestauracao WHERE operation_id='$operation')::text FROM pg_control_system()")
IFS='|' read -r actual_id replay marker <<< "$db_result"
[[ "$actual_id" == "$system_id" && "$marker" == true && "$replay" =~ ^[0-9A-F]+/[0-9A-F]+$ ]] || exit 1
api=(docker run --rm -i --network "$network" --env-file "$lab_dir/restore-maintenance.env" \
    -e "POSTGRES_HOST=$pg_ip" -e POSTGRES_DB=varal_lab -e "S3_ENDPOINT_URL=http://$storage_ip:9000" \
    -v "$lab_dir/keys/restore:/keys/restore:ro" -v "$lab_dir/keys/chain:/keys/chain:ro" \
    -v "$lab_dir/keys/checkpoint:/keys/checkpoint:ro" -v "$lab_dir/keys/receipt:/keys/receipt:ro" \
    -v "$work:/proof:ro" -e DJANGO_SETTINGS_MODULE=config.settings varal11-api-final:local)
"${api[@]}" python manage.py exportar_manifesto_restore --operacao "$operation" --isolado > "$work/db"
"${api[@]}" python - < "$base_dir/infra/lab/s3-manifest.py" > "$work/actual"
python3 "$base_dir/infra/lab/restore-object-verify.py" "$work/object-manifest" "$work/actual" "$work/db" > "$work/objects"
"${api[@]}" python - /proof/journal-anchor < "$base_dir/infra/lab/restore-journal-verify.py" > "$work/fence"
[[ -f "$lab_dir/keys/restore-proof" && $(stat -c '%a' "$lab_dir/keys/restore-proof") == 600 ]] || exit 1
python3 - "$work" "$lab_dir/keys/restore-proof" "$operation" "$snapshot_id" "$system_id" "$target" "$replay" "$last" <<'PY'
import hashlib, hmac, json, sys
from pathlib import Path
work, key, operation, snapshot, system_id, target, replay, last = sys.argv[1:]
work = Path(work)
read = lambda name: json.loads((work / name).read_text())
fields = dict(line.split('=',1) for line in (work/'metadata').read_text().splitlines())
fence, wal, objects = read('fence'), read('wal'), read('objects')
lsn = lambda value: (int(value.split('/')[0],16)<<32) + int(value.split('/')[1],16)
if lsn(replay) < lsn(target): raise ValueError('replay before target')
proof = dict(version=1, operation_id=operation, snapshot_id=snapshot, epoch=fence['epoch'], fence_id=fence['fence_id'], journal_seq=fence['seq'], journal_record_mac=fence['record_mac'], system_identifier=system_id, timeline=last[:8], target_lsn=target, replay_lsn=replay, wal_checkpoint_seq=wal['sequence'], wal_chain_mac=wal['chain_mac'], base_cipher_sha256=fields['base_cipher_sha256'], objects_cipher_sha256=fields['objects_cipher_sha256'], **objects, key_id='restore-proof-v1')
canonical = lambda value: json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
proof['mac'] = hmac.new(Path(key).read_bytes().rstrip(),b'varal-restore-proof-v1\n'+canonical(proof),hashlib.sha256).hexdigest()
(work/'proof.json').write_bytes(canonical(proof))
PY
[[ ! -e "$lab_dir/restore-proof-$operation.json" ]] || exit 1
cp "$work/proof.json" "$lab_dir/restore-proof-$operation.json"
printf 'Authenticated restore proof created; traffic and dispatch remain closed.\n'
