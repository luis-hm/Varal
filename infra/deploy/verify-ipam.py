"""Exercise low dynamic allocation followed by high fixed peers in a new private network."""

import ipaddress
import json
import secrets
import subprocess

prefix = "varal-hmg-ipam-qa-" + secrets.token_hex(6)
image = "varal-hmg-validation-bootstrap:20261117"
containers = []
created = False


def docker(arguments):
    result = subprocess.run(["docker", *arguments], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-1500:])
    return result.stdout.strip()


try:
    identifiers = docker(["network", "ls", "-q"]).splitlines()
    existing = json.loads(docker(["network", "inspect", *identifiers]))
    used = [
        ipaddress.ip_network(config["Subnet"])
        for network in existing
        for config in (network.get("IPAM", {}).get("Config") or [])
        if config.get("Subnet") and ":" not in config["Subnet"]
    ]
    subnet = next(
        candidate
        for candidate in (
            ipaddress.ip_network(f"{base}.{octet}.0/24")
            for base in ("172.30", "172.29", "172.28", "10.254", "10.253")
            for octet in range(250, 220, -1)
        )
        if not any(candidate.overlaps(value) for value in used)
    )
    docker(["network", "create", "--internal", "--subnet", str(subnet), prefix])
    created = True
    expected = {}
    for role, offset in (("dynamic", None), ("edge", 240), ("ssr", 241)):
        name = prefix + "-" + role
        containers.append(name)
        arguments = ["run", "-d", "--name", name, "--network", prefix]
        if offset is not None:
            expected[role] = str(subnet.network_address + offset)
            arguments += ["--ip", expected[role]]
        arguments += ["--entrypoint", "python", image, "-c", "import time; time.sleep(180)"]
        docker(arguments)
    details = json.loads(docker(["inspect", *containers]))
    addresses = {
        item["Name"].rsplit("-", 1)[-1]: item["NetworkSettings"]["Networks"][prefix]["IPAddress"]
        for item in details
    }
    assert all(item["State"]["Running"] for item in details)
    assert addresses["edge"] == expected["edge"]
    assert addresses["ssr"] == expected["ssr"]
    assert addresses["dynamic"] not in expected.values()
    assert len(set(addresses.values())) == 3
    assert int(ipaddress.ip_address(addresses["dynamic"])) < int(subnet.network_address + 240)
    print(json.dumps({"check": "dynamic-first with high fixed peers", "subnet": str(subnet), "addresses": addresses, "passed": True}))
finally:
    for name in containers:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
    if created:
        subprocess.run(["docker", "network", "rm", prefix], capture_output=True)
