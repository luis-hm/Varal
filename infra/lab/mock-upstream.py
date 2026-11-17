"""Synthetic upstream solely for the isolated proxy contract probe."""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        payload = json.dumps(
            {
                "host": self.headers.get("Host"),
                "forwarded": self.headers.get("Forwarded"),
                "xff": self.headers.get("X-Forwarded-For"),
                "proto": self.headers.get("X-Forwarded-Proto"),
                "cookie": self.headers.get("Cookie"),
                "expected": self.headers.get("X-Varal-Identidade-Esperada"),
                "path": self.path,
            }
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *_args):
        pass


for port in (8000, 3000, 9000):
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
threading.Event().wait()
