"""Stop only the relay whose PID and edge ID were recorded by this laboratory."""

import argparse
import os
import signal
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("lab_dir")
args = parser.parse_args()
root = Path(args.lab_dir)
if root.parent != Path("/tmp") or not root.name.startswith("varal11-stack."):
    raise SystemExit("invalid laboratory directory")
pidfile = root / "relay.pid"
pid_text, edge_id = pidfile.read_text().splitlines()
pid = int(pid_text)
try:
    command = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
except FileNotFoundError:
    pidfile.unlink()
    raise SystemExit(0)
if (
    not any(
        Path(arg.decode(errors="ignore")).name == "lab11-loopback.py" for arg in command
    )
    or edge_id.encode() not in command
):
    raise SystemExit("refusing to stop a process that is not this relay")
os.kill(pid, signal.SIGTERM)
pidfile.unlink()
print("local TLS relay stopped")
