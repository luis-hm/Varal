#!/bin/sh
set -eu
# Only disposable, explicitly named containers and one internal network created here.
base_dir=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
tmp_dir=$(mktemp -d /tmp/varal11-proxy.XXXXXXXX)
lab_id=$(basename "$tmp_dir" | tr '.' '-')
network_name="$lab_id-net"
mock_name="$lab_id-mock"
edge_name="$lab_id-edge"
ssr_name="$lab_id-ssr"
edge_id=
ssr_id=
mock_id=
network_id=
cleanup() {
    for owned_id in "$edge_id" "$ssr_id" "$mock_id"; do
        if [ -n "$owned_id" ]; then docker rm -f "$owned_id" >/dev/null 2>&1 || :; fi
    done
    if [ -n "$network_id" ]; then docker network rm "$network_id" >/dev/null 2>&1 || :; fi
    rm -rf "$tmp_dir"
}
trap cleanup EXIT HUP INT TERM
openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj /CN=varal11-test-ca -keyout "$tmp_dir/ca.key" -out "$tmp_dir/ca.pem" >/dev/null 2>&1
openssl req -newkey rsa:2048 -nodes -subj /CN=varal.local -keyout "$tmp_dir/key.pem" -out "$tmp_dir/leaf.csr" >/dev/null 2>&1
printf '%s\n' 'subjectAltName=DNS:varal.local,DNS:s3.varal.local' > "$tmp_dir/leaf.ext"
openssl x509 -req -in "$tmp_dir/leaf.csr" -CA "$tmp_dir/ca.pem" -CAkey "$tmp_dir/ca.key" -CAcreateserial -days 1 -extfile "$tmp_dir/leaf.ext" -out "$tmp_dir/cert.pem" >/dev/null 2>&1
chmod 600 "$tmp_dir/key.pem" "$tmp_dir/ca.key"
network_id=$(docker network create --internal --label "varal.lab=$lab_id" "$network_name")
mock_id=$(docker run -d --name "$mock_name" --label "varal.lab=$lab_id" --network "$network_name" --network-alias api --network-alias web --network-alias storage -v "$base_dir/infra/lab/mock-upstream.py:/mock.py:ro" python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b python /mock.py)
mock_ip=$(docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$mock_id")
case "$mock_ip" in *[!0-9.]*|'') echo 'invalid test IP' >&2; exit 1 ;; esac
sed "s/# LAB_SSR_ACCESS/allow $mock_ip; deny all;/" "$base_dir/infra/lab/ssr.conf" > "$tmp_dir/ssr.conf"
ssr_id=$(docker run -d --name "$ssr_name" --label "varal.lab=$lab_id" --network "$network_name" --network-alias ssr -v "$tmp_dir/ssr.conf:/etc/nginx/nginx.conf:ro" --entrypoint nginx nginx:1.30.6-alpine@sha256:901e593c95dc85f5a729f5765516321366ef4ac401821431d408897e95287d0a -g 'daemon off;')
edge_id=$(docker run -d --name "$edge_name" --label "varal.lab=$lab_id" --network "$network_name" --network-alias edge -v "$base_dir/infra/lab/nginx.conf:/etc/nginx/nginx.conf:ro" -v "$tmp_dir:/run/lab-tls:ro" --entrypoint nginx nginx:1.30.6-alpine@sha256:901e593c95dc85f5a729f5765516321366ef4ac401821431d408897e95287d0a -g 'daemon off;')
# Probe TLS from the private network, with a real CA and SNI; no service port is published.
docker cp "$tmp_dir/ca.pem" "$mock_name:/tmp/lab-ca.pem"
docker exec "$mock_name" python -c '
import http.client, json, socket, ssl, time
class LabHTTPS(http.client.HTTPSConnection):
    def connect(self):
        sock=socket.create_connection(("edge", 8443), timeout=3)
        self.sock=self._context.wrap_socket(sock, server_hostname="varal.local")
ctx=ssl.create_default_context(cafile="/tmp/lab-ca.pem")
for attempt in range(30):
    try:
        conn=LabHTTPS("varal.local", context=ctx, timeout=3)
        conn.request("GET", "/api/me/?marker=synthetic-sentinel", headers={"Host":"varal.local", "X-Forwarded-For":"203.0.113.111", "Forwarded":"for=203.0.113.112"})
        resp=conn.getresponse()
        assert resp.status == 200
        data=json.loads(resp.read())
        conn.close()
        break
    except (OSError, http.client.HTTPException):
        if attempt == 29: raise
        time.sleep(1)
assert data["xff"] != "203.0.113.111" and data["forwarded"] is None
assert data["proto"] == "https" and data["host"] == "varal.local"
class S3HTTPS(http.client.HTTPSConnection):
    def connect(self):
        sock=socket.create_connection(("edge", 8443), timeout=3)
        self.sock=self._context.wrap_socket(sock, server_hostname="s3.varal.local")
conn=S3HTTPS("s3.varal.local", context=ctx, timeout=3)
conn.request("GET", "/bucket/a%2Fb?sig=synthetic%252Dsentinel", headers={"Host":"s3.varal.local"})
resp=conn.getresponse()
assert resp.status == 200
s3=json.loads(resp.read())
assert s3["host"] == "s3.varal.local" and s3["path"] == "/bucket/a%2Fb?sig=synthetic%252Dsentinel"
conn.close()
try:
    socket.create_connection(("1.1.1.1", 443), timeout=2)
except OSError:
    pass
else:
    raise AssertionError("internal network permitted outbound connection")
'
# SSR is not published: probe it from the private test network.
docker exec "$mock_name" python -c '
import json, urllib.request, urllib.error
base="http://ssr:8080"
def get(path, headers=None):
    try:
        with urllib.request.urlopen(urllib.request.Request(base+path, headers=headers or {}), timeout=5) as r:
            return r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()
status, headers, body=get("/api/me/", {"Cookie":"fake=session", "X-Varal-Identidade-Esperada":"9ea37723-64dc-4924-b60a-c0e8c8a7f24f"})
assert status == 200 and "no-store" in headers["Cache-Control"]
data=json.loads(body)
assert data["cookie"] == "fake=session" and data["expected"] == "9ea37723-64dc-4924-b60a-c0e8c8a7f24f"
assert get("/api/notificacoes/resumo/")[0] == 200
assert get("/api/espacos/9ea37723-64dc-4924-b60a-c0e8c8a7f24f/resumo/")[0] == 200
assert get("/api/me/?x=1")[0] == 404
assert get("/api/espacos/../me/")[0] == 404
assert get("/api/auth/")[0] == 404
try:
    urllib.request.urlopen(urllib.request.Request(base+"/api/me/", data=b"", method="POST"), timeout=5)
except urllib.error.HTTPError as exc:
    assert exc.code == 405
else:
    raise AssertionError("SSR accepted POST")
'
# A different container on the same network must not reach the SSR listener.
if ! docker exec "$edge_name" sh -c 'wget -S -O /dev/null http://ssr:8080/api/me/ 2>&1' | grep -q '403 Forbidden'; then
    echo 'SSR peer isolation check failed' >&2
    exit 1
fi
for container_name in "$edge_name" "$ssr_name"; do
    if docker logs "$container_name" 2>&1 | grep -Eiq 'synthetic-sentinel|synthetic%252Dsentinel'; then exit 1; fi
done
printf '%s\n' 'isolated TLS edge, spoofed forwarding headers, SSR whitelist and log sentinel: ok'
