#!/usr/bin/env bash
set -euo pipefail
base_dir=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
lab_dir=${1:?laboratory directory required}
system_id=${2:?restored cluster system identifier required}
first=${3:?first segment required}
last=${4:?last segment required}
case "$lab_dir" in /tmp/varal11-stack.*) ;; *) echo 'invalid laboratory directory' >&2; exit 1 ;; esac
[[ "$system_id" =~ ^[0-9]{1,20}$ && "$first" =~ ^[0-9A-F]{24}$ && "$last" =~ ^[0-9A-F]{24}$ ]] || exit 1
project=$(cat "$lab_dir/project")
expected=$(basename "$lab_dir" | tr '.A-Z' '-a-z')
[[ "$project" == varal11-stack-* && "$project" == "$expected" ]] || exit 1
for name in wal_archive wal_anchor; do
    volume="${project}_${name}"
    [[ $(docker volume inspect --format '{{ index .Labels "com.docker.compose.project" }}' "$volume") == "$project" ]] || exit 1
    [[ $(docker volume inspect --format '{{ index .Labels "com.docker.compose.volume" }}' "$volume") == "$name" ]] || exit 1
done
epoch=$(python3 - "$lab_dir/lab.env" <<'PY'
import sys
with open(sys.argv[1]) as source:
    for line in source:
        if line.startswith('LAB_JOURNAL_EPOCH='):
            print(line.strip().split('=', 1)[1])
            break
PY
)
exec 9>"$lab_dir/operation.lock"
flock -n 9 || { echo 'another laboratory operation is running' >&2; exit 1; }
docker run --rm --network none --entrypoint python \
    -v "${project}_wal_archive:/varal/wal-archive:ro" \
    -v "${project}_wal_anchor:/varal/wal-anchor:ro" \
    -v "$lab_dir/keys/wal-cipher:/run/keys/wal-cipher:ro" \
    -v "$lab_dir/keys/wal-witness:/run/keys/wal-witness:ro" \
    varal11-wal-lab:local /srv/verify.py --archive /varal/wal-archive --anchor /varal/wal-anchor \
    --epoch "$epoch" --system-identifier "$system_id" --cipher-key /run/keys/wal-cipher \
    --witness-key /run/keys/wal-witness --first "$first" --last "$last"
