"""Start and verify an isolated, direct-origin Chromium/Node 22 QA container."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("lab_dir")
parser.add_argument("qa_source")
parser.add_argument("--instance", default="qa")
parser.add_argument("--image", choices=("varal11-browser-lab:node22", "varal11-browser-webkit-lab:ca"), default="varal11-browser-lab:node22")
parser.add_argument("--proof-file", default="browser-proof.json")
args = parser.parse_args()
if not re.fullmatch(r"[a-z0-9]{2,16}", args.instance):
    raise SystemExit("invalid browser instance")
if not re.fullmatch(r"browser-proof(?:-[a-z0-9]{2,16})?\.json", args.proof_file):
    raise SystemExit("invalid proof filename")
root, source = Path(args.lab_dir), Path(args.qa_source)
if root.parent != Path("/tmp") or not root.name.startswith("varal11-stack."):
    raise SystemExit("invalid laboratory directory")
if source != Path("/tmp/varal11-qa-source/web") or not (source / "playwright.lab11.config.ts").is_file():
    raise SystemExit("invalid read-only QA snapshot")
project = (root / "project").read_text().strip()
if project != root.name.lower().replace(".", "-"):
    raise SystemExit("invalid laboratory project")
values = dict(line.split("=", 1) for line in (root / "lab.env").read_text().splitlines() if "=" in line)
port = int(values["LAB_PORT"])
network = project + "_frontend"
edge_name = project + "-edge-1"
edge = json.loads(subprocess.check_output(["docker", "inspect", edge_name], text=True))[0]
if edge["Config"]["Labels"].get("com.docker.compose.project") != project or not edge["State"]["Running"]:
    raise SystemExit("laboratory edge not running")
edge_ip = edge["NetworkSettings"]["Networks"][network]["IPAddress"]
net = json.loads(subprocess.check_output(["docker", "network", "inspect", network], text=True))[0]
if not net["Internal"]:
    raise SystemExit("QA network is not internal")
image = args.image
name = project + "-browser-" + args.instance
probe = subprocess.run(["docker", "inspect", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
if probe.returncode == 0:
    raise SystemExit("browser container already exists")
output = root / "qa"
output.mkdir(mode=0o700, exist_ok=True)
# Parent lab directory is private; the bind-mounted output must be writable by UID 1001.
os.chmod(output, 0o777)
(output / "project" / "web").mkdir(parents=True, exist_ok=True)
if (output / "ca.pem").exists():
    if (output / "ca.pem").read_bytes() != (root / "tls/ca.pem").read_bytes():
        raise SystemExit("QA CA does not match laboratory CA")
else:
    shutil.copyfile(root / "tls/ca.pem", output / "ca.pem")
    os.chmod(output / "ca.pem", 0o444)
origin = f"https://varal.local:{port}"
command = [
    "docker", "run", "-d", "--name", name, "--label", f"varal.lab={project}", "--label", "varal.role=browser-qa",
    "--network", network, "--dns", "127.0.0.1", "--add-host", f"varal.local:{edge_ip}", "--add-host", f"s3.varal.local:{edge_ip}",
    "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--shm-size", "1g", "--log-driver", "none",
    "--tmpfs", "/tmp:uid=1001,gid=1001,mode=1777", "--tmpfs", "/home/pwuser:uid=1001,gid=1001,mode=0700",
    "-v", f"{root / 'tls/ca.pem'}:/run/lab-ca/ca.pem:ro", "-v", f"{output}:/qa", "-v", f"{source}:/qa/project/web:ro",
    "-e", f"LAB_BASE_URL={origin}", "-e", f"LAB_PROJECT={project}", "-e", "LAB_QA_OUTPUT=/qa", "-e", f"LAB_BROWSER_PROOF=/qa/{args.proof_file}",
    "-e", "LAB_CDP_URL=http://127.0.0.1:9222", "-e", "NODE_EXTRA_CA_CERTS=/qa/ca.pem", image,
]
container_id = subprocess.check_output(command, text=True).strip()
try:
    info = json.loads(subprocess.check_output(["docker", "inspect", container_id], text=True))[0]
    if info["Config"]["User"] != "1001:1001" or set(info["NetworkSettings"]["Networks"]) != {network} or info["NetworkSettings"]["Ports"]:
        raise RuntimeError("unexpected browser container privileges")
    if any(mount.get("Destination") == "/var/run/docker.sock" for mount in info["Mounts"]):
        raise RuntimeError("Docker socket is mounted")
    version = subprocess.check_output(["docker", "exec", container_id, "node", "--version"], text=True).strip()
    if version != "v22.23.5":
        raise RuntimeError("unexpected Node version")
    # The runtime network has no gateway; DNS is confined to a nonexistent local resolver.
    egress_code = "import socket,sys\ns=socket.socket();s.settimeout(2)\ntry:s.connect(('1.1.1.1',443))\nexcept OSError:sys.exit(0)\nsys.exit(1)"
    subprocess.run(["docker", "exec", container_id, "python3", "-c", egress_code], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Verify that Chromium itself trusts the CA, with certificate errors enforced.
    js = """const {chromium}=require('/opt/qa/node_modules/playwright');
(async()=>{const b=await chromium.connectOverCDP('http://127.0.0.1:9222',{timeout:60000});const c=await b.newContext({ignoreHTTPSErrors:false});const p=await c.newPage();const r=await p.goto(process.env.LAB_BASE_URL+'/api/ready/',{timeout:60000});if(!r||r.status()!==200)throw Error('readiness');await c.close();await b.close();})().catch(()=>process.exit(1));"""
    for attempt in range(30):
        result = subprocess.run(["docker", "exec", container_id, "node", "-e", js], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if result.returncode == 0:
            break
        if attempt == 29:
            raise RuntimeError("Chromium direct TLS verification failed")
        time.sleep(1)
    proof = {"origin": origin, "network": network, "direct": True, "browser_image_id": info["Image"], "docker_socket": False, "egress": False, "ephemeral_profile": True, "node_version": version, "ca_sha256": hashlib.sha256((root / "tls/ca.pem").read_bytes()).hexdigest(), "browser_ip": info["NetworkSettings"]["Networks"][network]["IPAddress"], "sandbox": "chromium-no-sandbox-in-restricted-container"}
    proof_path = output / args.proof_file
    if proof_path.exists():
        prior = output / ("browser-proof-before-" + args.instance + ".json")
        if prior.exists():
            raise RuntimeError("prior browser proof exists")
        shutil.copyfile(proof_path, prior)
    proof_path.write_text(json.dumps(proof, sort_keys=True, separators=(",", ":")) + "\n")
    os.chmod(proof_path, 0o644)
    id_path = root / ("browser-container-id" if args.proof_file == "browser-proof.json" else "browser-container-id-" + args.instance)
    id_path.write_text(container_id + "\n")
    os.chmod(id_path, 0o600)
    print(f"browser QA ready: {name}; proof {proof_path}; Node {version}")
except BaseException:
    subprocess.run(["docker", "rm", "-f", container_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    raise
