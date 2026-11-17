"""Verify an anchored encrypted WAL range; does not authorize restore or dispatch."""

import argparse
import hmac
import json
import re
import sys
from pathlib import Path

from archive import ZERO, Archive, Invalid, canonical, sign


def ordinal(segment):
    if not re.fullmatch(r"[0-9A-F]{24}", segment):
        raise Invalid("invalid segment")
    log_id = int(segment[8:16], 16)
    number = int(segment[16:24], 16)
    if number >= 256:  # Laboratory initdb uses 16 MiB WAL segments.
        raise Invalid("unsupported segment size")
    return (log_id << 8) | number


def verify(
    archive_dir,
    anchor_dir,
    epoch,
    system_identifier,
    cipher_key,
    witness_key,
    first,
    last,
):
    archive, anchor = Path(archive_dir), Path(anchor_dir)
    if first[:8] != last[:8]:
        raise Invalid("timeline transition requires independent proof")
    begin, end = ordinal(first), ordinal(last)
    if end < begin or end - begin > 1_000_000:
        raise Invalid("invalid WAL range")
    expected_identity = {
        "version": 1,
        "epoch": epoch,
        "system_identifier": system_identifier,
    }
    expected_identity["mac"] = sign(
        witness_key, "varal-wal-identity-v1", expected_identity
    )
    if json.loads((anchor / "identity.json").read_bytes()) != expected_identity:
        raise Invalid("cluster identity mismatch")
    checkpoint_path = anchor / "checkpoint.json"
    checkpoint_bytes = checkpoint_path.read_bytes()
    checkpoint = json.loads(checkpoint_bytes)
    checkpoint_unsigned = {k: v for k, v in checkpoint.items() if k != "mac"}
    if (
        set(checkpoint) != {"version", "epoch", "sequence", "chain_mac", "mac"}
        or checkpoint["version"] != 1
        or checkpoint["epoch"] != epoch
        or type(checkpoint["sequence"]) is not int
        or checkpoint["sequence"] < 1
        or not hmac.compare_digest(
            checkpoint["mac"],
            sign(witness_key, "varal-wal-checkpoint-v1", checkpoint_unsigned),
        )
    ):
        raise Invalid("invalid checkpoint")
    # Reuse authenticated ciphertext and plaintext verification without starting a writer.
    verifier = Archive.__new__(Archive)
    verifier.archive, verifier.epoch = archive, epoch
    verifier.cipher_key, verifier.witness_key = cipher_key, witness_key
    records = (archive / "manifest.jsonl").read_bytes().splitlines(keepends=True)
    previous = ZERO
    segments = set()
    ordered = []
    if len(records) < checkpoint["sequence"]:
        raise Invalid("manifest truncated")
    for index, line in enumerate(records[: checkpoint["sequence"]], start=1):
        record = json.loads(line)
        unsigned = {k: v for k, v in record.items() if k != "chain_mac"}
        if (
            set(record) != {"sequence", "previous", "receipt", "chain_mac"}
            or record["sequence"] != index
            or record["previous"] != previous
            or canonical(record) + b"\n" != line
            or not hmac.compare_digest(
                record["chain_mac"],
                sign(witness_key, "varal-wal-manifest-v1", unsigned),
            )
        ):
            raise Invalid("invalid manifest")
        verifier.verify_receipt(record["receipt"])
        segment = record["receipt"]["segment"]
        if segment in segments:
            raise Invalid("duplicate segment")
        segments.add(segment)
        if re.fullmatch(r"[0-9A-F]{24}", segment) and segment[:8] == first[:8]:
            current = ordinal(segment)
            if ordered and current <= ordered[-1]:
                raise Invalid("WAL segment order invalid")
            ordered.append(current)
        previous = record["chain_mac"]
    if (
        previous != checkpoint["chain_mac"]
        or checkpoint_path.read_bytes() != checkpoint_bytes
    ):
        raise Invalid("checkpoint changed or mismatched")
    actual = {
        ordinal(s)
        for s in segments
        if re.fullmatch(r"[0-9A-F]{24}", s) and s[:8] == first[:8]
    }
    if not all(number in actual for number in range(begin, end + 1)):
        raise Invalid("WAL segment gap")
    return checkpoint["sequence"]


def main():
    parser = argparse.ArgumentParser()
    for option in (
        "archive",
        "anchor",
        "epoch",
        "system-identifier",
        "cipher-key",
        "witness-key",
        "first",
        "last",
    ):
        parser.add_argument("--" + option, required=True)
    args = parser.parse_args()
    try:
        cipher_key = bytes.fromhex(Path(args.cipher_key).read_text().strip())
        witness_key = Path(args.witness_key).read_bytes().rstrip()
        count = verify(
            args.archive,
            args.anchor,
            args.epoch,
            args.system_identifier,
            cipher_key,
            witness_key,
            args.first,
            args.last,
        )
        print(
            f"authenticated WAL range verified; anchored records={count}; PITR not yet authorized"
        )
    except Exception:  # noqa: BLE001 -- Restore must fail closed without printing paths or data.
        print("WAL range cannot be verified", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
