"""Minimal structured diagnostics without untrusted URLs, payloads or tracebacks."""

import json
import logging


class SafeFilter(logging.Filter):
    def filter(self, record):
        # Scrub before downstream handlers or telemetry receive the record.
        record.msg = "application_log"
        record.args = ()
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
        for field in ("request", "response", "url", "path", "headers", "data"):
            record.__dict__.pop(field, None)
        return True


class SafeFormatter(logging.Formatter):
    def format(self, record):
        # Never interpolate messages, args, request objects or exception text.
        return json.dumps(
            {"logger": record.name, "level": record.levelname, "event": "application_log"},
            separators=(",", ":"),
        )
