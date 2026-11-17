#!/bin/sh
set -eu
mkdir -p "/home/pwuser/.pki/nssdb" /tmp/varal-browser-profile
certutil -N -d "sql:/home/pwuser/.pki/nssdb" --empty-password
certutil -A -d "sql:/home/pwuser/.pki/nssdb" -n varal-lab-ca -t 'C,,' -i /run/lab-ca/ca.pem
exec /ms-playwright/chromium-1254/chrome-linux64/chrome \
    --headless=new --no-sandbox --disable-background-networking --enable-devtools-pwa-handler \
    --remote-debugging-address=127.0.0.1 --remote-debugging-port=9222 \
    --user-data-dir=/tmp/varal-browser-profile --no-first-run --no-default-browser-check about:blank
