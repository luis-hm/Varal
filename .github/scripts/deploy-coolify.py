"""Queue a checked commit through Coolify's application-scoped signed Git hook.

No Coolify API token is used. The receiver matches repository/branch/secret and
queues payload.after as commit. Success proves queuing, not a healthy deployment.
Official implementation:
https://github.com/coollabsio/coolify/blob/v4.x/app/Http/Controllers/Webhook/Github.php
Setup: deploy-key/public source without GitHub App or a direct GitHub push hook;
unique manual_webhook_secret_github; auto-deploy enabled only for HMG initially.
Future production activation requires BOTH its workflow gate and auto-deploy.
"""

import hashlib
import hmac
import json
import os
import re
import ssl
import sys
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener


class DeployError(Exception):
    """Controlled error containing no remote response or secret."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise DeployError("Redirect refused; verify the configured HTTPS endpoint")


def required(env, name):
    value = env.get(name, "")
    if not value or "\r" in value or "\n" in value:
        raise DeployError(f"Missing or invalid configuration: {name}")
    return value


def base_url(value):
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        raise DeployError("Invalid HTTPS base URL") from None
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in ("", "/")
        or port not in (None, 443)
    ):
        raise DeployError("Expected an HTTPS origin without credentials or path")
    return value.rstrip("/")


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{12,64}", value):
        raise DeployError("Invalid Coolify resource or deployment UUID")
    return value


def request_json(url, headers, data=None):
    opener = build_opener(HTTPSHandler(context=ssl.create_default_context()), NoRedirect())
    request = Request(
        url,
        data=data,
        headers={"Accept": "application/json", "User-Agent": "varal-deploy-workflow"} | headers,
        method="POST" if data is not None else "GET",
    )
    try:
        with opener.open(request, timeout=30) as response:
            if response.status not in (200, 201, 202):
                raise DeployError("Endpoint returned an unexpected HTTP status")
            raw = response.read(1024 * 1024 + 1)
    except HTTPError as exc:
        raise DeployError(f"Request refused with HTTP {exc.code}") from None
    except (URLError, TimeoutError, OSError):
        # An ambiguous POST may already have queued a deployment. Never retry it.
        raise DeployError("Request failed; inspect Coolify before retrying") from None
    if len(raw) > 1024 * 1024:
        raise DeployError("Response exceeded the allowed size")
    try:
        return json.loads(raw)
    except (ValueError, UnicodeError):
        raise DeployError("Endpoint returned invalid JSON") from None


def signed_payload(repo, branch, sha, secret):
    # Do not forward full push events: authors/messages may contain private data.
    payload = {"ref": "refs/heads/" + branch, "repository": {"full_name": repo}, "after": sha}
    raw = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    signature = "sha256=" + hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    return raw, signature


def queued_deployment(response, resource):
    if not isinstance(response, list):
        raise DeployError("Coolify did not acknowledge a queued deployment")
    accepted = [
        item for item in response
        if isinstance(item, dict) and item.get("status") == "success"
    ]
    # Other apps with the same repo/branch may return invalid-signature failures.
    if len(accepted) != 1:
        raise DeployError("Coolify did not acknowledge exactly one successful queue entry")
    entry = accepted[0]
    acknowledged_resource = entry.get("application_uuid")
    if acknowledged_resource is not None and acknowledged_resource != resource:
        raise DeployError("Coolify acknowledged a different application")
    return identifier(entry.get("deployment_uuid"))


def deploy(env):
    branch = required(env, "DEPLOY_EXPECTED_BRANCH")
    if branch not in ("develop", "main") or env.get("GITHUB_REF") != "refs/heads/" + branch:
        raise DeployError("This workflow cannot deploy the current Git ref")
    sha = required(env, "GITHUB_SHA")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise DeployError("Invalid expected Git commit")
    repo = required(env, "GITHUB_REPOSITORY")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise DeployError("Invalid GitHub repository")
    resource = identifier(required(env, "COOLIFY_RESOURCE_UUID"))
    origin = base_url(required(env, "COOLIFY_URL"))
    secret = required(env, "COOLIFY_WEBHOOK_SECRET")
    if len(secret) < 32:
        raise DeployError("Webhook secret must contain at least 32 characters")
    head = request_json(
        f"https://api.github.com/repos/{repo}/git/ref/heads/{quote(branch, safe='')}",
        {"Authorization": "Bearer " + required(env, "GITHUB_TOKEN")},
    )
    obj = head.get("object") if isinstance(head, dict) else None
    if not isinstance(obj, dict) or obj.get("sha") != sha:
        raise DeployError("A newer push exists; refusing to queue this obsolete workflow")
    raw, signature = signed_payload(repo, branch, sha, secret)
    response = request_json(
        origin + "/webhooks/source/github/events/manual",
        {
            "Content-Type": "application/json",
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": str(uuid.uuid4()),
            "X-Hub-Signature-256": signature,
        },
        raw,
    )
    deployment = queued_deployment(response, resource)
    print(f"Coolify acknowledged queued deployment {deployment} for commit {sha}", flush=True)
    print("Queuing acknowledged only; completion and application health are not verified here")


if __name__ == "__main__":
    try:
        deploy(os.environ)
    except DeployError as error:
        print(f"Deployment stopped: {error}", file=sys.stderr)
        sys.exit(1)
