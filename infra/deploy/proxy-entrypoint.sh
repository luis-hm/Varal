#!/bin/sh
set -eu
case "${VARAL_DOMAIN:-}" in ''|*[!a-z0-9.-]*) echo 'invalid public domain' >&2; exit 1 ;; esac
case "${VARAL_PROXY_ROLE:-}" in edge|ssr) ;; *) echo 'invalid proxy role' >&2; exit 1 ;; esac
case "${VARAL_STACK:-}" in hmgvaral|varal) ;; *) echo 'invalid stack namespace' >&2; exit 1 ;; esac
if [ "$VARAL_PROXY_ROLE" = edge ]; then
    trust=${COOLIFY_PROXY_TRUST:-coolify-proxy}
    if [ "$trust" != coolify-proxy ]; then
        case "$trust" in ''|*[!0-9A-Fa-f.:/]*) echo 'invalid exact trusted proxy' >&2; exit 1 ;; esac
        if ! printf '%s\n' "$trust" | grep -Eq '^([0-9]{1,3}\.){3}[0-9]{1,3}/32$|^[0-9A-Fa-f:]+/128$'; then
            echo 'invalid exact trusted proxy' >&2; exit 1
        fi
    fi
    export COOLIFY_PROXY_TRUST="$trust"
else
    case "${VARAL_WEB_IP:-}" in ''|*[!0-9A-Fa-f.:]*) echo 'invalid exact SSR client' >&2; exit 1 ;; esac
    if ! printf '%s\n' "${VARAL_WEB_IP:-}" | grep -Eq '^([0-9]{1,3}\.){3}[0-9]{1,3}$|^[0-9A-Fa-f:]+$'; then
        echo 'invalid exact SSR client' >&2; exit 1
    fi
fi
envsubst '$VARAL_DOMAIN $VARAL_STACK $COOLIFY_PROXY_TRUST $VARAL_WEB_IP' < "/etc/varal/$VARAL_PROXY_ROLE.conf.template" > /tmp/nginx.conf
exec nginx -c /tmp/nginx.conf -g 'daemon off;'
