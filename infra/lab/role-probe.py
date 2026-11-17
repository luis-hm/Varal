"""Probe runtime DB privilege boundaries with synthetic, rolled-back domain data."""

import os
import uuid

import psycopg

assert not any(key.startswith("LAB_") for key in os.environ)
assert "MIGRATE_PASSWORD" not in os.environ and "APP_PASSWORD" not in os.environ


class RollbackProbe(Exception):
    pass


with psycopg.connect(
    dbname=os.environ["POSTGRES_DB"],
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    host=os.environ["POSTGRES_HOST"],
) as connection:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT rolsuper, rolcreaterole, rolcreatedb FROM pg_roles WHERE rolname=current_user"
        )
        assert cursor.fetchone() == (False, False, False)
        cursor.execute(
            "SELECT pg_has_role(current_user, %s, 'MEMBER')", ("varal_migrate",)
        )
        assert cursor.fetchone()[0] is False
        for privilege in ("INSERT", "UPDATE", "DELETE", "TRUNCATE", "TRIGGER"):
            cursor.execute(
                "SELECT has_table_privilege(current_user, 'public.privacidade_revisaoexportacao', %s)",
                (privilege,),
            )
            assert cursor.fetchone()[0] is False
        for privilege in ("INSERT", "UPDATE", "DELETE", "SELECT"):
            cursor.execute(
                "SELECT has_table_privilege(current_user, 'public.espacos_espaco', %s)",
                (privilege,),
            )
            assert cursor.fetchone()[0] is True
        cursor.execute(
            "SELECT has_table_privilege(current_user, 'public.espacos_espaco', 'TRIGGER')"
        )
        assert cursor.fetchone()[0] is False
        cursor.execute("SELECT has_schema_privilege(current_user, 'public', 'CREATE')")
        assert cursor.fetchone()[0] is False
    try:
        with connection.transaction():  # noqa: SIM117 -- Rollback scope is explicit.
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT valor FROM public.privacidade_revisaoexportacao WHERE id=1"
                )
                previous = cursor.fetchone()[0]
                cursor.execute(
                    "INSERT INTO public.espacos_espaco (id, tipo, nome, dono_id, janela_alerta_dias) VALUES (%s, 'grupo', 'synthetic', NULL, 3)",
                    (uuid.uuid4(),),
                )
                cursor.execute(
                    "SELECT valor FROM public.privacidade_revisaoexportacao WHERE id=1"
                )
                assert cursor.fetchone()[0] > previous
                raise RollbackProbe
    except RollbackProbe:
        pass
print("runtime role boundaries and revision trigger: ok")
