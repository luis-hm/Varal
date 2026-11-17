#!/bin/sh
set -eu
umask 077
export MC_CONFIG_DIR=/tmp/mc
mkdir -p "$MC_CONFIG_DIR"
# All credentials are synthetic local-only values; raw CLI output is never published.
if ! mc alias set lab http://storage:9000 "$STORAGE_ADMIN_USER" "$STORAGE_ADMIN_PASSWORD" >/dev/null 2>&1; then
    echo 'storage admin connection failed' >&2; exit 1
fi
if ! mc mb --ignore-existing lab/varal-lab-private >/dev/null 2>&1; then
    echo 'storage bucket initialization failed' >&2; exit 1
fi
if ! mc anonymous set none lab/varal-lab-private >/dev/null 2>&1; then
    echo 'storage privacy configuration failed' >&2; exit 1
fi
if ! mc admin user info lab "$STORAGE_APP_USER" >/dev/null 2>&1; then
    if ! mc admin user add lab "$STORAGE_APP_USER" "$STORAGE_APP_PASSWORD" >/dev/null 2>&1; then
        echo 'storage user initialization failed' >&2; exit 1
    fi
fi
if ! mc admin policy create lab varal-lab-app /etc/varal/storage-policy.json >/dev/null 2>&1; then
    echo 'storage policy initialization failed' >&2; exit 1
fi
if ! mc admin policy attach lab varal-lab-app --user "$STORAGE_APP_USER" >/dev/null 2>&1; then
    echo 'storage policy attachment failed' >&2; exit 1
fi
if ! mc alias set app http://storage:9000 "$STORAGE_APP_USER" "$STORAGE_APP_PASSWORD" >/dev/null 2>&1 || ! mc ls app/varal-lab-private >/dev/null 2>&1; then
    echo 'restricted storage credential verification failed' >&2; exit 1
fi
printf '%s\n' 'private laboratory bucket and restricted application credential ready'
