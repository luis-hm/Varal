"""Decrypt a verified WAL range into an empty isolated restore volume, never open traffic."""
import argparse
import json
import os
import sys
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from archive import Invalid, atomic
from verify import ordinal, verify


def main():
    parser = argparse.ArgumentParser()
    for option in ("archive", "anchor", "output", "epoch", "system-identifier", "cipher-key", "witness-key", "first", "last"):
        parser.add_argument("--" + option, required=True)
    args = parser.parse_args()
    archive, output = Path(args.archive), Path(args.output)
    if any(output.iterdir()):
        raise Invalid("restore WAL output must be empty")
    cipher = bytes.fromhex(Path(args.cipher_key).read_text().strip())
    witness = Path(args.witness_key).read_bytes().rstrip()
    count = verify(archive, args.anchor, args.epoch, args.system_identifier, cipher, witness, args.first, args.last)
    records = [json.loads(line) for line in (archive / "manifest.jsonl").read_bytes().splitlines()][:count]
    start, end = ordinal(args.first), ordinal(args.last)
    selected = []
    for record in records:
        receipt = record["receipt"]
        segment = receipt["segment"]
        if len(segment) == 24 and segment[:8] == args.first[:8] and start <= ordinal(segment) <= end:
            ciphertext = (archive / (segment + ".gcm")).read_bytes()
            associated = (args.epoch + "\n" + segment).encode()
            plaintext = AESGCM(cipher).decrypt(bytes.fromhex(receipt["nonce"]), ciphertext, associated)
            atomic(output / segment, plaintext)
            selected.append(segment)
    if len(selected) != end - start + 1:
        raise Invalid("WAL export incomplete")
    print("verified WAL range staged in isolated volume; recovery remains closed")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001 -- Avoid disclosing paths or contents on failure.
        print("WAL export failed; recovery remains closed", file=sys.stderr)
        sys.exit(1)
