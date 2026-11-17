"""Disposable STARTTLS SMTP capture: synthetic .invalid recipients only, never relay."""

import os
import socketserver
import ssl
import uuid
from email.utils import parseaddr
from pathlib import Path


class Handler(socketserver.StreamRequestHandler):
    def reply(self, message):
        self.wfile.write(message + b"\r\n")
        self.wfile.flush()

    def handle(self):
        secure = sender = recipient = False
        self.connection.settimeout(10)
        self.reply(b"220 capture.local ESMTP")
        while line := self.rfile.readline(8193):
            if len(line) > 8192:
                self.reply(b"500 line too long")
                return
            command, _, argument = line.rstrip(b"\r\n").partition(b" ")
            command = command.upper()
            if command in (b"EHLO", b"HELO"):
                if secure:
                    self.reply(b"250 capture.local")
                else:
                    self.reply(b"250-capture.local")
                    self.reply(b"250 STARTTLS")
            elif command == b"STARTTLS" and not secure:
                self.reply(b"220 Ready to start TLS")
                self.rfile.close()
                self.wfile.close()
                self.connection = self.server.context.wrap_socket(
                    self.connection, server_side=True
                )
                self.rfile = self.connection.makefile("rb", self.rbufsize)
                self.wfile = self.connection.makefile("wb", self.wbufsize)
                secure = True
                sender = recipient = False
            elif (
                secure and command == b"MAIL" and argument.upper().startswith(b"FROM:")
            ):
                sender, recipient = True, False
                self.reply(b"250 OK")
            elif (
                secure
                and command == b"RCPT"
                and sender
                and argument.upper().startswith(b"TO:")
            ):
                address = parseaddr(argument[3:].decode("ascii", "replace"))[1].lower()
                recipient = address.endswith(".invalid") and "@" in address
                self.reply(b"250 OK" if recipient else b"550 synthetic recipients only")
            elif secure and command == b"DATA" and recipient:
                self.reply(b"354 End with <CRLF>.<CRLF>")
                data = bytearray()
                while True:
                    part = self.rfile.readline(8193)
                    if not part or len(part) > 8192 or len(data) + len(part) > 1048576:
                        return
                    if part == b".\r\n":
                        break
                    data.extend(part[1:] if part.startswith(b"..") else part)
                path = Path("/capture") / f"{uuid.uuid4()}.eml"
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "wb") as output:
                    output.write(data)
                sender = recipient = False
                self.reply(b"250 Captured")
            elif command == b"RSET":
                sender = recipient = False
                self.reply(b"250 OK")
            elif command == b"QUIT":
                self.reply(b"221 Bye")
                return
            else:
                self.reply(b"503 Unsupported or out of sequence")


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def handle_error(self, _request, _client_address):
        # Never print message content, addresses, or untrusted protocol lines.
        pass


if __name__ == "__main__":
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain("/run/smtp/cert.pem", "/run/smtp/key.pem")
    with Server(("0.0.0.0", 1025), Handler) as server:
        server.context = context
        server.serve_forever()
