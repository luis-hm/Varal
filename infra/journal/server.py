"""Private, single-writer deletion journal. See docs/arquitetura/protocolo-journal.md."""

import argparse
import fcntl
import hashlib
import hmac
import json
import os
import re
import threading
import uuid
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

ZERO = "0" * 64
FIELDS = {
    "version",
    "epoch",
    "operation_id",
    "owner_id",
    "kind",
    "fence",
    "prepare_seq",
}


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("ascii")


def mac(key, domain, value):
    return hmac.new(
        key, domain.encode() + b"\n" + canonical(value), hashlib.sha256
    ).hexdigest()


def uuid_ok(value):
    try:
        return isinstance(value, str) and str(uuid.UUID(value)) == value
    except ValueError:
        return False


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class Invalid(Exception):
    pass


class Conflict(Exception):
    pass


class Closed(Exception):
    pass


class Journal:
    def __init__(
        self, directory, checkpoint_dir, epoch, chain_key, receipt_key, checkpoint_key
    ):
        self.directory, self.checkpoint_dir = Path(directory), Path(checkpoint_dir)
        if self.directory.resolve() == self.checkpoint_dir.resolve():
            raise Invalid("checkpoint directory must be independent")
        self.epoch = epoch
        self.chain_key, self.receipt_key, self.checkpoint_key = (
            chain_key,
            receipt_key,
            checkpoint_key,
        )
        self.path = self.directory / "journal.jsonl"
        self.checkpoint = self.checkpoint_dir / "checkpoint.json"
        self.fence_path = self.checkpoint_dir / "fence.json"
        self.lock = threading.Lock()
        self.lockfile = open(self.directory / "writer.lock", "a+b")  # noqa: SIM115 -- Held for the writer's lifetime.
        fcntl.flock(self.lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.records = []
        self.failed = False
        try:
            self.recover()
            self.load_fence()
        except BaseException:
            self.lockfile.close()
            raise

    def checkpoint_for(self, seq, chain_mac):
        value = {
            "version": 1,
            "epoch": self.epoch,
            "seq": seq,
            "mac": chain_mac,
            "checkpoint_key_id": "checkpoint-v1",
        }
        value["checkpoint_mac"] = mac(
            self.checkpoint_key, "varal-journal-checkpoint-v1", value
        )
        return value

    def save_checkpoint(self, value):
        temp = self.checkpoint_dir / "checkpoint.tmp"
        with open(temp, "wb") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(canonical(value) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, self.checkpoint)
        sync_dir(self.checkpoint_dir)

    def recover(self):
        if not self.path.is_file() or not self.checkpoint.is_file():
            raise Invalid("missing anchor")
        cp = json.loads(self.checkpoint.read_bytes())
        if (
            cp != self.checkpoint_for(cp.get("seq"), cp.get("mac"))
            or type(cp["seq"]) is not int
            or cp["seq"] < 0
        ):
            raise Invalid("invalid checkpoint")
        content = self.path.read_bytes()
        lines = content.splitlines(keepends=True)
        previous = ZERO
        valid_bytes = 0
        for line in lines:
            if not line.endswith(b"\n"):
                if len(self.records) < cp["seq"]:
                    raise Invalid("truncated acknowledged record")
                break
            try:
                record = json.loads(line)
                signature = record.pop("mac")
                expected = mac(self.chain_key, "varal-journal-record-v1", record)
                if (
                    not hmac.compare_digest(signature, expected)
                    or record["seq"] != len(self.records) + 1
                    or record["prev_mac"] != previous
                    or record["epoch"] != self.epoch
                    or record["chain_key_id"] != "chain-v1"
                ):
                    raise Invalid("invalid chain")
                record["mac"] = signature
                if canonical(record) + b"\n" != line:
                    raise Invalid("noncanonical record")
                self.validate_recovered(record)
            except (ValueError, KeyError, TypeError) as exc:
                raise Invalid("invalid record") from exc
            self.records.append(record)
            previous = signature
            valid_bytes += len(line)
        if (
            cp["seq"] > len(self.records)
            or (cp["seq"] and self.records[cp["seq"] - 1]["mac"] != cp["mac"])
            or (cp["seq"] == 0 and cp["mac"] != ZERO)
        ):
            raise Invalid("checkpoint mismatch")
        with open(self.path, "r+b") as stream:
            if valid_bytes != len(content):
                stream.truncate(valid_bytes)
            stream.flush()
            os.fsync(stream.fileno())
        for record in self.records[cp["seq"] :]:
            self.save_checkpoint(self.checkpoint_for(record["seq"], record["mac"]))

    def fence_receipt(self, state, fence_id, seq, record_mac):
        value = {
            "version": 1,
            "epoch": self.epoch,
            "fence_id": fence_id,
            "state": state,
            "seq": seq,
            "record_mac": record_mac,
            "key_id": "receipt-v1",
        }
        value["mac"] = mac(self.receipt_key, "varal-journal-fence-v1", value)
        return value

    def load_fence(self):
        if not self.fence_path.is_file():
            raise Invalid("fence anchor missing")
        data = json.loads(self.fence_path.read_bytes())
        if not isinstance(data, dict) or set(data) != {
            "version",
            "epoch",
            "fence_id",
            "state",
            "seq",
            "record_mac",
            "key_id",
            "mac",
        }:
            raise Invalid("invalid fence")
        if (
            data["state"] not in ("open", "drain", "sealed")
            or type(data["seq"]) is not int
            or not 0 <= data["seq"] <= len(self.records)
        ):
            raise Invalid("invalid fence")
        if data["state"] == "open":
            if data["fence_id"] is not None:
                raise Invalid("invalid fence")
        elif not uuid_ok(data["fence_id"]):
            raise Invalid("invalid fence")
        record_mac = self.records[data["seq"] - 1]["mac"] if data["seq"] else ZERO
        if data != self.fence_receipt(
            data["state"], data["fence_id"], data["seq"], record_mac
        ):
            raise Invalid("invalid fence")
        if data["state"] == "sealed" and data["seq"] != len(self.records):
            raise Invalid("sealed checkpoint changed")
        self.fence = data

    def save_fence(self, receipt):
        temp = self.checkpoint_dir / "fence.tmp"
        with open(temp, "wb") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(canonical(receipt) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, self.fence_path)
        sync_dir(self.checkpoint_dir)
        self.fence = receipt

    def transition_fence(self, request):
        if (
            not isinstance(request, dict)
            or set(request) != {"version", "epoch", "fence_id", "action"}
            or type(request["version"]) is not int
            or request["version"] != 1
            or request["epoch"] != self.epoch
            or not uuid_ok(request["fence_id"])
            or request["action"] not in ("DRAIN", "SEAL", "RELEASE")
        ):
            raise Invalid("invalid fence request")
        with self.lock:
            if self.failed:
                raise OSError("journal unavailable")
            old, action, fence_id = self.fence, request["action"], request["fence_id"]
            if action == "DRAIN":
                if old["state"] == "drain" and old["fence_id"] == fence_id:
                    return old
                if old["state"] != "open":
                    raise Conflict()
                state = "drain"
            elif action == "SEAL":
                if old["state"] == "sealed" and old["fence_id"] == fence_id:
                    return old
                if old["state"] != "drain" or old["fence_id"] != fence_id:
                    raise Conflict()
                pending = {
                    r["operation_id"] for r in self.records if r["kind"] == "PREPARE"
                }
                pending.difference_update(
                    r["operation_id"]
                    for r in self.records
                    if r["kind"] in ("COMMIT", "ABORT")
                )
                if pending:
                    raise Conflict()
                state = "sealed"
            else:
                if (
                    old["state"] not in ("drain", "sealed")
                    or old["fence_id"] != fence_id
                ):
                    raise Conflict()
                state, fence_id = "open", None
            seq = len(self.records)
            receipt = self.fence_receipt(
                state, fence_id, seq, self.records[-1]["mac"] if seq else ZERO
            )
            try:
                self.save_fence(receipt)
            except OSError:
                self.failed = True
                raise
            return receipt

    def validate_recovered(self, record):
        request = {key: record[key] for key in FIELDS}
        self.validate_request(request)
        if self.check_conflicts(request) is not None:
            raise Invalid("duplicate record")

    def validate_request(self, request):
        if (
            not isinstance(request, dict)
            or set(request) != FIELDS
            or type(request["version"]) is not int
            or request["version"] != 1
            or request["epoch"] != self.epoch
            or not all(
                uuid_ok(request[k]) for k in ("epoch", "operation_id", "owner_id")
            )
            or request["kind"] not in ("PREPARE", "COMMIT", "ABORT")
            or type(request["fence"]) is not int
            or request["fence"] < 1
        ):
            raise Invalid("invalid input")
        if request["kind"] == "PREPARE":
            if request["prepare_seq"] is not None:
                raise Invalid("invalid prepare")
        elif type(request["prepare_seq"]) is not int or request["prepare_seq"] < 1:
            raise Invalid("invalid terminal")

    def check_conflicts(self, request):
        operation = [
            r for r in self.records if r["operation_id"] == request["operation_id"]
        ]
        same = next((r for r in operation if r["kind"] == request["kind"]), None)
        if same:
            if {k: same[k] for k in FIELDS} != request:
                raise Conflict()
            return same
        if request["kind"] == "PREPARE":
            if operation:
                raise Conflict()
        else:
            prepare = next((r for r in operation if r["kind"] == "PREPARE"), None)
            if (
                not prepare
                or any(r["kind"] != "PREPARE" for r in operation)
                or any(prepare[k] != request[k] for k in ("owner_id", "epoch", "fence"))
                or prepare["seq"] != request["prepare_seq"]
            ):
                raise Conflict()
        return None

    def receipt(self, record):
        req = {key: record[key] for key in FIELDS}
        cp = self.checkpoint_for(record["seq"], record["mac"])
        value = dict(
            req,
            request_digest=hashlib.sha256(canonical(req)).hexdigest(),
            seq=record["seq"],
            record_mac=record["mac"],
            checkpoint_seq=cp["seq"],
            checkpoint_mac=cp["checkpoint_mac"],
            receipt_key_id="receipt-v1",
        )
        value["receipt_mac"] = mac(self.receipt_key, "varal-journal-receipt-v1", value)
        return value

    def append(self, request):
        with self.lock:
            if self.failed:
                raise OSError("journal unavailable")
            self.validate_request(request)
            existing = self.check_conflicts(request)
            if existing:
                return False, self.receipt(existing)
            if self.fence["state"] == "sealed" or (
                self.fence["state"] == "drain" and request["kind"] == "PREPARE"
            ):
                raise Closed()
            record = dict(
                request,
                seq=len(self.records) + 1,
                recorded_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                prev_mac=self.records[-1]["mac"] if self.records else ZERO,
                chain_key_id="chain-v1",
            )
            record["mac"] = mac(self.chain_key, "varal-journal-record-v1", record)
            try:
                with open(self.path, "ab") as stream:
                    stream.write(canonical(record) + b"\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                self.save_checkpoint(self.checkpoint_for(record["seq"], record["mac"]))
            except OSError:
                self.failed = True
                raise
            self.records.append(record)
            return True, self.receipt(record)


def initialize(directory, checkpoint_dir, epoch, checkpoint_key, receipt_key):
    if not uuid_ok(epoch):
        raise Invalid("invalid epoch")
    directory, checkpoint_dir = Path(directory), Path(checkpoint_dir)
    if directory.resolve() == checkpoint_dir.resolve():
        raise Invalid("checkpoint directory must be independent")
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    checkpoint_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    path, cp = directory / "journal.jsonl", checkpoint_dir / "checkpoint.json"
    fence_path = checkpoint_dir / "fence.json"
    # Never initialize over an existing or partially initialized journal.
    if path.exists() or cp.exists() or fence_path.exists():
        raise Invalid("already initialized")
    with open(path, "xb") as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.flush()
        os.fsync(stream.fileno())
    sync_dir(directory)
    checkpoint = {
        "version": 1,
        "epoch": epoch,
        "seq": 0,
        "mac": ZERO,
        "checkpoint_key_id": "checkpoint-v1",
    }
    checkpoint["checkpoint_mac"] = mac(
        checkpoint_key, "varal-journal-checkpoint-v1", checkpoint
    )
    with open(cp, "xb") as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(canonical(checkpoint) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())
    fence = {
        "version": 1,
        "epoch": epoch,
        "fence_id": None,
        "state": "open",
        "seq": 0,
        "record_mac": ZERO,
        "key_id": "receipt-v1",
    }
    fence["mac"] = mac(receipt_key, "varal-journal-fence-v1", fence)
    with open(fence_path, "xb") as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(canonical(fence) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())
    sync_dir(checkpoint_dir)


class PrivateServer(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, _request, _client_address):
        # Raw exceptions can contain untrusted request data.
        pass


class Handler(BaseHTTPRequestHandler):
    server_version = "varal-journal"
    sys_version = ""

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def log_message(self, *_args):
        pass

    def reply(self, status, body):
        encoded = canonical(body)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def authenticate(self, body):
        key_id = self.headers.get("X-Varal-Key-Id", "")
        key = self.server.auth_keys.get(key_id)
        digest = hashlib.sha256(body).hexdigest()
        supplied = self.headers.get("X-Varal-Body-SHA256", "")
        signature = self.headers.get("X-Varal-Signature", "")
        try:
            payload = f"varal-journal-request-v1\n{self.command}\n{self.path}\n{digest}\n{key_id}".encode(
                "ascii"
            )
        except UnicodeEncodeError:
            return False
        expected = hmac.new(key or b"invalid", payload, hashlib.sha256).hexdigest()
        return bool(
            key
            and hmac.compare_digest(digest, supplied)
            and hmac.compare_digest(expected, signature)
        )

    def do_POST(self):
        if self.server.failed:
            return self.reply(503, {"error": "unavailable"})
        try:
            if (
                self.path not in ("/v1/records", "/v1/fence")
                or self.headers.get("Content-Type") != "application/json"
                or self.headers.get("Transfer-Encoding")
            ):
                return self.reply(400, {"error": "invalid_request"})
            length = int(self.headers.get("Content-Length", "-1"))
            if length > 4096:
                return self.reply(413, {"error": "too_large"})
            if length < 0:
                return self.reply(400, {"error": "invalid_request"})
            body = self.rfile.read(length)
            if not self.authenticate(body):
                return self.reply(401, {"error": "unauthorized"})
            required_key = "fence-v1" if self.path == "/v1/fence" else "writer-v1"
            if self.headers["X-Varal-Key-Id"] != required_key:
                return self.reply(403, {"error": "forbidden"})
            request = json.loads(body, object_pairs_hook=reject_duplicates)
            if self.path == "/v1/fence":
                return self.reply(
                    200, {"fence": self.server.journal.transition_fence(request)}
                )
            created, receipt = self.server.journal.append(request)
            self.reply(201 if created else 200, {"receipt": receipt})
        except Conflict:
            self.reply(409, {"error": "conflict"})
        except Closed:
            self.reply(503, {"error": "unavailable"})
        except (Invalid, ValueError, TypeError, KeyError):
            self.reply(400, {"error": "invalid_request"})
        except OSError:
            self.server.failed = True
            self.reply(503, {"error": "unavailable"})

    def do_GET(self):
        if not self.authenticate(b""):
            return self.reply(401, {"error": "unauthorized"})
        if self.server.failed:
            return self.reply(503, {"error": "unavailable"})
        key_id = self.headers["X-Varal-Key-Id"]
        with self.server.journal.lock:
            if self.server.journal.failed:
                return self.reply(503, {"error": "unavailable"})
            if self.path.startswith("/v1/fence"):
                if key_id not in ("restore-v1", "fence-v1"):
                    return self.reply(403, {"error": "forbidden"})
                match = re.fullmatch(r"/v1/fence\?nonce=([0-9a-f]{64})", self.path)
                if not match:
                    return self.reply(400, {"error": "invalid_request"})
                fence = self.server.journal.fence
                freshness = {
                    key: fence[key]
                    for key in (
                        "version",
                        "epoch",
                        "fence_id",
                        "state",
                        "seq",
                        "record_mac",
                        "key_id",
                    )
                }
                freshness["nonce"] = match.group(1)
                freshness["mac"] = mac(
                    self.server.journal.receipt_key,
                    "varal-journal-fence-read-v1",
                    freshness,
                )
                return self.reply(200, {"fence": fence, "freshness": freshness})
            match = re.fullmatch(r"/v1/operations/([0-9a-f-]{36})", self.path)
            if match and uuid_ok(match.group(1)):
                records = [
                    r
                    for r in self.server.journal.records
                    if r["operation_id"] == match.group(1)
                ]
                if not records:
                    return self.reply(404, {"error": "not_found"})
                return self.reply(
                    200, {"receipts": [self.server.journal.receipt(r) for r in records]}
                )
            if key_id != "restore-v1":
                return self.reply(403, {"error": "forbidden"})
            parsed = urlsplit(self.path)
            pairs = parse_qsl(parsed.query, keep_blank_values=True)
            if (
                parsed.path != "/v1/records"
                or len(pairs) != 2
                or [k for k, _ in pairs] != ["after", "limit"]
                or not all(re.fullmatch(r"0|[1-9][0-9]*", v) for _, v in pairs)
            ):
                return self.reply(400, {"error": "invalid_request"})
            after, limit = (int(v) for _, v in pairs)
            if not 1 <= limit <= 500:
                return self.reply(400, {"error": "invalid_request"})
            records = self.server.journal.records
            cp = self.server.journal.checkpoint_for(
                len(records), records[-1]["mac"] if records else ZERO
            )
            self.reply(
                200, {"records": records[after : after + limit], "checkpoint": cp}
            )


def reject_duplicates(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate key")
        value[key] = item
    return value


def read_key(path):
    value = Path(path).read_bytes().rstrip()
    if len(value) < 32:
        raise Invalid("key too short")
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--directory", required=True)
    parser.add_argument("--checkpoint-directory", required=True)
    parser.add_argument("--epoch", required=True)
    for key in ("chain", "receipt", "checkpoint", "writer", "restore", "fence"):
        parser.add_argument("--" + key + "-key-file", required=True)
    parser.add_argument("--listen", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8090)
    args = parser.parse_args()
    chain, receipt, checkpoint, writer, restore, fence = [
        read_key(getattr(args, k + "_key_file"))
        for k in ("chain", "receipt", "checkpoint", "writer", "restore", "fence")
    ]
    if len({chain, receipt, checkpoint, writer, restore, fence}) != 6:
        raise Invalid("keys must be distinct")
    if args.init:
        initialize(
            args.directory, args.checkpoint_directory, args.epoch, checkpoint, receipt
        )
        return
    journal = Journal(
        args.directory,
        args.checkpoint_directory,
        args.epoch,
        chain,
        receipt,
        checkpoint,
    )
    server = PrivateServer((args.listen, args.port), Handler)
    server.journal, server.auth_keys, server.failed = (
        journal,
        {"writer-v1": writer, "restore-v1": restore, "fence-v1": fence},
        False,
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
