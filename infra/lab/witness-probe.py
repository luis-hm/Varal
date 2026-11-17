"""Run the real backend witness against the disposable lab PostgreSQL and archive."""

import importlib.util
import os

from django.conf import settings

settings.configure(
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["POSTGRES_DB"],
            "USER": os.environ["POSTGRES_USER"],
            "PASSWORD": os.environ["POSTGRES_PASSWORD"],
            "HOST": "postgres",
            "PORT": 5432,
        }
    },
    INSTALLED_APPS=[],
    VARAL_WAL_WITNESS_DIR="/run/wal-witness",
    VARAL_WAL_WITNESS_KEY_FILE="/run/keys/witness",
    VARAL_WAL_WITNESS_EPOCH=os.environ["JOURNAL_EPOCH"],
    VARAL_WAL_WITNESS_TIMEOUT=40,
)
import django

django.setup()
from django.db import connection

spec = importlib.util.spec_from_file_location(
    "witness_probe_module", "/probe/witness.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with connection.cursor() as cursor:
    cursor.execute("INSERT INTO wal_witness_probe DEFAULT VALUES")
module.testemunhar()
# A bad MAC key must not grant permission to send, even though PostgreSQL was reachable.
with connection.cursor() as cursor:
    cursor.execute("INSERT INTO wal_witness_probe DEFAULT VALUES")
settings.VARAL_WAL_WITNESS_KEY_FILE = "/run/keys/wrong"
try:
    module.testemunhar()
except module.WitnessIndisponivel:
    pass
else:
    raise AssertionError("invalid witness unexpectedly accepted")
print("backend witness accepted authentic archived WAL and rejected invalid MAC: ok")
