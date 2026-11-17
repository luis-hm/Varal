"""Check exact proxy DNS and input guards in disposable containers without ports."""

import json
import secrets
import subprocess
import time

IMAGE = "varal-hmg-validation-proxy:20261117"
name = "varal-hmg-proxy-qa-" + secrets.token_hex(6)
names = []
base = [
    "docker", "run", "--network", "none",
    "--read-only", "--tmpfs", "/tmp:mode=1777",
    "--add-host", "hmgvaral-api:127.0.0.1", "--add-host", "hmgvaral-web:127.0.0.1",
    "-e", "VARAL_STACK=hmgvaral",
    "-e", "VARAL_DOMAIN=hmgvaral.codehub.systems", "-e", "VARAL_PROXY_ROLE=edge",
]


def run(arguments):
    return subprocess.run(arguments, capture_output=True, text=True)


try:
    names.append(name)
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
    inspected = run(["docker", "inspect", name])
    config = json.loads(inspected.stdout)[0]
    assert config["State"]["Running"]
    assert config["HostConfig"]["ReadonlyRootfs"]
    assert config["HostConfig"]["Tmpfs"]["/tmp"] == "mode=1777"
    print("PASS exact coolify-proxy hostname resolves and actual entrypoint starts nginx")

    ssr_name = name + "-ssr"
    names.append(ssr_name)
    result = run([
        *base, "-d", "--name", ssr_name,
        "-e", "VARAL_PROXY_ROLE=ssr", "-e", "VARAL_WEB_IP=172.30.212.240", IMAGE,
    ])
    assert result.returncode == 0, result.stderr
    for _ in range(30):
        result = run(["docker", "exec", ssr_name, "nginx", "-t", "-c", "/tmp/nginx.conf"])
        if result.returncode == 0:
            break
        time.sleep(0.1)
    assert result.returncode == 0, result.stderr
    config = json.loads(run(["docker", "inspect", ssr_name]).stdout)[0]
    assert config["State"]["Running"] and config["HostConfig"]["ReadonlyRootfs"]
    assert config["HostConfig"]["Tmpfs"]["/tmp"] == "mode=1777"
    print("PASS SSR entrypoint starts nginx with read-only root and manifest-equivalent tmpfs")

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
    result = run([*base, "--rm", "-e", "VARAL_STACK=other-stack", IMAGE])
    assert result.returncode != 0 and "invalid stack namespace" in result.stderr
    print("PASS only explicitly allowed stack namespaces are accepted")
    print("Proxy startup/DNS/input guards: 5/5 groups passed; no HTTP spoof proof inferred.")
finally:
    for name in names:
        run(["docker", "rm", "-f", name])
