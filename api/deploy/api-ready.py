"""Run the application's readiness checks without trusting an HTTP proxy header."""

import os
import socket
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # /app
try:
    with socket.create_connection(("127.0.0.1", 8000), timeout=2):
        pass
    import django

    django.setup()
    from config.views import readiness
    from django.test import RequestFactory

    result = readiness(RequestFactory().get("/api/ready/"))
    sys.exit(0 if result.status_code == 200 else 1)
except Exception:  # noqa: BLE001 -- Probe failures must remain quiet and unhealthy.
    # Health probes must not print potentially sensitive exception details.
    sys.exit(1)
