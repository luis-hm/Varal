"""Exercise actual read-only proxies with private mocks and colliding shared aliases.

All networks/containers are new and private. No ports, application credentials or existing
volumes are used. The fixture is not a claim about the cause of a remote health failure.
"""

import ipaddress
import json
import secrets
import subprocess
import time

PREFIX = "varal-hmg-http-qa-" + secrets.token_hex(6)
DOMAIN = "hmgvaral.codehub.systems"
PROXY = "varal-hmg-validation-proxy:20261117"
MOCK = "varal-hmg-validation-bootstrap:20261117"
containers = []
networks = []

SERVER = r'''
import http.server,json,os,threading,time
identity=os.environ['IDENTITY']
count=0
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args): pass
 def do_GET(self):
  global count
  if self.path=='/qa/count':
   value={'count':count}
  else:
   count+=1
   if identity=='private-api' and (
    self.headers.get_all('Host')!=[os.environ['PUBLIC_DOMAIN']] or
    self.headers.get('X-Forwarded-Proto')!='https' or
    self.client_address[0] not in os.environ['TRUSTED_PEERS'].split(',')
   ):
    self.send_response(400); self.end_headers(); return
   value={'identity':identity,'path':self.path,'host':self.headers.get_all('Host'),
    'xff':self.headers.get('X-Forwarded-For'),'proto':self.headers.get('X-Forwarded-Proto'),
    'cookie':self.headers.get('Cookie'),'expected':self.headers.get('X-Varal-Identidade-Esperada'),
    'authorization':self.headers.get('Authorization'),'forwarded':self.headers.get('Forwarded')}
  payload=json.dumps(value).encode()
  self.send_response(200); self.send_header('Content-Type','application/json')
  self.send_header('Content-Length',str(len(payload))); self.end_headers(); self.wfile.write(payload)
for port in map(int,os.environ['PORTS'].split(',')):
 server=http.server.ThreadingHTTPServer(('0.0.0.0',port),Handler)
 threading.Thread(target=server.serve_forever,daemon=True).start()
while True: time.sleep(1)
'''

CLIENT = r'''
import http.client,json,sys
connection=http.client.HTTPConnection(sys.argv[1],int(sys.argv[2]),timeout=5)
connection.request(sys.argv[3],sys.argv[4],headers=json.loads(sys.argv[5]))
response=connection.getresponse()
body=response.read().decode()
try: payload=json.loads(body)
except ValueError: payload=None
print(json.dumps({'status':response.status,'payload':payload}))
'''


def docker(arguments, expected=0):
    result = subprocess.run(["docker", *arguments], capture_output=True, text=True)
    if result.returncode != expected:
        raise RuntimeError(result.stderr[-2000:])
    return result.stdout.strip()


def start(role, arguments, image, command):
    name = PREFIX + "-" + role
    containers.append(name)
    docker(["run", "-d", "--name", name, *arguments, image, *command])
    return name


def request(source, target, path, *, port=8080, method="GET", headers=None):
    return json.loads(docker([
        "exec", source, "python", "-c", CLIENT, target, str(port), method, path,
        json.dumps(headers or {"Host": DOMAIN}),
    ]))


def ensure_started(name):
    for _ in range(40):
        result = subprocess.run(
            ["docker", "exec", name, "nginx", "-t", "-c", "/tmp/nginx.conf"],
            capture_output=True,
        )
        if result.returncode == 0:
            return
        time.sleep(0.1)
    raise RuntimeError("proxy did not start with its read-only filesystem")


try:
    ids = docker(["network", "ls", "-q"]).splitlines()
    used = [
        ipaddress.ip_network(config["Subnet"])
        for network in json.loads(docker(["network", "inspect", *ids]))
        for config in (network.get("IPAM", {}).get("Config") or [])
        if config.get("Subnet") and ":" not in config["Subnet"]
    ]
    pools = []
    for base in ("172.29", "172.28", "10.254", "10.253"):
        for octet in range(249, 210, -1):
            candidate = ipaddress.ip_network(f"{base}.{octet}.0/24")
            if not any(candidate.overlaps(value) for value in used):
                pools.append(candidate)
                if len(pools) == 3:
                    break
        if len(pools) == 3:
            break
    assert len(pools) == 3
    for role, subnet in zip(("application", "frontend", "shared"), pools, strict=True):
        name = PREFIX + "-" + role
        docker(["network", "create", "--internal", "--subnet", str(subnet), name])
        networks.append(name)
    application, frontend, shared = networks
    edge_ip = str(pools[0].network_address + 240)
    ssr_ip = str(pools[0].network_address + 241)
    web_ip = str(pools[1].network_address + 240)

    api = start("api", [
        "--network", application, "--network-alias", "hmgvaral-api", "--network-alias", "api",
        "-e", "IDENTITY=private-api", "-e", "PORTS=8000", "-e", "PUBLIC_DOMAIN=" + DOMAIN,
        "-e", "TRUSTED_PEERS=" + edge_ip + "," + ssr_ip, "--entrypoint", "python",
    ], MOCK, ["-c", SERVER])
    web = start("web", [
        "--network", frontend, "--ip", web_ip, "--network-alias", "hmgvaral-web", "--network-alias", "web",
        "-e", "IDENTITY=private-web", "-e", "PORTS=3000", "--entrypoint", "python",
    ], MOCK, ["-c", SERVER])
    decoy = start("foreign", [
        "--network", shared, "--network-alias", "api", "--network-alias", "web",
        "--network-alias", "foreign-api", "--network-alias", "coolify-proxy",
        "-e", "IDENTITY=foreign-app", "-e", "PORTS=8000,3000", "--entrypoint", "python",
    ], MOCK, ["-c", SERVER])
    common = [
        "--read-only", "--tmpfs", "/tmp:mode=1777",
        "-e", "VARAL_DOMAIN=" + DOMAIN, "-e", "VARAL_STACK=hmgvaral",
    ]
    ssr = start("ssr", [
        *common, "--network", "name=" + application + ",ip=" + ssr_ip,
        "--network", "name=" + frontend,
        "-e", "VARAL_PROXY_ROLE=ssr", "-e", "VARAL_WEB_IP=" + web_ip,
    ], PROXY, [])
    edge = start("edge", [
        *common, "--network", "name=" + shared,
        "--network", "name=" + application + ",ip=" + edge_ip,
        "--network", "name=" + frontend,
        "-e", "VARAL_PROXY_ROLE=edge", "-e", "COOLIFY_PROXY_TRUST=coolify-proxy",
    ], PROXY, [])
    ensure_started(edge)
    ensure_started(ssr)

    # Establish that the foreign app is reachable, without sending actual credentials.
    foreign = json.loads(docker(["exec", edge, "wget", "-qO-", "http://foreign-api:8000/api/probe"]))
    assert foreign["identity"] == "foreign-app"
    before = request(decoy, "127.0.0.1", "/qa/count", port=8000)["payload"]["count"]

    # Execute precisely the health command from the deployment manifest.
    docker(["exec", edge, "/bin/sh", "-c",
            'wget -q -O /dev/null --header="Host: $VARAL_DOMAIN" http://127.0.0.1:8080/api/ready/'])
    print("PASS exact edge healthcheck reaches private API with one valid Host and trusted HTTPS peer")

    for _ in range(10):
        result = request(web, edge, "/api/me/")
        assert result["status"] == 200 and result["payload"]["identity"] == "private-api"
        result = request(web, edge, "/entrar")
        assert result["status"] == 200 and result["payload"]["identity"] == "private-web"
    result = request(web, edge, "/accounts/google/login/callback/")
    assert result["status"] == 200 and result["payload"]["identity"] == "private-api"
    print("PASS edge selects stack-specific API/web despite reachable foreign api/web aliases")

    trusted = request(decoy, edge, "/api/me/", headers={
        "Host": DOMAIN, "X-Forwarded-For": "203.0.113.10", "X-Forwarded-Proto": "http",
    })
    assert trusted["payload"]["xff"] == "203.0.113.10" and trusted["payload"]["proto"] == "https"
    untrusted = request(web, edge, "/api/me/", headers={
        "Host": DOMAIN, "X-Forwarded-For": "203.0.113.99", "Forwarded": "for=203.0.113.99",
    })
    assert untrusted["payload"]["xff"] == web_ip and untrusted["payload"]["forwarded"] is None
    print("PASS trusted proxy preserves client address; untrusted peer cannot forge XFF")

    for path in (
        "/api/me/", "/api/notificacoes/resumo/",
        "/api/espacos/00000000-0000-0000-0000-000000000001/resumo/",
    ):
        result = request(web, ssr, path, headers={
            "Host": "ignored.invalid", "Cookie": "sessionid=synthetic",
            "X-Varal-Identidade-Esperada": "synthetic-owner", "Authorization": "synthetic-denied",
        })
        assert result["status"] == 200 and result["payload"]["identity"] == "private-api"
        assert result["payload"]["cookie"] == "sessionid=synthetic"
        assert result["payload"]["expected"] == "synthetic-owner"
        assert result["payload"]["authorization"] is None
    assert request(web, ssr, "/api/me/", method="POST")["status"] == 405
    assert request(web, ssr, "/api/me/?extra=1")["status"] == 404
    assert request(web, ssr, "/api/ready/")["status"] == 404
    print("PASS SSR keeps exact three GET routes, cookie/identity allowlist and rejects mutations/query")

    after = request(decoy, "127.0.0.1", "/qa/count", port=8000)["payload"]["count"]
    assert before == after
    print("PASS foreign application received no edge or SSR requests from the tested flows")
    print("HTTP private-upstream/health/proxy checks: 5/5 groups passed with no published ports.")
finally:
    for name in containers:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
    for name in reversed(networks):
        subprocess.run(["docker", "network", "rm", name], capture_output=True)
