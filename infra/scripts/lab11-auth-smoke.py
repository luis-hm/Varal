"""Exercise synthetic signup, CSRF, secure cookies and SSR over verified lab TLS."""

import argparse
import json
import secrets
import subprocess
import tempfile
import uuid
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("lab_dir")
args = parser.parse_args()
root = Path(args.lab_dir)
if root.parent != Path("/tmp") or not root.name.startswith("varal11-stack."):
    raise SystemExit("invalid laboratory directory")
values = dict(
    line.split("=", 1)
    for line in (root / "lab.env").read_text().splitlines()
    if "=" in line
)
port = int(values["LAB_PORT"])
origin = f"https://varal.local:{port}"
with tempfile.TemporaryDirectory(prefix="auth-smoke.", dir=root) as tmp:
    tmp = Path(tmp)
    jar = tmp / "cookies"
    body = tmp / "body"
    headers = tmp / "headers"

    def call(path, method="GET", payload=None, extra=()):
        command = [
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
            f"varal.local:{port}:127.0.0.1",
            "--cookie-jar",
            str(jar),
            "--cookie",
            str(jar),
            "--dump-header",
            str(headers),
            "--output",
            str(body),
            "--write-out",
            "%{http_code}",
            "--request",
            method,
        ]
        for item in extra:
            command.extend(["--header", item])
        if payload is not None:
            command.extend(
                ["--header", "Content-Type: application/json", "--data-binary", "@-"]
            )
        command.append(origin + path)
        result = subprocess.run(
            command,
            input=json.dumps(payload).encode() if payload is not None else None,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            raise SystemExit("TLS request transport failed")
        return int(result.stdout), body.read_bytes(), headers.read_text()

    def cookies():
        found = {}
        for line in jar.read_text().splitlines():
            if line.startswith("#HttpOnly_"):
                line = line[len("#HttpOnly_") :]
            elif line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) == 7:
                found[parts[5]] = {"value": parts[6], "secure": parts[3] == "TRUE"}
        return found

    status, _, _ = call("/api/auth/browser/v1/config")
    assert status == 200
    csrf = cookies()["csrftoken"]["value"]
    synthetic_email = f"smoke-{uuid.uuid4()}@varal.invalid"
    payload = {"email": synthetic_email, "password": secrets.token_urlsafe(24) + "A1!"}
    status, _, _ = call(
        "/api/auth/browser/v1/auth/signup", "POST", payload, [f"Origin: {origin}"]
    )
    assert status == 403
    status, _, _ = call(
        "/api/auth/browser/v1/auth/signup",
        "POST",
        payload,
        [f"Origin: {origin}", f"X-CSRFToken: {csrf}"],
    )
    assert status == 200
    state = cookies()
    assert state["csrftoken"]["secure"] and state["sessionid"]["secure"]
    status, response, hdr = call("/api/me/")
    assert status == 200 and "no-store" in hdr.lower()
    user_id = str(uuid.UUID(json.loads(response)["id"]))
    cookie = f"sessionid={state['sessionid']['value']}; varal_owner={user_id}"
    status, _, _ = call("/", extra=[f"Cookie: {cookie}"])
    assert status == 200
print(
    "verified TLS, CSRF rejection, synthetic signup, secure cookies and authenticated SSR: ok"
)
