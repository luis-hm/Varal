"""Exercise a synthetic journal fence over authenticated HTTP in the isolated lab."""

import hashlib
import hmac
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()


def request(method, path, key_id, key_file, data=None):
    body = canonical(data) if data is not None else b""
    digest = hashlib.sha256(body).hexdigest()
    payload = f"varal-journal-request-v1\n{method}\n{path}\n{digest}\n{key_id}".encode()
    signature = hmac.new(
        Path(key_file).read_bytes().rstrip(), payload, hashlib.sha256
    ).hexdigest()
    req = urllib.request.Request(
        "http://journal:8090" + path,
        data=body if method == "POST" else None,
        method=method,
        headers={
            "Content-Type": "application/json",
            "X-Varal-Key-Id": key_id,
            "X-Varal-Body-SHA256": digest,
            "X-Varal-Signature": signature,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


epoch, operation, owner, fence_id = (
    os.environ[k] for k in ("LAB_EPOCH", "LAB_OPERATION", "LAB_OWNER", "LAB_FENCE")
)
base = {"version": 1, "epoch": epoch, "fence_id": fence_id}
if sys.argv[1] == "seal":
    assert (
        request(
            "POST",
            "/v1/fence",
            "fence-v1",
            "/run/keys/fence",
            dict(base, action="DRAIN"),
        )[0]
        == 200
    )
    assert (
        request(
            "POST",
            "/v1/fence",
            "fence-v1",
            "/run/keys/fence",
            dict(base, action="SEAL"),
        )[0]
        == 409
    )
    terminal = {
        "version": 1,
        "epoch": epoch,
        "operation_id": operation,
        "owner_id": owner,
        "kind": "ABORT",
        "fence": 1,
        "prepare_seq": 1,
    }
    assert (
        request("POST", "/v1/records", "writer-v1", "/run/keys/writer", terminal)[0]
        == 201
    )
    status, result = request(
        "POST", "/v1/fence", "fence-v1", "/run/keys/fence", dict(base, action="SEAL")
    )
    assert status == 200 and result["fence"]["state"] == "sealed"
elif sys.argv[1] != "restart":
    raise SystemExit(1)
nonce = "ab" * 32
status, result = request(
    "GET", "/v1/fence?nonce=" + nonce, "restore-v1", "/run/keys/restore"
)
assert (
    status == 200
    and result["fence"]["state"] == "sealed"
    and result["fence"]["fence_id"] == fence_id
)
freshness = result["freshness"]
signature = freshness.pop("mac")
key = Path("/run/keys/receipt").read_bytes().rstrip()
assert hmac.compare_digest(
    signature,
    hmac.new(
        key, b"varal-journal-fence-read-v1\n" + canonical(freshness), hashlib.sha256
    ).hexdigest(),
)
assert freshness["nonce"] == nonce and freshness["seq"] == result["fence"]["seq"]
if sys.argv[1] == "restart":
    assert (
        request(
            "POST",
            "/v1/fence",
            "restore-v1",
            "/run/keys/restore",
            dict(base, action="RELEASE"),
        )[0]
        == 403
    )
    assert (
        request(
            "POST",
            "/v1/fence",
            "fence-v1",
            "/run/keys/fence",
            dict(base, action="RELEASE"),
        )[0]
        == 200
    )
