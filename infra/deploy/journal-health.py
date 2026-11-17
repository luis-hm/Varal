"""Check an authenticated, deliberately nonexistent operation on localhost."""

import hashlib
import hmac
import sys
import urllib.error
import urllib.request
from pathlib import Path

path = "/v1/operations/00000000-0000-0000-0000-000000000000"
digest = hashlib.sha256(b"").hexdigest()
payload = f"varal-journal-request-v1\nGET\n{path}\n{digest}\nwriter-v1".encode()
key = Path("/run/keys/writer/key").read_bytes().rstrip()
signature = hmac.new(key, payload, hashlib.sha256).hexdigest()
request = urllib.request.Request(
    "http://127.0.0.1:8090" + path,
    headers={
        "X-Varal-Key-Id": "writer-v1",
        "X-Varal-Body-SHA256": digest,
        "X-Varal-Signature": signature,
    },
)
try:
    with urllib.request.urlopen(request, timeout=2) as response:
        # A matching operation would still prove the authenticated listener is responding.
        sys.exit(0 if response.status == 200 else 1)
except urllib.error.HTTPError as error:
    sys.exit(0 if error.code == 404 else 1)
except OSError:
    sys.exit(1)
