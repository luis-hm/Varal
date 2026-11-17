"""Single-writer encrypted WAL archive with authenticated, durable witness receipts."""

import argparse
import fcntl
import hashlib
import hmac
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

NAME = re.compile(r"(?:[0-9A-F]{24}(?:\.[0-9A-F]{8}\.backup)?|[0-9A-F]{8}\.history)\Z")
ZERO = "0" * 64


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def sign(key, domain, value):
    return hmac.new(
        key, domain.encode() + b"\n" + canonical(value), hashlib.sha256
    ).hexdigest()


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic(path, payload, mode=0o600):
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as stream:
        os.fchmod(stream.fileno(), mode)
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)
    sync_dir(path.parent)


class Invalid(Exception):
    pass


class Archive:
    def __init__(
        self, spool, archive, acknowledgments, anchor, epoch, cipher_key, witness_key
    ):
        self.spool, self.archive, self.acks, self.anchor = map(
            Path, (spool, archive, acknowledgments, anchor)
        )
        if (
            len(
                {
                    path.resolve()
                    for path in (self.spool, self.archive, self.acks, self.anchor)
                }
            )
            != 4
        ):
            raise Invalid("WAL directories must be distinct")
        if (
            str(uuid.UUID(epoch)) != epoch
            or len(cipher_key) != 32
            or len(witness_key) < 32
        ):
            raise Invalid("invalid configuration")
        self.epoch, self.cipher_key, self.witness_key = epoch, cipher_key, witness_key
        self.manifest = self.archive / "manifest.jsonl"
        self.checkpoint = self.anchor / "checkpoint.json"
        self.lockfile = open(self.anchor / "writer.lock", "a+b")  # noqa: SIM115
        try:
            fcntl.flock(self.lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.records = []
            self.recover()
        except BaseException:
            self.lockfile.close()
            raise

    def checkpoint_for(self, sequence, chain_mac):
        data = {
            "version": 1,
            "epoch": self.epoch,
            "sequence": sequence,
            "chain_mac": chain_mac,
        }
        data["mac"] = sign(self.witness_key, "varal-wal-checkpoint-v1", data)
        return data

    def write_checkpoint(self, sequence, chain_mac):
        atomic(
            self.checkpoint, canonical(self.checkpoint_for(sequence, chain_mac)) + b"\n"
        )

    def verify_receipt(self, receipt):
        fields = {
            "version",
            "epoch",
            "segment",
            "timeline",
            "plaintext_sha256",
            "ciphertext_sha256",
            "nonce",
            "key_id",
            "mac",
        }
        if (
            set(receipt) != fields
            or receipt["version"] != 1
            or receipt["epoch"] != self.epoch
            or not NAME.fullmatch(receipt["segment"])
            or receipt["timeline"] != receipt["segment"][:8]
            or receipt["key_id"] != "wal-v1"
        ):
            raise Invalid("invalid receipt")
        unsigned = {k: v for k, v in receipt.items() if k != "mac"}
        if not hmac.compare_digest(
            receipt["mac"], sign(self.witness_key, "varal-wal-witness-v1", unsigned)
        ):
            raise Invalid("invalid receipt MAC")
        if (
            not re.fullmatch(r"[0-9a-f]{64}", receipt["plaintext_sha256"])
            or not re.fullmatch(r"[0-9a-f]{64}", receipt["ciphertext_sha256"])
            or not re.fullmatch(r"[0-9a-f]{24}", receipt["nonce"])
        ):
            raise Invalid("invalid receipt digest")
        ciphertext = (self.archive / (receipt["segment"] + ".gcm")).read_bytes()
        if hashlib.sha256(ciphertext).hexdigest() != receipt["ciphertext_sha256"]:
            raise Invalid("archive missing or altered")
        associated = (self.epoch + "\n" + receipt["segment"]).encode()
        plain = AESGCM(self.cipher_key).decrypt(
            bytes.fromhex(receipt["nonce"]), ciphertext, associated
        )
        if hashlib.sha256(plain).hexdigest() != receipt["plaintext_sha256"]:
            raise Invalid("archive plaintext mismatch")

    def validate_identity(self, required):
        source = self.spool / "cluster.id"
        identity = self.anchor / "identity.json"
        if not source.exists():
            if required or identity.exists():
                raise Invalid("cluster identity unavailable")
            return False
        cluster_id = source.read_text().strip()
        if not re.fullmatch(r"[0-9]{1,20}", cluster_id):
            raise Invalid("invalid cluster identity")
        expected = {"version": 1, "epoch": self.epoch, "system_identifier": cluster_id}
        expected["mac"] = sign(self.witness_key, "varal-wal-identity-v1", expected)
        if identity.exists():
            if json.loads(identity.read_bytes()) != expected:
                raise Invalid("cluster identity mismatch")
        elif required:
            raise Invalid("cluster identity anchor missing")
        else:
            atomic(identity, canonical(expected) + b"\n")
        return True

    def write_ack(self, receipt):
        path = self.acks / (receipt["segment"] + ".ack")
        data = canonical(receipt) + b"\n"
        if path.exists():
            if path.read_bytes() != data:
                raise Invalid("witness conflict")
            return
        atomic(path, data, 0o644)

    def recover(self):
        if not self.manifest.is_file() or not self.checkpoint.is_file():
            raise Invalid("archive anchor missing")
        checkpoint = json.loads(self.checkpoint.read_bytes())
        if (
            type(checkpoint.get("sequence")) is not int
            or checkpoint["sequence"] < 0
            or checkpoint
            != self.checkpoint_for(checkpoint["sequence"], checkpoint.get("chain_mac"))
        ):
            raise Invalid("invalid archive checkpoint")
        content = self.manifest.read_bytes()
        previous, offset = ZERO, 0
        seen = set()
        for line in content.splitlines(keepends=True):
            if not line.endswith(b"\n"):
                if len(self.records) < checkpoint["sequence"]:
                    raise Invalid("acknowledged manifest truncated")
                break
            record = json.loads(line)
            expected = sign(
                self.witness_key,
                "varal-wal-manifest-v1",
                {k: v for k, v in record.items() if k != "chain_mac"},
            )
            if (
                set(record) != {"sequence", "previous", "receipt", "chain_mac"}
                or record["sequence"] != len(self.records) + 1
                or record["previous"] != previous
                or not hmac.compare_digest(record["chain_mac"], expected)
                or canonical(record) + b"\n" != line
            ):
                raise Invalid("invalid archive manifest")
            self.verify_receipt(record["receipt"])
            if record["receipt"]["segment"] in seen:
                raise Invalid("duplicate archive segment")
            seen.add(record["receipt"]["segment"])
            self.records.append(record)
            previous = record["chain_mac"]
            offset += len(line)
        seq = checkpoint["sequence"]
        self.validate_identity(required=bool(self.records))
        if (
            seq > len(self.records)
            or (seq == 0 and checkpoint["chain_mac"] != ZERO)
            or (seq and self.records[seq - 1]["chain_mac"] != checkpoint["chain_mac"])
        ):
            raise Invalid("archive checkpoint mismatch")
        with open(self.manifest, "r+b") as stream:
            if offset != len(content):
                stream.truncate(offset)
            stream.flush()
            os.fsync(stream.fileno())
        for record in self.records[seq:]:
            self.write_checkpoint(record["sequence"], record["chain_mac"])
        for record in self.records:
            self.write_ack(record["receipt"])

    def archive_one(self, path):
        if not self.validate_identity(required=bool(self.records)):
            return False
        segment = path.name.removesuffix(".ready")
        if not NAME.fullmatch(segment):
            raise Invalid("invalid WAL name")
        plaintext = path.read_bytes()
        digest = hashlib.sha256(plaintext).hexdigest()
        prior = next(
            (r["receipt"] for r in self.records if r["receipt"]["segment"] == segment),
            None,
        )
        if prior:
            if prior["plaintext_sha256"] != digest:
                raise Invalid("conflicting WAL segment")
            self.write_ack(prior)
        else:
            nonce = os.urandom(12)
            associated = (self.epoch + "\n" + segment).encode()
            ciphertext = AESGCM(self.cipher_key).encrypt(nonce, plaintext, associated)
            atomic(self.archive / (segment + ".gcm"), ciphertext)
            receipt = {
                "version": 1,
                "epoch": self.epoch,
                "segment": segment,
                "timeline": segment[:8],
                "plaintext_sha256": digest,
                "ciphertext_sha256": hashlib.sha256(ciphertext).hexdigest(),
                "nonce": nonce.hex(),
                "key_id": "wal-v1",
            }
            receipt["mac"] = sign(self.witness_key, "varal-wal-witness-v1", receipt)
            record = {
                "sequence": len(self.records) + 1,
                "previous": self.records[-1]["chain_mac"] if self.records else ZERO,
                "receipt": receipt,
            }
            record["chain_mac"] = sign(
                self.witness_key, "varal-wal-manifest-v1", record
            )
            with open(self.manifest, "ab") as stream:
                stream.write(canonical(record) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
            self.write_checkpoint(record["sequence"], record["chain_mac"])
            self.records.append(record)
            self.write_ack(receipt)
        path.unlink()
        sync_dir(self.spool)
        return True


def main():
    parser = argparse.ArgumentParser()
    for option in (
        "spool",
        "archive",
        "acks",
        "anchor",
        "epoch",
        "cipher-key",
        "witness-key",
    ):
        parser.add_argument("--" + option, required=True)
    parser.add_argument("--init", action="store_true")
    args = parser.parse_args()
    cipher_key = bytes.fromhex(Path(args.cipher_key).read_text().strip())
    witness_key = Path(args.witness_key).read_bytes().rstrip()
    archive, anchor = Path(args.archive), Path(args.anchor)
    if args.init:
        if (archive / "manifest.jsonl").exists() or (
            anchor / "checkpoint.json"
        ).exists():
            raise Invalid("already initialized")
        atomic(archive / "manifest.jsonl", b"")
        checkpoint = {
            "version": 1,
            "epoch": args.epoch,
            "sequence": 0,
            "chain_mac": ZERO,
        }
        checkpoint["mac"] = sign(witness_key, "varal-wal-checkpoint-v1", checkpoint)
        atomic(anchor / "checkpoint.json", canonical(checkpoint) + b"\n")
        return
    worker = Archive(
        args.spool,
        args.archive,
        args.acks,
        args.anchor,
        args.epoch,
        cipher_key,
        witness_key,
    )
    while True:
        pending = sorted(worker.spool.glob("*.ready"))
        for path in pending:
            worker.archive_one(path)
        (worker.anchor / "heartbeat").touch()
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001 -- Fail closed without printing untrusted paths.
        print("WAL archive unavailable", file=sys.stderr)
        sys.exit(1)
