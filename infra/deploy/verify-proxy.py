"""Check exact proxy DNS and input guards in disposable containers without ports."""

import secrets
import subprocess
import time

IMAGE = "varal-hmg-validation-proxy:20261117"
name = "varal-hmg-proxy-qa-" + secrets.token_hex(6)
base = [
    "docker", "run", "--network", "none",
    "--add-host", "api:127.0.0.1", "--add-host", "web:127.0.0.1",
    "-e", "VARAL_DOMAIN=hmgvaral.codehub.systems", "-e", "VARAL_PROXY_ROLE=edge",
]


def run(arguments):
    return subprocess.run(arguments, capture_output=True, text=True)


try:
    result = run([
        *base, "-d", "--name", name,
        "--add-host", "coolify-proxy:172.18.0.2",
        "-e", "COOLIFY_PROXY_TRUST=coolify-proxy", IMAGE,
    ])
    assert result.returncode == 0, result.stderr
    for _ in range(30):
        result = run(["docker", "exec", name, "nginx", "-t", "-c", "/tmp/nginx.conf"])
        if result.returncode == 0:
            break
        time.sleep(0.1)
    assert result.returncode == 0, result.stderr
    print("PASS exact coolify-proxy hostname resolves and actual entrypoint starts nginx")

    result = run([*base, "--rm", "-e", "COOLIFY_PROXY_TRUST=coolify-proxy", IMAGE])
    assert result.returncode != 0
    print("PASS missing trusted hostname refuses startup without fallback")

    for value in (
        "0.0.0.0/0", "10.0.1.0/24", "arbitrary-host", "unix:",
        "172.18.0.2/32;include /tmp/injected", "172.18.0.2/32\ninclude /tmp/injected",
    ):
        result = run([*base, "--rm", "-e", "COOLIFY_PROXY_TRUST=" + value, IMAGE])
        assert result.returncode != 0
        assert "invalid exact trusted proxy" in result.stderr
    print("PASS broad CIDRs, other hosts and configuration injection are refused")
    print("Proxy DNS/input guards: 3/3 groups passed; no HTTP spoof proof inferred.")
finally:
    run(["docker", "rm", "-f", name])
