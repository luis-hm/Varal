#!/bin/sh
set -eu
# PostgreSQL init scripts run only for a new cluster. Bind it to the protected stack marker.
[ ! -e /varal/stack-identity/database.ready ] || { echo 'database reinitialization refused' >&2; exit 1; }
umask 077
printf '%s\n' "$JOURNAL_EPOCH" > /varal/stack-identity/.database.ready.tmp
sync -f /varal/stack-identity/.database.ready.tmp
mv /varal/stack-identity/.database.ready.tmp /varal/stack-identity/database.ready
sync -f /varal/stack-identity
