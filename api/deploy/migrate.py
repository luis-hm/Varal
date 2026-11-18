"""Run migrations once and protect system tables from the runtime role."""

import fcntl
import os
import subprocess
import sys

import psycopg
from psycopg import sql

with open("/varal/lock/migrate.lock", "a+b") as lock:
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("migration lock unavailable", file=sys.stderr)
        sys.exit(1)
    result = subprocess.run(
        ["python", "manage.py", "migrate", "--noinput"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode:
        print("migration failed", file=sys.stderr)
        sys.exit(result.returncode)
    try:
        with (
            psycopg.connect(
                dbname=os.environ["POSTGRES_DB"],
                user=os.environ["POSTGRES_USER"],
                password=os.environ["POSTGRES_PASSWORD"],
                host=os.environ["POSTGRES_HOST"],
            ) as connection,
            connection.cursor() as cursor,
        ):
            for table in ("privacidade_revisaoexportacao", "django_migrations"):
                cursor.execute(
                    sql.SQL(
                        "REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON TABLE {} FROM {}"
                    ).format(
                        sql.Identifier("public", table),
                        sql.Identifier(os.environ["VARAL_RUNTIME_DB_ROLE"]),
                    )
                )
    except Exception:  # noqa: BLE001 -- Keep errors from containing SQL or user data.
        print("migration permissions failed", file=sys.stderr)
        sys.exit(1)
