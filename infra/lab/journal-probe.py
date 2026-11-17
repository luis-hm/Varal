"""Send one synthetic authenticated PREPARE to the disposable journal."""
import hashlib
import hmac
import json
import os
import urllib.request
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


body = canonical(
    {
        "version": 1,
        "epoch": os.environ["LAB_EPOCH"],
        "operation_id": os.environ["LAB_OPERATION"],
        "owner_id": os.environ["LAB_OWNER"],
        "kind": "PREPARE",
        "fence": 1,
        "prepare_seq": None,
    }
)
digest = hashlib.sha256(body).hexdigest()
message = f"varal-journal-request-v1\nPOST\n/v1/records\n{digest}\nwriter-v1".encode()
key = Path("/run/keys/writer").read_bytes().rstrip()
signature = hmac.new(key, message, hashlib.sha256).hexdigest()
request = urllib.request.Request(
    "http://journal:8090/v1/records",
    data=body,
    headers={
        "Content-Type": "application/json",
        "X-Varal-Key-Id": "writer-v1",
        "X-Varal-Body-SHA256": digest,
        "X-Varal-Signature": signature,
    },
)
with urllib.request.urlopen(request, timeout=5) as response:
    receipt = json.load(response)["receipt"]
unsigned = {key: value for key, value in receipt.items() if key != "receipt_mac"}
expected = hmac.new(
    Path("/run/keys/receipt").read_bytes().rstrip(),
    b"varal-journal-receipt-v1\n" + canonical(unsigned),
    hashlib.sha256,
).hexdigest()
assert hmac.compare_digest(expected, receipt["receipt_mac"])
assert receipt["epoch"] == os.environ["LAB_EPOCH"] and receipt["seq"] == 1
print(json.dumps(receipt, sort_keys=True))
