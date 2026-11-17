"""Initialize an empty archive only; verify complete existing anchors on restart."""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, "/srv")
from archive import atomic, canonical, sign  # noqa: E402

try:
    directories = tuple(Path("/varal") / name for name in ("wal-spool", "wal-archive", "wal-acks", "wal-anchor"))
    spool, archive, acks, anchor = directories
    epoch = os.environ["JOURNAL_EPOCH"]
    cipher = bytes.fromhex(Path("/run/keys/wal-cipher/key").read_text().strip())
    witness = Path("/run/keys/wal-witness/key").read_bytes().rstrip()
    if not any(archive.iterdir()) and not any(anchor.iterdir()):
        if any(spool.iterdir()) or any(acks.iterdir()):
            raise ValueError("existing spool without archive anchor")
        atomic(archive / "manifest.jsonl", b"")
        checkpoint = {"version": 1, "epoch": epoch, "sequence": 0, "chain_mac": "0" * 64}
        checkpoint["mac"] = sign(witness, "varal-wal-checkpoint-v1", checkpoint)
        atomic(anchor / "checkpoint.json", canonical(checkpoint) + b"\n")
    if len(cipher) != 32 or not (archive / "manifest.jsonl").is_file():
        raise ValueError("archive missing")
    checkpoint = json.loads((anchor / "checkpoint.json").read_bytes())
    unsigned = {key: value for key, value in checkpoint.items() if key != "mac"}
    if checkpoint.get("epoch") != epoch or checkpoint.get("mac") != sign(
        witness, "varal-wal-checkpoint-v1", unsigned
    ):
        raise ValueError("archive checkpoint invalid")
    # The archive process verifies chain/identity before writing; don't contend for its
    # single-writer lock here when compose recreates an init service during redeploy.
    print("WAL initialization verified")
except Exception:
    print("WAL initialization unavailable", file=sys.stderr)
    sys.exit(1)
