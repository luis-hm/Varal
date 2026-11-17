"""Initialize new stack capabilities once; never replace keys or initialized data."""

import json
import os
import secrets
import sys
import uuid
from pathlib import Path

KEYS = ("chain", "receipt", "checkpoint", "writer", "restore", "fence", "wal-cipher", "wal-witness")
STATE_DIRS = {
    "/state/journal": 10001,
    "/state/checkpoint": 10001,
    "/state/wal-spool": 70,
    "/state/wal-archive": 70,
    "/state/wal-acks": 70,
    "/state/wal-anchor": 70,
}


def sync_dir(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main():
    epoch = str(uuid.UUID(os.environ["JOURNAL_EPOCH"]))
    marker = Path("/bootstrap/initialized.json")
    keyfiles = [Path("/keys") / name / "key" for name in KEYS]
    if marker.exists():
        metadata = json.loads(marker.read_text())
        if set(metadata) != {"version", "epoch", "sealed"} or metadata["version"] != 1 or metadata["epoch"] != epoch or type(metadata["sealed"]) is not bool:
            raise ValueError("epoch mismatch")
        values = [path.read_bytes().rstrip() for path in keyfiles]
        if any(len(value) != 64 for value in values) or len(set(values)) != len(values):
            raise ValueError("capability missing or altered")
        for value in values:
            bytes.fromhex(value.decode("ascii"))
        if metadata["sealed"] and not all(Path(path).is_file() for path in (
            "/state/journal/journal.jsonl", "/state/checkpoint/checkpoint.json",
            "/state/checkpoint/fence.json", "/state/wal-archive/manifest.jsonl",
            "/state/wal-anchor/checkpoint.json",
        )):
            raise ValueError("initialized state disappeared; refuse automatic reinitialization")
        if Path("/bootstrap/database.ready").exists() and not Path("/state/postgres/PG_VERSION").is_file():
            raise ValueError("database disappeared; explicit recovery required")
        print("existing stack capabilities verified")
        return
    # Missing marker with partial keys/data is an operator recovery condition, not a new stack.
    if any(Path("/state/postgres").iterdir()) or any(list(path.parent.iterdir()) for path in keyfiles) or any(
        list(Path(directory).iterdir()) for directory in STATE_DIRS
    ):
        raise ValueError("refusing initialization over existing state")
    for directory, owner in STATE_DIRS.items():
        os.chown(directory, owner, owner)
        os.chmod(directory, 0o700 if "wal-acks" not in directory else 0o755)
    os.chown(marker.parent, 0, 70)
    marker.parent.chmod(0o770)
    for path in keyfiles:
        path.parent.chmod(0o755)
        with path.open("xb") as stream:
            os.fchmod(stream.fileno(), 0o444)
            stream.write(secrets.token_hex(32).encode("ascii") + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        sync_dir(path.parent)
    with marker.open("x") as stream:
        os.fchmod(stream.fileno(), 0o600)
        json.dump({"version": 1, "epoch": epoch, "sealed": False}, stream)
        stream.flush()
        os.fsync(stream.fileno())
    sync_dir(marker.parent)
    print("new stack capabilities initialized")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("stack initialization refused; inspect persistent state securely", file=sys.stderr)
        sys.exit(1)
