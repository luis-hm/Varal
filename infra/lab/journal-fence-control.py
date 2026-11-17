"""Issue one privileged fence transition on localhost and authenticate its receipt."""
import hashlib
import hmac
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


epoch, fence_id, action = sys.argv[1:]
body = canonical({"version": 1, "epoch": epoch, "fence_id": fence_id, "action": action})
digest = hashlib.sha256(body).hexdigest()
message = f"varal-journal-request-v1\nPOST\n/v1/fence\n{digest}\nfence-v1".encode()
key = Path("/run/keys/fence").read_bytes().rstrip()
signature = hmac.new(key, message, hashlib.sha256).hexdigest()
request = urllib.request.Request(
    "http://127.0.0.1:8090/v1/fence",
    data=body,
    headers={
        "Content-Type": "application/json",
        "X-Varal-Key-Id": "fence-v1",
        "X-Varal-Body-SHA256": digest,
        "X-Varal-Signature": signature,
    },
)
try:
    with urllib.request.urlopen(request, timeout=10) as response:
        receipt = json.load(response)["fence"]
    supplied = receipt["mac"]
    unsigned = {key: value for key, value in receipt.items() if key != "mac"}
    expected = hmac.new(
        Path("/run/keys/receipt").read_bytes().rstrip(),
        b"varal-journal-fence-v1\n" + canonical(unsigned),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(supplied, expected) or receipt["epoch"] != epoch:
        raise ValueError("invalid receipt")
    if action != "RELEASE" and receipt["fence_id"] != fence_id:
        raise ValueError("invalid fence id")
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
except (OSError, ValueError, KeyError, urllib.error.URLError):
    raise SystemExit("fence transition unavailable; cutover remains closed") from None
