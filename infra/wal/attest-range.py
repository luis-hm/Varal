"""Verify an archived WAL range and emit its authenticated checkpoint."""
import json
import sys
from pathlib import Path

from verify import verify

archive, anchor, epoch, system_id, cipher_file, witness_file, first, last = sys.argv[1:]
checkpoint_path = Path(anchor) / "checkpoint.json"
before = checkpoint_path.read_bytes()
sequence = verify(
    archive,
    anchor,
    epoch,
    system_id,
    bytes.fromhex(Path(cipher_file).read_text().strip()),
    Path(witness_file).read_bytes().rstrip(),
    first,
    last,
)
if checkpoint_path.read_bytes() != before:
    raise RuntimeError("checkpoint changed")
checkpoint = json.loads(before)
if checkpoint["sequence"] != sequence:
    raise RuntimeError("checkpoint mismatch")
print(json.dumps({"sequence": sequence, "chain_mac": checkpoint["chain_mac"]}, sort_keys=True, separators=(",", ":")))
