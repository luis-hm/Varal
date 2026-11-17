"""Compare restored object bytes with the encrypted backup and restored DB inventory.

Inputs are private files prepared by the restore operator; no network or signing occurs here.
The S3 inventory must be freshly emitted by s3-manifest.py against the restored bucket.
"""

import hashlib
import json
import sys
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def objects(manifest):
    if manifest.get("version") != 1 or not isinstance(manifest.get("bucket"), str):
        raise ValueError("invalid manifest")
    result = {}
    for item in manifest["objects"]:
        key, size, digest = item["key"], item["size"], item["sha256"]
        if not isinstance(key, str) or not key or key in result:
            raise ValueError("invalid object key")
        if type(size) is not int or size < 0 or not isinstance(digest, str) or len(digest) != 64:
            raise ValueError("invalid object metadata")
        if any(char not in "0123456789abcdef" for char in digest):
            raise ValueError("invalid digest")
        result[key] = (size, digest)
    return result


def main():
    if len(sys.argv) != 4:
        raise ValueError("expected backup inventory, restored inventory and DB inventory")
    backup, actual, db = (json.loads(Path(path).read_bytes()) for path in sys.argv[1:])
    baseline, restored = objects(backup), objects(actual)
    if backup["bucket"] != actual["bucket"] or db.get("bucket") != backup["bucket"] or baseline != restored:
        raise ValueError("restored objects differ from backup")
    if db.get("version") != 1 or not isinstance(db.get("objects"), list) or not isinstance(db.get("pins"), list):
        raise ValueError("invalid DB inventory")
    for item in db["objects"]:
        metadata = restored.get(item["key"])
        if metadata is None or (item["size"] is not None and item["size"] != metadata[0]):
            raise ValueError("referenced object missing or wrong size")
        if item["sha256"] is not None and item["sha256"] != metadata[1]:
            raise ValueError("referenced object hash mismatch")
    for pin in db["pins"]:
        metadata = restored.get(pin["key"])
        if metadata is None or (pin["size"] is not None and pin["size"] != metadata[0]):
            raise ValueError("pinned object missing or wrong size")
    result = {
        "objects_manifest_sha256": hashlib.sha256(canonical(actual)).hexdigest(),
        "pins_manifest_sha256": hashlib.sha256(canonical(db["pins"])).hexdigest(),
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        print("Object verification failed; restore remains closed", file=sys.stderr)
        sys.exit(1)
