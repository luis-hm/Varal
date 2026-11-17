"""Offline boundaries for the signed queue hook; no API access or credentials."""

import hashlib
import hmac
import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.error import HTTPError

spec = importlib.util.spec_from_file_location(
    "deploy_coolify", Path(__file__).with_name("deploy-coolify.py")
)
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)
UUID = "hmgresourceabcdefghijklmn"
SHA = "a" * 40
SECRET = "synthetic-only-secret-for-offline-tests"


def environment():
    return {
        "DEPLOY_EXPECTED_BRANCH": "develop", "GITHUB_REF": "refs/heads/develop",
        "GITHUB_SHA": SHA, "GITHUB_REPOSITORY": "luis-hm/Varal",
        "COOLIFY_RESOURCE_UUID": UUID, "COOLIFY_URL": "https://coolify.example",
        "COOLIFY_WEBHOOK_SECRET": SECRET, "GITHUB_TOKEN": "synthetic-github-token",
    }


class SignedQueueBoundaries(unittest.TestCase):
    def test_plaintext_credentials_in_url_and_redirects_are_refused(self):
        for url in (
            "http://coolify.example", "https://user:password@coolify.example",
            "https://coolify.example/api/v1", "https://coolify.example?key=secret",
        ):
            with self.subTest(url=url), self.assertRaises(deploy.DeployError):
                deploy.base_url(url)
        with self.assertRaises(deploy.DeployError):
            deploy.NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.example")

    def test_payload_pins_checked_sha_and_signature_covers_exact_bytes(self):
        raw, signature = deploy.signed_payload("luis-hm/Varal", "develop", SHA, SECRET)
        self.assertEqual(json.loads(raw), {
            "ref": "refs/heads/develop", "repository": {"full_name": "luis-hm/Varal"}, "after": SHA,
        })
        expected = "sha256=" + hmac.new(SECRET.encode(), raw, hashlib.sha256).hexdigest()
        self.assertEqual(signature, expected)
        self.assertNotEqual(signature, deploy.signed_payload("luis-hm/Varal", "main", SHA, SECRET)[1])

    def test_wrong_ref_stops_before_network(self):
        with patch.object(deploy, "request_json") as request:
            with self.assertRaises(deploy.DeployError):
                deploy.deploy(environment() | {"GITHUB_REF": "refs/heads/main"})
            request.assert_not_called()

    def test_newer_push_stops_before_webhook(self):
        with patch.object(deploy, "request_json", return_value={"object": {"sha": "b" * 40}}) as request:
            with self.assertRaisesRegex(deploy.DeployError, "newer push"):
                deploy.deploy(environment())
            self.assertEqual(request.call_count, 1)

    def test_failed_or_wrong_resource_is_not_reported_as_queued(self):
        for response in (
            [{"status": "failed", "message": "secret invalid"}],
            [{"status": "success", "application_uuid": "productionabcdefghijklmn", "deployment_uuid": UUID}],
            [{"status": "success", "application_uuid": UUID}],
        ):
            with self.subTest(response=response), self.assertRaises(deploy.DeployError):
                deploy.queued_deployment(response, UUID)
        # Older response shapes may omit application_uuid. The unique secret
        # still scopes the signed hook; never claim UUID correlation in that case.
        self.assertEqual(deploy.queued_deployment([
            {"status": "success", "deployment_uuid": UUID}
        ], UUID), UUID)

    def test_queue_request_has_hmac_without_api_or_github_bearer(self):
        result = [{"status": "success", "application_uuid": UUID, "deployment_uuid": UUID}]
        with patch.object(deploy, "request_json", side_effect=[{"object": {"sha": SHA}}, result]) as request:
            with patch("sys.stdout", new_callable=io.StringIO) as output:
                deploy.deploy(environment())
            url, headers, raw = request.call_args.args
            self.assertEqual(url, "https://coolify.example/webhooks/source/github/events/manual")
            self.assertNotIn("Authorization", headers)
            self.assertEqual(headers["X-GitHub-Event"], "push")
            expected = "sha256=" + hmac.new(SECRET.encode(), raw, hashlib.sha256).hexdigest()
            self.assertEqual(headers["X-Hub-Signature-256"], expected)
            self.assertIn("Queuing acknowledged only", output.getvalue())
            self.assertNotIn(SECRET, output.getvalue())

    def test_http_failure_is_redacted_and_post_not_retried(self):
        opener = Mock()
        opener.open.side_effect = HTTPError(
            "https://coolify.example/?private", 403, SECRET, {}, io.BytesIO(b"secret")
        )
        with patch.object(deploy, "build_opener", return_value=opener):
            with self.assertRaisesRegex(deploy.DeployError, r"^Request refused with HTTP 403$"):
                deploy.request_json("https://coolify.example", {}, b"{}")
        self.assertEqual(opener.open.call_count, 1)


if __name__ == "__main__":
    unittest.main()
