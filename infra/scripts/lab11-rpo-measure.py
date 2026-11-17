"""Measure a laboratory's observed WAL commit gap without logging WAL contents.

The first segment must be at or before the recovered commit. The result is an
observation for this fixture, not a guarantee of RPO or a complete loss audit.
"""
import argparse
import datetime
import hashlib
import hmac
import json
import re
import signal
import subprocess
import sys
import uuid
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def lsn(value):
    if not re.fullmatch(r"[0-9A-F]{1,8}/[0-9A-F]{1,8}", value):
        raise ValueError("invalid LSN")
    high, low = value.split("/")
    return (int(high, 16) << 32) | int(low, 16)


def receipt(path, key, domain):
    data = json.loads(path.read_bytes())
    mac = data.pop("mac")
    if not hmac.compare_digest(mac, hmac.new(key, domain + canonical(data), hashlib.sha256).hexdigest()):
        raise ValueError("invalid receipt")
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("lab_dir", type=Path)
    parser.add_argument("operation")
    parser.add_argument("first_segment")
    args = parser.parse_args()
    lab = args.lab_dir
    if lab.parent != Path("/tmp") or not lab.name.startswith("varal11-stack."):
        raise ValueError("invalid lab")
    project = (lab / "project").read_text().strip()
    if project != lab.name.lower().replace(".", "-") or str(uuid.UUID(args.operation)) != args.operation:
        raise ValueError("invalid operation")
    if not re.fullmatch(r"[0-9A-F]{24}", args.first_segment):
        raise ValueError("invalid first segment")
    key = (lab / "keys/restore-proof").read_bytes().rstrip()
    proof = receipt(lab / f"restore-proof-{args.operation}.json", key, b"varal-restore-proof-v1\n")
    ledger = receipt(lab / f"restore-ledger-{args.operation}.json", key, b"varal-restore-ledger-gate-v1\n")
    if proof["operation_id"] != args.operation or ledger["operation_id"] != args.operation:
        raise ValueError("operation mismatch")
    if any(proof[field] != ledger[field] for field in ("epoch", "fence_id", "system_identifier")):
        raise ValueError("receipt mismatch")
    timeline = proof["timeline"]
    if args.first_segment[:8] != timeline or not re.fullmatch(r"[0-9A-F]{8}", timeline):
        raise ValueError("timeline mismatch")
    watermark = lsn(ledger["watermark_lsn"])
    replay = lsn(proof["replay_lsn"])
    # PostgreSQL names a boundary LSN as the preceding 16 MiB segment.
    end_ordinal = (watermark - 1) // 0x1000000
    last = timeline + f"{end_ordinal // 256:08X}{end_ordinal % 256:08X}"
    volume = f"{project}_rpo_wal_{uuid.uuid4().hex}"
    existing = subprocess.run(["docker", "volume", "inspect", volume], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    if existing.returncode == 0:
        raise ValueError("temporary volume exists")
    subprocess.run(["docker", "volume", "create", "--label", "varal.role=rpo-evidence", "--label", f"varal.parent={project}", volume], check=True, stdout=subprocess.DEVNULL)
    try:
        subprocess.run(["docker", "run", "--rm", "--network", "none", "-v", f"{volume}:/restore", "--entrypoint", "chown", "python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b", "70:70", "/restore"], check=True, stdout=subprocess.DEVNULL)
        export = ["docker", "run", "--rm", "--network", "none", "--entrypoint", "python", "-v", f"{project}_wal_archive:/varal/wal-archive:ro", "-v", f"{project}_wal_anchor:/varal/wal-anchor:ro", "-v", f"{volume}:/varal/restore-wal", "-v", f"{lab}/keys/wal-cipher:/run/keys/cipher:ro", "-v", f"{lab}/keys/wal-witness:/run/keys/witness:ro", "varal11-wal-lab:local", "/srv/export.py", "--archive", "/varal/wal-archive", "--anchor", "/varal/wal-anchor", "--output", "/varal/restore-wal", "--epoch", proof["epoch"], "--system-identifier", proof["system_identifier"], "--cipher-key", "/run/keys/cipher", "--witness-key", "/run/keys/witness", "--first", args.first_segment, "--last", last]
        subprocess.run(export, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        start = (int(args.first_segment[8:16], 16) << 32) | (int(args.first_segment[16:24], 16) << 24)
        if start > replay or replay > watermark:
            raise ValueError("invalid measurement range")
        start_lsn = f"{start >> 32:X}/{start & 0xFFFFFFFF:X}"
        cmd = ["docker", "run", "--rm", "--network", "none", "-e", "TZ=UTC", "-v", f"{volume}:/wal:ro", "--entrypoint", "pg_waldump", "varal11-postgres-lab:local", "--path=/wal", f"--timeline={int(timeline, 16)}", f"--start={start_lsn}", f"--end={ledger['watermark_lsn']}", "--rmgr=Transaction"]
        output = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
        commits = []
        for line in output.splitlines():
            if "COMMIT" not in line:
                continue
            pos = re.search(r"lsn:\s*([0-9A-F]+/[0-9A-F]+)", line)
            stamp = re.search(r"(\d{4}-\d\d-\d\d\s+\d\d:\d\d:\d\d(?:\.\d+)?\s+UTC)", line)
            if pos and stamp:
                instant = datetime.datetime.fromisoformat(stamp.group(1).replace(" UTC", "+00:00"))
                commits.append((lsn(pos.group(1)), pos.group(1), instant))
        recovered = [record for record in commits if record[0] <= replay]
        source = [record for record in commits if record[0] <= watermark]
        if not recovered or not source:
            raise ValueError("commit timestamps unavailable")
        a, b = max(recovered), max(source)
        gap = (b[2] - a[2]).total_seconds()
        if gap < 0:
            raise ValueError("clock ordering inconsistent")
        print(json.dumps({"scope": "lab WAL commits only; journal exclusions require separate reconciliation", "recovered_commit_lsn": a[1], "recovered_commit_utc": a[2].isoformat(), "source_commit_lsn": b[1], "source_commit_utc": b[2].isoformat(), "observed_commit_gap_seconds": gap, "replay_lsn": proof["replay_lsn"], "source_watermark_lsn": ledger["watermark_lsn"], "commit_records_examined": len(commits)}, sort_keys=True))
    finally:
        removed = subprocess.run(["docker", "volume", "rm", volume], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if removed.returncode:
            print(f"Temporary WAL volume requires cleanup: {volume}", file=sys.stderr)


if __name__ == "__main__":
    def terminate(_signum, _frame):
        raise SystemExit("RPO measurement interrupted; no result claimed")

    signal.signal(signal.SIGTERM, terminate)
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError):
        print("RPO measurement failed; no result claimed", file=sys.stderr)
        sys.exit(1)
