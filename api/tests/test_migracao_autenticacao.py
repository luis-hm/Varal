from importlib import import_module

import pytest
from django.apps import apps
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from apps.contas_usuario.models import Usuario
from apps.espacos.models import Espaco


@pytest.mark.django_db(transaction=True)
def test_rn03_ca05_migracao_preserva_legado_e_cria_espaco_unico():
    executor = MigrationExecutor(connection)
    final_targets = executor.loader.graph.leaf_nodes()
    initial_targets = [("contas_usuario", "0001_initial"), ("espacos", "0001_initial")]
    try:
        executor.migrate(initial_targets)
        state = executor.loader.project_state(initial_targets)
        LegacyUser = state.apps.get_model("contas_usuario", "Usuario")
        user = LegacyUser.objects.create(
            username="legacy", email="legacy@example.com", password="existing-hash"
        )
        user_id = user.pk
        MigrationExecutor(connection).migrate(final_targets)
        migrated = Usuario.objects.get(pk=user_id)
        assert migrated.password == "existing-hash"
        assert migrated.nome == "" and migrated.prefs_notificacao == {}
        original = Espaco.objects.get(dono_id=user_id).pk
        migration = import_module("apps.espacos.migrations.0002_pessoais_existentes")
        with connection.schema_editor() as editor:
            migration.criar_espacos_pessoais(apps, editor)
        assert Espaco.objects.get(dono_id=user_id).pk == original
    finally:
        MigrationExecutor(connection).migrate(final_targets)
