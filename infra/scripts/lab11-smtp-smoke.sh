#!/bin/sh
set -eu
base_dir=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
tmp_dir=$(mktemp -d /tmp/varal11-smtp.XXXXXXXX)
lab_id=$(basename "$tmp_dir" | tr '.' '-')
network_id=
receiver_id=
cleanup() {
    if [ -n "$receiver_id" ]; then docker rm -f "$receiver_id" >/dev/null 2>&1 || :; fi
    if [ -n "$network_id" ]; then docker network rm "$network_id" >/dev/null 2>&1 || :; fi
    rm -rf "$tmp_dir"
}
trap cleanup EXIT HUP INT TERM
openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj /CN=varal11-smtp-ca -keyout "$tmp_dir/ca.key" -out "$tmp_dir/ca.pem" >/dev/null 2>&1
openssl req -newkey rsa:2048 -nodes -subj /CN=smtp-capture -keyout "$tmp_dir/smtp.key" -out "$tmp_dir/smtp.csr" >/dev/null 2>&1
printf '%s\n' 'subjectAltName=DNS:smtp-capture' > "$tmp_dir/smtp.ext"
openssl x509 -req -in "$tmp_dir/smtp.csr" -CA "$tmp_dir/ca.pem" -CAkey "$tmp_dir/ca.key" -CAcreateserial -days 1 -extfile "$tmp_dir/smtp.ext" -out "$tmp_dir/smtp.pem" >/dev/null 2>&1
chmod 444 "$tmp_dir/smtp.key"
docker build -t varal11-smtp-lab:local -f "$base_dir/infra/lab/smtp.Dockerfile" "$base_dir/infra/lab" >/dev/null
network_id=$(docker network create --internal --label "varal.lab=$lab_id" "$lab_id-net")
receiver_id=$(docker run -d --label "varal.lab=$lab_id" --network "$network_id" --network-alias smtp-capture --read-only --tmpfs /capture:uid=10002,gid=10002,mode=0700 -v "$tmp_dir/smtp.pem:/run/smtp/cert.pem:ro" -v "$tmp_dir/smtp.key:/run/smtp/key.pem:ro" varal11-smtp-lab:local)
attempt=0
until docker run --rm --network "$network_id" -v "$tmp_dir/ca.pem:/ca.pem:ro" python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b python -c '
import smtplib, ssl
from email.message import EmailMessage
message=EmailMessage()
message["From"]="sender@example.invalid"
message["To"]="recipient@example.invalid"
message["Subject"]="synthetic"
message.set_content("synthetic transport proof")
with smtplib.SMTP("smtp-capture", 1025, timeout=3) as client:
    client.ehlo()
    client.starttls(context=ssl.create_default_context(cafile="/ca.pem"))
    client.ehlo()
    client.send_message(message)
    try:
        client.sendmail("sender@example.invalid", ["outside@example.com"], "synthetic")
    except smtplib.SMTPRecipientsRefused:
        pass
    else:
        raise AssertionError("receiver accepted an external address")
' >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 10 ]; then exit 1; fi
    sleep 1
done
docker exec "$receiver_id" python -c '
from pathlib import Path
files=list(Path("/capture").glob("*.eml"))
assert len(files) == 1
content=files[0].read_bytes()
assert b"synthetic transport proof" in content
assert files[0].stat().st_mode & 0o777 == 0o600
'
printf '%s\n' 'isolated SMTP STARTTLS, verified certificate, capture and external-recipient rejection: ok'
