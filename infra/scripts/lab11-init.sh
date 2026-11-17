#!/bin/sh
set -eu
# The generated directory, project and volumes are unique and contain synthetic laboratory data.
base_dir=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
lab_dir=$(mktemp -d /tmp/varal11-stack.XXXXXXXX)
chmod 700 "$lab_dir"
project=$(basename "$lab_dir" | tr '.A-Z' '-a-z')
printf 'Laboratory directory: %s\nProject: %s\n' "$lab_dir" "$project"
mkdir -m 755 "$lab_dir/keys"
mkdir -m 700 "$lab_dir/tls"
for name in chain receipt checkpoint writer restore fence wal-cipher wal-witness; do
    openssl rand -hex 32 > "$lab_dir/keys/$name"
    chmod 444 "$lab_dir/keys/$name"
done
openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj /CN=varal11-lab-ca -keyout "$lab_dir/tls/ca.key" -out "$lab_dir/tls/ca.pem" >/dev/null 2>&1
openssl req -newkey rsa:2048 -nodes -subj /CN=varal.local -keyout "$lab_dir/tls/key.pem" -out "$lab_dir/tls/leaf.csr" >/dev/null 2>&1
printf '%s\n' 'subjectAltName=DNS:varal.local,DNS:s3.varal.local' > "$lab_dir/tls/leaf.ext"
openssl x509 -req -in "$lab_dir/tls/leaf.csr" -CA "$lab_dir/tls/ca.pem" -CAkey "$lab_dir/tls/ca.key" -CAcreateserial -days 1 -extfile "$lab_dir/tls/leaf.ext" -out "$lab_dir/tls/cert.pem" >/dev/null 2>&1
openssl req -newkey rsa:2048 -nodes -subj /CN=smtp-capture -keyout "$lab_dir/tls/smtp.key" -out "$lab_dir/tls/smtp.csr" >/dev/null 2>&1
printf '%s\n' 'subjectAltName=DNS:smtp-capture' > "$lab_dir/tls/smtp.ext"
openssl x509 -req -in "$lab_dir/tls/smtp.csr" -CA "$lab_dir/tls/ca.pem" -CAkey "$lab_dir/tls/ca.key" -CAcreateserial -days 1 -extfile "$lab_dir/tls/smtp.ext" -out "$lab_dir/tls/smtp.pem" >/dev/null 2>&1
chmod 600 "$lab_dir/tls/ca.key" "$lab_dir/tls/key.pem"
# Synthetic leaf key is readable only to this private temp tree and its isolated receiver.
chmod 444 "$lab_dir/tls/smtp.key"
VARAL11_BASE_DIR="$base_dir" python3 - "$lab_dir" "$project" <<'PY'
import base64
import ipaddress
import json
import os
import secrets
import socket
import subprocess
import sys
import uuid
from pathlib import Path

root = Path(sys.argv[1])
project = sys.argv[2]
with socket.socket() as listener:
    listener.bind(('127.0.0.1', 0))
    port = listener.getsockname()[1]
# Docker still rejects a race with networks created after this check; never alter existing networks.
networks = json.loads(subprocess.check_output([sys.executable, str(Path(os.environ['VARAL11_BASE_DIR']) / 'infra/scripts/lab11-networks.py')], text=True))
application = ipaddress.ip_network(networks['application'])
frontend = ipaddress.ip_network(networks['frontend'])
epoch = str(uuid.uuid4())
postgres_password = secrets.token_hex(24)
postgres_admin_password = secrets.token_hex(24)
postgres_migrate_password = secrets.token_hex(24)
storage_password = secrets.token_hex(24)
storage_app_password = secrets.token_hex(24)
values = {
    'LAB_ENV_FILE': str(root / 'lab.env'),
    'LAB_RUNTIME_ENV': str(root / 'runtime.env'),
    'LAB_KEYS_DIR': str(root / 'keys'),
    'LAB_TLS_DIR': str(root / 'tls'),
    'LAB_POSTGRES_DB': 'varal_lab',
    'LAB_POSTGRES_USER': 'varal_lab',
    'LAB_POSTGRES_ADMIN': 'varal_admin',
    'LAB_POSTGRES_ADMIN_PASSWORD': postgres_admin_password,
    'LAB_POSTGRES_MIGRATE_USER': 'varal_migrate',
    'LAB_POSTGRES_MIGRATE_PASSWORD': postgres_migrate_password,
    'LAB_POSTGRES_PASSWORD': postgres_password,
    'LAB_STORAGE_USER': 'varal-lab',
    'LAB_STORAGE_PASSWORD': storage_password,
    'LAB_STORAGE_APP_USER': 'varal-lab-app',
    'LAB_STORAGE_APP_PASSWORD': storage_app_password,
    'LAB_JOURNAL_EPOCH': epoch,
    'LAB_EDGE_IP': str(application.network_address + 250),
    'LAB_SSR_IP': str(application.network_address + 251),
    'LAB_WEB_IP': str(frontend.network_address + 250),
    'LAB_FRONTEND_SUBNET': str(frontend),
    'LAB_SSR_CONFIG': str(root / 'ssr.conf'),
    'LAB_EDGE_CONFIG': str(root / 'edge.conf'),
    'LAB_APPLICATION_SUBNET': str(application),
    'LAB_PORT': str(port),
    'DJANGO_DEBUG': '0',
    'ACCOUNT_RATE_LIMIT_SIGNUP': '1000/m/ip',
    'DJANGO_SECRET_KEY': secrets.token_hex(32),
    'DJANGO_ALLOWED_HOSTS': 'varal.local,api',
    'FRONTEND_URL': f'https://varal.local:{port}',
    'API_PUBLIC_URL': f'https://varal.local:{port}',
    'POSTGRES_DB': 'varal_lab',
    'POSTGRES_USER': 'varal_lab',
    'POSTGRES_PASSWORD': postgres_password,
    'S3_BUCKET_NAME': 'varal-lab-private',
    'S3_REGION_NAME': 'us-east-1',
    'S3_PUBLIC_ENDPOINT_URL': f'https://s3.varal.local:{port}',
    'AWS_ACCESS_KEY_ID': 'varal-lab-app',
    'AWS_SECRET_ACCESS_KEY': storage_app_password,
    'JOURNAL_EPOCH': epoch,
    'NOTIFICACOES_STORAGE_KEY': base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
    'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
    'EMAIL_HOST': 'smtp-capture',
    'EMAIL_PORT': '1025',
    'EMAIL_USE_TLS': '1',
    'WEBPUSH_ENABLED': '0',
}
template = Path(os.environ['VARAL11_BASE_DIR']) / 'infra/lab/ssr.conf'
config = template.read_text().replace('# LAB_SSR_ACCESS', f"allow {values['LAB_WEB_IP']}; deny all;")
(root / 'ssr.conf').write_text(config)
edge_template = (Path(os.environ['VARAL11_BASE_DIR']) / 'infra/lab/nginx.conf').read_text()
if port != 8443:
    edge_template = edge_template.replace('listen 8443 ssl default_server;', f'listen 8443 ssl default_server;\n        listen {port} ssl default_server;')
    edge_template = edge_template.replace('listen 8443 ssl;', f'listen 8443 ssl;\n        listen {port} ssl;')
(root / 'edge.conf').write_text(edge_template)
path = root / 'lab.env'
path.write_text(''.join(f'{key}={value}\n' for key, value in values.items()))
path.chmod(0o600)
runtime = root / 'runtime.env'
runtime.write_text(''.join(f'{key}={value}\n' for key, value in values.items() if not key.startswith('LAB_')))
runtime.chmod(0o600)
(root / 'project').write_text(project + '\n')
PY
compose_file="$base_dir/infra/lab/compose.yml"
docker compose --env-file "$lab_dir/lab.env" -f "$compose_file" -p "$project" config --quiet
docker compose --env-file "$lab_dir/lab.env" -f "$compose_file" -p "$project" build journal-init wal-init
docker compose --env-file "$lab_dir/lab.env" -f "$compose_file" -p "$project" --profile initialize run --rm journal-init
docker compose --env-file "$lab_dir/lab.env" -f "$compose_file" -p "$project" --profile initialize run --rm wal-init
docker compose --env-file "$lab_dir/lab.env" -f "$compose_file" -p "$project" up -d journal wal-archive
printf 'Laboratory directory: %s\nProject: %s\n' "$lab_dir" "$project"
