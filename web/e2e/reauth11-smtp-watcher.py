"""Host-only CA06 lab watcher. Never log message, code, session, or headers."""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

if sys.argv[1:] != ["--run-isolated-lab"]:
    raise SystemExit("Explicit --run-isolated-lab required")
raw_dir = os.environ.get("LAB_DIR", "")
lab = Path(raw_dir).resolve(strict=True)
if str(lab) != raw_dir or not re.fullmatch(
    r"/tmp/varal11-stack\.[A-Za-z0-9]{8}", raw_dir
):
    raise SystemExit("Invalid lab path")
project = lab.name.replace(".", "-").lower()
smtp_id = os.environ.get("CA06_SMTP_ID", "")
browser_id = os.environ.get("CA06_BROWSER_ID", "")
if not all(re.fullmatch(r"[a-f0-9]{12,64}", value) for value in (smtp_id, browser_id)):
    raise SystemExit("Explicit container IDs required")


def docker(*args, data=None, timeout=20):
    # No shell and no inherited stdout/stderr: nothing sensitive goes to a terminal or log.
    return subprocess.run(
        ["docker", *args],
        input=data,
        capture_output=True,
        check=True,
        timeout=timeout,
    ).stdout


def inspect(cid):
    return json.loads(docker("inspect", cid))[0]


smtp = inspect(smtp_id)
browser = inspect(browser_id)
sl = smtp["Config"]["Labels"]
bl = browser["Config"]["Labels"]
if not (
    smtp["State"]["Running"]
    and smtp["Id"].startswith(smtp_id)
    and sl.get("com.docker.compose.project") == project
    and sl.get("com.docker.compose.service") == "smtp-capture"
    and str(smtp["Config"]["User"]).split(":")[0] == "10002"
    and browser["State"]["Running"]
    and browser["Id"].startswith(browser_id)
    and bl.get("varal.lab") == project
    and bl.get("varal.role") == "browser-qa"
    and str(browser["Config"]["User"]).split(":")[0] == "1001"
    and all(m.get("Destination") != "/var/run/docker.sock" for m in browser["Mounts"])
):
    raise SystemExit("Refusing unrelated containers")

# Only synthetic metadata leaves the browser; never output it in the watcher log.
meta_code = """const fs=require('fs');const p='/qa/ca06-meta.json';
if ((fs.statSync(p).mode & 0o077) !== 0) process.exit(2);
process.stdout.write(JSON.parse(fs.readFileSync(p,'utf8')).email);"""
recipient = (
    docker("exec", "-u", "1001:1001", browser_id, "node", "-e", meta_code)
    .decode()
    .strip()
)
if not re.fullmatch(r"ca06-code-[a-f0-9]{32}@example\.invalid", recipient):
    raise SystemExit("Invalid synthetic recipient")

find_message = r"""
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses
from pathlib import Path
import sys
target = sys.stdin.read().strip().lower()
matches = []
for path in Path('/capture').glob('*.eml'):
    try:
        msg = BytesParser(policy=policy.default).parsebytes(path.read_bytes(), headersonly=True)
        addresses = [address.lower() for _, address in getaddresses(msg.get_all('To', []))]
        if target in addresses:
            matches.append(path.name)
    except (OSError, ValueError):
        continue
if len(matches) == 1:
    print(matches[0])
elif len(matches) > 1:
    sys.exit(2)
"""
filename = ""
deadline = time.monotonic() + 100
while time.monotonic() < deadline:
    filename = (
        docker(
            "exec",
            "-i",
            "-u",
            "10002:10002",
            smtp_id,
            "python",
            "-c",
            find_message,
            data=recipient.encode(),
        )
        .decode()
        .strip()
    )
    if filename:
        break
    time.sleep(0.5)
if not re.fullmatch(r"[a-f0-9-]{36}\.eml", filename):
    raise SystemExit("Matching SMTP message unavailable")

# Stream the selected synthetic message directly between the two isolated containers.
# No message or code reaches a terminal, log, argument, or persistent raw-mail artifact.
read_mail = """from pathlib import Path
import sys
sys.stdout.buffer.write((Path('/capture') / sys.argv[1]).read_bytes())
"""
parse_mail = r"""from email import policy
from email.parser import BytesParser
from email.utils import getaddresses
import json, os, re, sys
recipient = json.load(open('/qa/ca06-meta.json'))['email'].lower()
message = BytesParser(policy=policy.default).parsebytes(sys.stdin.buffer.read(10485760))
addresses = [value.lower() for _, value in getaddresses(message.get_all('To', []))]
if recipient not in addresses:
    raise SystemExit(2)
parts = message.walk() if message.is_multipart() else [message]
found = set()
for part in parts:
    if part.get_content_type() == 'text/plain':
        for line in part.get_content().splitlines():
            candidate = line.strip()
            if re.fullmatch(r'[BCDFGHJKLMNPQRSTVWXZ]{4}-[BCDFGHJKLMNPQRSTVWXZ]{4}', candidate):
                found.add(candidate)
if len(found) != 1:
    raise SystemExit(3)
fd = os.open('/qa/ca06-code.txt', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'w', encoding='ascii') as output:
    output.write(found.pop())
    output.flush()
    os.fsync(output.fileno())
"""
reader = subprocess.Popen(
    [
        "docker",
        "exec",
        "-u",
        "10002:10002",
        smtp_id,
        "python",
        "-c",
        read_mail,
        filename,
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
)
try:
    writer = subprocess.run(
        [
            "docker",
            "exec",
            "-i",
            "-u",
            "1001:1001",
            browser_id,
            "python3",
            "-c",
            parse_mail,
        ],
        stdin=reader.stdout,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=30,
        check=False,
    )
finally:
    if reader.stdout:
        reader.stdout.close()
    try:
        reader_code = reader.wait(timeout=30)
    except subprocess.TimeoutExpired:
        reader.terminate()
        reader_code = reader.wait(timeout=10)
if reader_code or writer.returncode:
    raise SystemExit("SMTP-to-browser private pipe failed")
print("CA06_SMTP_CAPTURED=True")
