"""Seal successful journal/WAL initialization before PostgreSQL can start."""

import json
import os
import sys
from pathlib import Path

try:
    marker = Path("/bootstrap/initialized.json")
    metadata = json.loads(marker.read_text())
    if metadata["epoch"] != os.environ["JOURNAL_EPOCH"] or not all(
        Path(path).is_file() for path in (
            "/state/journal/journal.jsonl", "/state/checkpoint/checkpoint.json",
            "/state/checkpoint/fence.json", "/state/wal-archive/manifest.jsonl",
            "/state/wal-anchor/checkpoint.json",
        )
    ):
        raise ValueError("incomplete state")
    if not metadata["sealed"]:
        metadata["sealed"] = True
        temporary = marker.with_suffix(".tmp")
        with temporary.open("w") as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump(metadata, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, marker)
        descriptor = os.open(marker.parent, os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    print("stack initialization sealed")
except Exception:
    print("stack initialization sealing unavailable", file=sys.stderr)
    sys.exit(1)
