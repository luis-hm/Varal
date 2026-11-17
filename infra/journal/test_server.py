import hashlib
import hmac
import http.client
import io
import json
import tempfile
import threading
import unittest
import uuid
from http.server import ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from server import Closed, Conflict, Handler, Invalid, Journal, canonical, initialize


class JournalTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data = Path(self.tmp.name) / "data"
        self.anchor = Path(self.tmp.name) / "anchor"
        self.epoch = str(uuid.uuid4())
        self.keys = (b"c" * 32, b"r" * 32, b"p" * 32)
        initialize(self.data, self.anchor, self.epoch, self.keys[2], self.keys[1])
        self.journal = self.open()
        self.addCleanup(lambda: self.journal.lockfile.close())
        self.req = {
            "version": 1,
            "epoch": self.epoch,
            "operation_id": str(uuid.uuid4()),
            "owner_id": str(uuid.uuid4()),
            "kind": "PREPARE",
            "fence": 1,
            "prepare_seq": None,
        }

    def open(self):
        return Journal(self.data, self.anchor, self.epoch, *self.keys)

    def restart(self):
        self.journal.lockfile.close()
        self.journal = self.open()

    def test_http_authentication_replay_and_permissions(self):
        server = SimpleNamespace(
            journal=self.journal,
            auth_keys={
                "writer-v1": b"w" * 32,
                "restore-v1": b"s" * 32,
                "fence-v1": b"f" * 32,
            },
            failed=False,
        )

        def call(method, path, key_id, key, body=b""):
            digest = hashlib.sha256(body).hexdigest()
            message = f"varal-journal-request-v1\n{method}\n{path}\n{digest}\n{key_id}".encode()
            signature = hmac.new(key, message, hashlib.sha256).hexdigest()
            handler = Handler.__new__(Handler)
            handler.server, handler.command, handler.path = server, method, path
            handler.headers = {
                "Content-Type": "application/json",
                "Content-Length": str(len(body)),
                "X-Varal-Key-Id": key_id,
                "X-Varal-Body-SHA256": digest,
                "X-Varal-Signature": signature,
            }
            handler.rfile = io.BytesIO(body)
            result = []
            handler.reply = lambda status, value: result.append((status, value))
            getattr(handler, "do_" + method)()
            return result[0]

        body = canonical(self.req)
        status, first = call("POST", "/v1/records", "writer-v1", b"w" * 32, body)
        self.assertEqual(status, 201)
        self.assertEqual(
            call("POST", "/v1/records", "writer-v1", b"w" * 32, body), (200, first)
        )
        self.assertEqual(
            call("POST", "/v1/records", "writer-v1", b"x" * 32, body)[0], 401
        )
        self.assertEqual(
            call("GET", "/v1/records?after=0&limit=5", "writer-v1", b"w" * 32)[0], 403
        )
        status, page = call(
            "GET", "/v1/records?after=0&limit=5", "restore-v1", b"s" * 32
        )
        self.assertEqual(status, 200)
        self.assertEqual(page["records"][0]["operation_id"], self.req["operation_id"])
        status, found = call(
            "GET", "/v1/operations/" + self.req["operation_id"], "writer-v1", b"w" * 32
        )
        self.assertEqual((status, found["receipts"][0]), (200, first["receipt"]))
        fence_request = canonical(
            {
                "version": 1,
                "epoch": self.epoch,
                "fence_id": str(uuid.uuid4()),
                "action": "DRAIN",
            }
        )
        self.assertEqual(
            call("POST", "/v1/fence", "restore-v1", b"s" * 32, fence_request)[0], 403
        )
        self.assertEqual(
            call("POST", "/v1/fence", "fence-v1", b"f" * 32, fence_request)[0], 200
        )
        nonce = "a" * 64
        status, response = call(
            "GET", "/v1/fence?nonce=" + nonce, "restore-v1", b"s" * 32
        )
        self.assertEqual(status, 200)
        self.assertEqual(response["freshness"]["nonce"], nonce)
        freshness = response["freshness"]
        signature = freshness.pop("mac")
        expected = hmac.new(
            self.keys[1],
            b"varal-journal-fence-read-v1\n" + canonical(freshness),
            hashlib.sha256,
        ).hexdigest()
        self.assertEqual(signature, expected)
        self.assertEqual(
            call("GET", "/v1/fence?nonce=bad", "restore-v1", b"s" * 32)[0], 400
        )

    def test_http_wire(self):
        try:
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        except PermissionError:
            self.skipTest("sandbox does not permit loopback sockets")
        httpd.journal = self.journal
        httpd.auth_keys = {"writer-v1": b"w" * 32, "restore-v1": b"s" * 32}
        httpd.failed = False
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            body = canonical(self.req)
            path = "/v1/records"
            digest = hashlib.sha256(body).hexdigest()
            payload = (
                f"varal-journal-request-v1\nPOST\n{path}\n{digest}\nwriter-v1".encode()
            )
            signature = hmac.new(b"w" * 32, payload, hashlib.sha256).hexdigest()
            headers = {
                "Content-Type": "application/json",
                "X-Varal-Key-Id": "writer-v1",
                "X-Varal-Body-SHA256": digest,
                "X-Varal-Signature": signature,
            }
            conn = http.client.HTTPConnection(*httpd.server_address, timeout=2)
            conn.request("POST", path, body, headers)
            response = conn.getresponse()
            self.assertEqual(response.status, 201)
            self.assertEqual(json.loads(response.read())["receipt"]["seq"], 1)
            conn.close()
        finally:
            httpd.shutdown()
            thread.join()
            httpd.server_close()

    def test_fence_drains_and_seals_durably_without_discarding_pending(self):
        _, prepared = self.journal.append(self.req)
        fence_id = str(uuid.uuid4())
        req = {
            "version": 1,
            "epoch": self.epoch,
            "fence_id": fence_id,
            "action": "DRAIN",
        }
        receipt = self.journal.transition_fence(req)
        self.assertEqual(receipt["state"], "drain")
        self.assertEqual(self.journal.transition_fence(req), receipt)
        self.assertEqual(self.journal.append(self.req), (False, prepared))
        with self.assertRaises(Closed):
            self.journal.append(dict(self.req, operation_id=str(uuid.uuid4())))
        with self.assertRaises(Conflict):
            self.journal.transition_fence(dict(req, action="SEAL"))
        self.journal.append(dict(self.req, kind="ABORT", prepare_seq=prepared["seq"]))
        sealed = self.journal.transition_fence(dict(req, action="SEAL"))
        self.assertEqual(sealed["state"], "sealed")
        self.restart()
        self.assertEqual(self.journal.fence, sealed)
        with self.assertRaises(Closed):
            self.journal.append(dict(self.req, operation_id=str(uuid.uuid4())))
        self.journal.transition_fence(dict(req, action="RELEASE"))
        self.assertTrue(
            self.journal.append(dict(self.req, operation_id=str(uuid.uuid4())))[0]
        )

    def test_missing_fence_anchor_fails_closed(self):
        self.journal.lockfile.close()
        (self.anchor / "fence.json").unlink()
        with self.assertRaises(Invalid):
            self.open()

    def test_idempotence_and_terminal_collision(self):
        created, receipt = self.journal.append(self.req)
        self.assertTrue(created)
        self.assertEqual((False, receipt), self.journal.append(self.req))
        terminal = dict(self.req, kind="COMMIT", prepare_seq=receipt["seq"])
        self.journal.append(terminal)
        with self.assertRaises(Conflict):
            self.journal.append(dict(terminal, kind="ABORT"))
        with self.assertRaises(Conflict):
            self.journal.append(dict(self.req, owner_id=str(uuid.uuid4())))
        self.restart()
        self.assertEqual((False, receipt), self.journal.append(self.req))

    def test_concurrent_terminal_has_one_winner(self):
        _, receipt = self.journal.append(self.req)
        outcomes = []

        def run(kind):
            try:
                self.journal.append(
                    dict(self.req, kind=kind, prepare_seq=receipt["seq"])
                )
                outcomes.append("ok")
            except Conflict:
                outcomes.append("conflict")

        threads = [
            threading.Thread(target=run, args=(kind,)) for kind in ("COMMIT", "ABORT")
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertCountEqual(outcomes, ["ok", "conflict"])

    def test_crash_before_checkpoint_promotes_fsynced_tail(self):
        with (
            patch.object(
                self.journal, "save_checkpoint", side_effect=OSError("failure")
            ),
            self.assertRaises(OSError),
        ):
            self.journal.append(self.req)
        with self.assertRaises(OSError):
            self.journal.append(self.req)
        self.restart()
        created, receipt = self.journal.append(self.req)
        self.assertFalse(created)
        self.assertEqual(receipt["seq"], 1)

    def test_truncated_acknowledged_suffix_and_missing_checkpoint_fail_closed(self):
        self.journal.append(self.req)
        self.journal.lockfile.close()
        (self.data / "journal.jsonl").write_bytes(b"")
        with self.assertRaises(Invalid):
            self.open()
        (self.anchor / "checkpoint.json").unlink()
        with self.assertRaises(Invalid):
            self.open()

    def test_partial_unacknowledged_tail_is_discarded(self):
        _, receipt = self.journal.append(self.req)
        self.journal.lockfile.close()
        with (self.data / "journal.jsonl").open("ab") as stream:
            stream.write(b'{"incomplete":')
        self.journal = self.open()
        self.assertEqual((False, receipt), self.journal.append(self.req))


if __name__ == "__main__":
    unittest.main()
