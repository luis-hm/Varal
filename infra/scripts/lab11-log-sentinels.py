"""Probe application log sinks with unique synthetic URL/referer sentinels."""

import argparse
import secrets
import subprocess
import sys
import urllib.parse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("lab_dir")
args = parser.parse_args()
root = Path(args.lab_dir)
if root.parent != Path("/tmp") or not root.name.startswith("varal11-stack."):
    raise SystemExit("invalid laboratory directory")
project = (root / "project").read_text().strip()
if project != root.name.lower().replace(".", "-"):
    raise SystemExit("invalid laboratory project")
values = dict(
    line.split("=", 1)
    for line in (root / "lab.env").read_text().splitlines()
    if "=" in line
)
port = int(values["LAB_PORT"])
sentinel = "varal11sentinel" + secrets.token_hex(12)
encoded = "".join(f"%{ord(char):02X}" for char in sentinel)
double = encoded.replace("%", "%25")
paths = [
    f"/c/{sentinel}",
    f"/api/convites/{encoded}/aceitar/?probe={double}",
    f"/api/convites/{double}/?probe={sentinel}",
]
for path in paths:
    result = subprocess.run(
        [
            "curl",
            "--silent",
            "--show-error",
            "--max-time",
            "60",
            "--noproxy",
            "*",
            "--path-as-is",
            "--cacert",
            str(root / "tls/ca.pem"),
            "--resolve",
            f"varal.local:{port}:127.0.0.1",
            "--header",
            f"Referer: https://synthetic.invalid/{double}",
            "--header",
            f"X-Untrusted-Sentinel: {encoded}",
            "--output",
            "/dev/null",
            f"https://varal.local:{port}{path}",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode:
        raise SystemExit("sentinel request transport failed")
for service in (
    "edge",
    "ssr",
    "api",
    "web",
    "worker",
    "beat",
    "storage",
    "journal",
    "wal-archive",
):
    name = f"{project}-{service}-1"
    logs = subprocess.run(["docker", "logs", name], capture_output=True, check=False)
    if logs.returncode:
        raise SystemExit(f"could not inspect {service} sink")
    text = (logs.stdout + logs.stderr).decode("utf-8", "replace")
    for _ in range(4):
        if sentinel.lower() in text.lower():
            print(f"synthetic sentinel found in {service} sink", file=sys.stderr)
            raise SystemExit(1)
        text = urllib.parse.unquote(text)
print("synthetic path/query/referer sentinels absent from inspected service logs")
