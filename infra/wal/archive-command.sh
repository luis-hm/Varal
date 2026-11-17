#!/bin/sh
set -eu
# PostgreSQL invokes this outside application transactions. No WAL bytes enter logs.
source_file=$1
segment=$2
case "$segment" in *[!0-9A-F.abehikoprstuyc]*|'') exit 1 ;; esac
ready="/varal/wal-spool/$segment.ready"
ack="/varal/wal-acks/$segment.ack"
if [ ! -f "$ack" ] && [ ! -f "$ready" ]; then
    temp="/varal/wal-spool/.$segment.$$.tmp"
    trap 'rm -f "$temp"' EXIT HUP INT TERM
    umask 077
    cp "$source_file" "$temp"
    sync -f "$temp"
    mv "$temp" "$ready"
    sync -f /varal/wal-spool
fi
count=0
while [ ! -f "$ack" ]; do
    count=$((count + 1))
    [ "$count" -lt 300 ] || exit 1
    sleep 0.1
done
exit 0
