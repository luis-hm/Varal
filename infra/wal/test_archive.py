import hashlib
import json
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from archive import ZERO, Archive, Invalid, atomic, canonical, sign
from verify import verify


class ArchiveTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.spool, self.archive, self.acks, self.anchor = [
            root / part for part in ("spool", "archive", "acks", "anchor")
        ]
        for folder in (self.spool, self.archive, self.acks, self.anchor):
            folder.mkdir()
        (self.spool / "cluster.id").write_text("7391024312345678901\n")
        self.epoch = str(uuid.uuid4())
        self.cipher, self.key = b"c" * 32, b"w" * 32
        atomic(self.archive / "manifest.jsonl", b"")
        checkpoint = {
            "version": 1,
            "epoch": self.epoch,
            "sequence": 0,
            "chain_mac": ZERO,
        }
        checkpoint["mac"] = sign(self.key, "varal-wal-checkpoint-v1", checkpoint)
        atomic(self.anchor / "checkpoint.json", canonical(checkpoint) + b"\n")
        self.worker = self.open()
        self.addCleanup(lambda: self.worker.lockfile.close())
        self.segment = "000000010000000000000001"

    def open(self):
        return Archive(
            self.spool,
            self.archive,
            self.acks,
            self.anchor,
            self.epoch,
            self.cipher,
            self.key,
        )

    def restart(self):
        self.worker.lockfile.close()
        self.worker = self.open()

    def test_receipt_only_after_encrypted_archive_and_checkpoint(self):
        raw = b"synthetic wal bytes" * 100
        path = self.spool / (self.segment + ".ready")
        path.write_bytes(raw)
        self.worker.archive_one(path)
        receipt = json.loads((self.acks / (self.segment + ".ack")).read_bytes())
        self.assertEqual(receipt["plaintext_sha256"], hashlib.sha256(raw).hexdigest())
        ciphertext = (self.archive / (self.segment + ".gcm")).read_bytes()
        self.assertNotIn(raw, ciphertext)
        self.assertEqual(
            json.loads((self.anchor / "checkpoint.json").read_bytes())["sequence"], 1
        )
        self.assertFalse(path.exists())
        self.restart()
        self.assertEqual(
            json.loads((self.acks / (self.segment + ".ack")).read_bytes()), receipt
        )

    def test_crash_before_checkpoint_does_not_publish_ack(self):
        path = self.spool / (self.segment + ".ready")
        path.write_bytes(b"synthetic")
        with (
            patch.object(
                self.worker, "write_checkpoint", side_effect=OSError("failure")
            ),
            self.assertRaises(OSError),
        ):
            self.worker.archive_one(path)
        self.assertFalse((self.acks / (self.segment + ".ack")).exists())
        self.restart()
        self.assertTrue((self.acks / (self.segment + ".ack")).exists())
        self.worker.archive_one(path)
        self.assertFalse(path.exists())

    def test_missing_acknowledged_segment_or_anchor_fails_closed(self):
        path = self.spool / (self.segment + ".ready")
        path.write_bytes(b"synthetic")
        self.worker.archive_one(path)
        self.worker.lockfile.close()
        (self.archive / (self.segment + ".gcm")).unlink()
        with self.assertRaises((Invalid, OSError)):
            self.open()
        (self.anchor / "checkpoint.json").unlink()
        with self.assertRaises(Invalid):
            self.open()

    def test_range_verifier_detects_gap_and_cluster_mismatch(self):
        for suffix in (1, 3):
            path = self.spool / (f"0000000100000000000000{suffix:02X}.ready")
            path.write_bytes(b"synthetic" + bytes([suffix]))
            self.worker.archive_one(path)
        first = "000000010000000000000001"
        last = "000000010000000000000003"
        args = (
            self.archive,
            self.anchor,
            self.epoch,
            "7391024312345678901",
            self.cipher,
            self.key,
        )
        self.assertEqual(verify(*args, first, first), 2)
        with self.assertRaises(Invalid):
            verify(*args, first, last)
        wrong = (self.archive, self.anchor, self.epoch, "123", self.cipher, self.key)
        with self.assertRaises(Invalid):
            verify(*wrong, first, first)

    def test_same_segment_with_other_bytes_cannot_replace_receipt(self):
        path = self.spool / (self.segment + ".ready")
        path.write_bytes(b"first")
        self.worker.archive_one(path)
        path.write_bytes(b"second")
        with self.assertRaises(Invalid):
            self.worker.archive_one(path)


if __name__ == "__main__":
    unittest.main()
