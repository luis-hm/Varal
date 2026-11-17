"""Local-only raw TLS relay to an internal Docker edge; never logs traffic.

Each connection uses docker exec and is therefore unsuitable for performance measurements.
"""

import argparse
import os
import socket
import socketserver
import subprocess
import threading


class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        if self.server.python_target:
            bridge = """import os,selectors,socket,sys
s=socket.create_connection(('127.0.0.1',int(sys.argv[1])),timeout=5)
s.settimeout(None)
sel=selectors.DefaultSelector()
sel.register(sys.stdin.buffer,selectors.EVENT_READ)
sel.register(s,selectors.EVENT_READ)
while sel.get_map():
 for key,_ in sel.select():
  if key.fileobj is s:
   data=s.recv(65536)
   if not data: sys.exit(0)
   sys.stdout.buffer.write(data); sys.stdout.buffer.flush()
  else:
   data=os.read(0,65536)
   if data: s.sendall(data)
   else: sel.unregister(sys.stdin.buffer); s.shutdown(socket.SHUT_WR)
"""
            command = ["docker", "exec", "-i", self.server.edge_id, "python3", "-c", bridge, str(self.server.target_port)]
        else:
            command = ["docker", "exec", "-i", self.server.edge_id, "nc", "127.0.0.1", str(self.server.target_port)]
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )

        def upstream():
            try:
                while data := self.request.recv(65536):
                    process.stdin.write(data)
                    process.stdin.flush()
            except (OSError, ValueError):
                pass
            finally:
                process.stdin.close()

        self.request.settimeout(60)
        thread = threading.Thread(target=upstream, daemon=True)
        thread.start()
        try:
            while data := os.read(process.stdout.fileno(), 65536):
                self.request.sendall(data)
        except OSError:
            pass
        finally:
            try:
                self.request.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            thread.join(timeout=1)


class Relay(socketserver.ThreadingTCPServer):
    allow_reuse_address = False
    daemon_threads = True

    def handle_error(self, _request, _client_address):
        # Do not expose request bytes, URLs, headers or exception details.
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--edge-id", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--target-port", type=int, default=8443)
    parser.add_argument("--python-target", action="store_true")
    args = parser.parse_args()
    if len(args.edge_id) != 64 or any(
        c not in "0123456789abcdef" for c in args.edge_id
    ):
        raise SystemExit("invalid lab container ID")
    if not 1024 <= args.port <= 65535 or not 1024 <= args.target_port <= 65535:
        raise SystemExit("invalid local port")
    with Relay(("127.0.0.1", args.port), Handler) as server:
        server.edge_id = args.edge_id
        server.target_port = args.target_port
        server.python_target = args.python_target
        server.serve_forever()


if __name__ == "__main__":
    main()
