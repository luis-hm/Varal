"""Disposable SMTP receiver for local integration tests, never a mail relay."""

import os
import socketserver
from email.utils import parseaddr
from pathlib import Path


class Handler(socketserver.StreamRequestHandler):
    def reply(self, message):
        self.wfile.write(message + b"\r\n")
        self.wfile.flush()

    def handle(self):
        self.reply(b"220 capture.local ESMTP")
        sender = False
        recipient = False
        while line := self.rfile.readline(8193):
            if len(line) > 8192:
                self.reply(b"500 line too long")
                return
            command, _, argument = line.rstrip(b"\r\n").partition(b" ")
            command = command.upper()
            if command in (b"EHLO", b"HELO"):
                self.reply(b"250 capture.local")
            elif command == b"MAIL" and argument.upper().startswith(b"FROM:"):
                sender, recipient = True, False
                self.reply(b"250 OK")
            elif command == b"RCPT" and sender and argument.upper().startswith(b"TO:"):
                address = parseaddr(argument[3:].decode("ascii", "replace"))[1].lower()
                recipient = address.endswith(".invalid") and "@" in address
                self.reply(b"250 OK" if recipient else b"550 synthetic recipients only")
            elif command == b"DATA" and recipient:
                self.reply(b"354 End with <CRLF>.<CRLF>")
                data = bytearray()
                while True:
                    part = self.rfile.readline(8193)
                    if not part or len(part) > 8192 or len(data) + len(part) > 1048576:
                        return
                    if part == b".\r\n":
                        break
                    data.extend(part[1:] if part.startswith(b"..") else part)
                path = Path("/tmp/varal-smtp-capture.eml")
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
                with os.fdopen(fd, "wb") as output:
                    output.write(data)
                sender, recipient = False, False
                self.reply(b"250 Captured")
            elif command == b"RSET":
                sender, recipient = False, False
                self.reply(b"250 OK")
            elif command == b"QUIT":
                self.reply(b"221 Bye")
                return
            else:
                self.reply(b"503 Unsupported or out of sequence")


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    with Server(("0.0.0.0", 1025), Handler) as server:
        server.serve_forever()
