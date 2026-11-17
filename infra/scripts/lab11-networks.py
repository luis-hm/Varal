"""Choose two private /24 networks that do not overlap Docker networks or host routes."""

import ipaddress
import json
import secrets
import subprocess

ids = subprocess.check_output(["docker", "network", "ls", "-q"], text=True).split()
networks = (
    json.loads(
        subprocess.check_output(["docker", "network", "inspect", *ids], text=True)
    )
    if ids
    else []
)
occupied = []
for network in networks:
    for entry in (network.get("IPAM") or {}).get("Config") or []:
        if entry.get("Subnet"):
            occupied.append(ipaddress.ip_network(entry["Subnet"], strict=False))
try:
    routes = json.loads(
        subprocess.check_output(
            ["ip", "-j", "-4", "route", "show", "table", "all"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    )
    for route in routes:
        dst = route.get("dst", "default")
        if dst != "default":
            occupied.append(ipaddress.ip_network(dst, strict=False))
except (OSError, subprocess.CalledProcessError, ValueError):
    pass
candidates = [
    ipaddress.ip_network(f"10.{second}.{third}.0/24")
    for second in range(192, 224)
    for third in range(256)
]
secrets.SystemRandom().shuffle(candidates)
chosen = []
for candidate in candidates:
    if not any(
        net.version == 4 and candidate.overlaps(net) for net in occupied + chosen
    ):
        chosen.append(candidate)
        if len(chosen) == 2:
            break
if len(chosen) != 2:
    raise SystemExit("no isolated laboratory networks available")
print(json.dumps({"application": str(chosen[0]), "frontend": str(chosen[1])}))
