"""Start a local-only relay for a verified Compose edge; unsuitable for benchmarks."""

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("lab_dir")
args = parser.parse_args()
root = Path(args.lab_dir)
if root.parent != Path("/tmp") or not root.name.startswith("varal11-stack."):
    raise SystemExit("invalid laboratory directory")
project = (root / "project").read_text().strip()
if project != root.name.lower().replace(".", "-") or not re.fullmatch(
    r"varal11-stack-[a-z0-9]+", project
):
    raise SystemExit("invalid laboratory project")
values = dict(
    line.split("=", 1)
    for line in (root / "lab.env").read_text().splitlines()
    if "=" in line
)
port = int(values["LAB_PORT"])
name = f"{project}-edge-1"
data = json.loads(subprocess.check_output(["docker", "inspect", name], text=True))[0]
labels = data["Config"]["Labels"]
if (
    labels.get("com.docker.compose.project") != project
    or labels.get("com.docker.compose.service") != "edge"
    or not data["State"]["Running"]
):
    raise SystemExit("edge is not the running laboratory service")
pidfile = root / "relay.pid"
if pidfile.exists():
    raise SystemExit("relay pid file already exists; stop or inspect it first")
script = Path(__file__).with_name("lab11-loopback.py").resolve()
process = subprocess.Popen(
    [sys.executable, str(script), "--edge-id", data["Id"], "--port", str(port)],
    stdin=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    start_new_session=True,
)
pidfile.write_text(f"{process.pid}\n{data['Id']}\n")
os.chmod(pidfile, 0o600)
for _ in range(50):
    if process.poll() is not None:
        pidfile.unlink()
        raise SystemExit("relay failed to start")
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
            print(
                f"local TLS relay started on 127.0.0.1:{port}; not valid for benchmarks"
            )
            break
    except OSError:
        time.sleep(0.1)
else:
    process.terminate()
    pidfile.unlink()
    raise SystemExit("relay did not become ready")
