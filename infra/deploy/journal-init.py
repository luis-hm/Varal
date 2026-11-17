"""Idempotent init wrapper: complete state is verified; partial state fails closed."""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, "/srv/journal")
from server import initialize, mac, read_key  # noqa: E402

try:
    directory, checkpoint = Path("/varal/journal"), Path("/varal/checkpoint")
    epoch = os.environ["JOURNAL_EPOCH"]
    keys = {name: read_key(f"/run/keys/{name}/key") for name in (
        "chain", "receipt", "checkpoint", "writer", "restore", "fence"
    )}
    if len(set(keys.values())) != 6:
        raise ValueError("capabilities must be distinct")
    if not any(directory.iterdir()) and not any(checkpoint.iterdir()):
        initialize(directory, checkpoint, epoch, keys["checkpoint"], keys["receipt"])
    # A running writer may hold its lock across a rolling deployment. Verify signed anchors
    # without taking that lock; the journal process performs full recovery before listening.
    if not (directory / "journal.jsonl").is_file():
        raise ValueError("journal missing")
    anchor = json.loads((checkpoint / "checkpoint.json").read_bytes())
    unsigned = {key: value for key, value in anchor.items() if key != "checkpoint_mac"}
    if anchor.get("epoch") != epoch or anchor.get("checkpoint_mac") != mac(
        keys["checkpoint"], "varal-journal-checkpoint-v1", unsigned
    ):
        raise ValueError("checkpoint invalid")
    fence = json.loads((checkpoint / "fence.json").read_bytes())
    unsigned = {key: value for key, value in fence.items() if key != "mac"}
    if fence.get("epoch") != epoch or fence.get("mac") != mac(
        keys["receipt"], "varal-journal-fence-v1", unsigned
    ):
        raise ValueError("fence invalid")
    print("journal initialization verified")
except Exception:
    print("journal initialization unavailable", file=sys.stderr)
    sys.exit(1)
