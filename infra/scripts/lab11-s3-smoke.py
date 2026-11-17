"""Probe private S3 with synthetic bytes and verified TLS without logging signed URLs."""

import argparse
import json
import subprocess
import tempfile
import time
import urllib.parse
import uuid
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("lab_dir")
parser.add_argument("--prove-60", action="store_true")
args = parser.parse_args()
root = Path(args.lab_dir)
if root.parent != Path("/tmp") or not root.name.startswith("varal11-stack."):
    raise SystemExit("invalid laboratory directory")
project = (root / "project").read_text().strip()
if project != root.name.lower().replace(".", "-"):
    raise SystemExit("invalid laboratory project")
base = Path(__file__).resolve().parents[2]
values = dict(
    line.split("=", 1)
    for line in (root / "lab.env").read_text().splitlines()
    if "=" in line
)
port = int(values["LAB_PORT"])
compose = [
    "docker",
    "compose",
    "--env-file",
    str(root / "lab.env"),
    "-f",
    str(base / "infra/lab/compose.yml"),
    "-p",
    project,
]
key = "laboratorio/" + str(uuid.uuid4()) + ".pdf"
payload = b"synthetic-pdf-content-for-private-storage-proof"
create = """
import django, json, os, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from django.conf import settings
from apps.boletos.storage import cliente
key=sys.argv[1]
cliente().put_object(Bucket=settings.S3_BUCKET_NAME, Key=key, Body=b"synthetic-pdf-content-for-private-storage-proof")
public=cliente(publico=True)
params={"Bucket":settings.S3_BUCKET_NAME,"Key":key}
print(json.dumps({"long":public.generate_presigned_url("get_object", Params=params, ExpiresIn=60),"short":public.generate_presigned_url("get_object", Params=params, ExpiresIn=1)}))
"""
cleanup = """
import django, os, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from django.conf import settings
from apps.boletos.storage import cliente
cliente().delete_object(Bucket=settings.S3_BUCKET_NAME, Key=sys.argv[1])
"""


def api(code):
    result = subprocess.run(
        compose + ["exec", "-T", "api", "python", "-", key],
        input=code.encode(),
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError("API storage operation failed")
    return result.stdout


def get(url, output):
    result = subprocess.run(
        [
            "curl",
            "--silent",
            "--show-error",
            "--max-time",
            "60",
            "--noproxy",
            "*",
            "--cacert",
            str(root / "tls/ca.pem"),
            "--resolve",
            f"s3.varal.local:{port}:127.0.0.1",
            "--output",
            str(output),
            "--write-out",
            "%{http_code}",
            url,
        ],
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError("signed storage request failed")
    return int(result.stdout)


try:
    urls = json.loads(api(create))
    query = urllib.parse.parse_qs(urllib.parse.urlsplit(urls["long"]).query)
    assert query["X-Amz-Expires"] == ["60"]
    with tempfile.TemporaryDirectory(prefix="s3-smoke.", dir=root) as tmp:
        output = Path(tmp) / "content"
        assert get(urls["long"], output) == 200 and output.read_bytes() == payload
        unsigned = urls["long"].split("?", 1)[0]
        assert get(unsigned, output) == 403
        time.sleep(3)
        assert get(urls["short"], output) == 403
        if args.prove_60:
            time.sleep(61)
            assert get(urls["long"], output) == 403
    suffix = "60s expiration observed" if args.prove_60 else "60s expiry parameter verified"
    print(f"private S3, browser-reachable signed host and expiration: ok ({suffix})")
finally:
    api(cleanup)
