"""Revision coverage for exported data and its ACL dependencies.

Operational queues, auth sessions and EmailAddress are deliberately excluded. If the
export schema or its access predicates grow, update this inventory and its tests.
"""

import uuid

from django.db import migrations

TABLES = (
    "espacos_espaco",
    "espacos_membro",
    "espacos_subgrupo",
    "lancamentos_lancamento",
    "lancamento_acesso",
    "lancamentos_historico",
    "boletos_instrumento",
    "boletos_documentoboleto",
    "pagamentos_pagamento",
    "pagamentos_documentocomprovante",
    "recorrencias_recorrencia",
    "recorrencias_recorrencia_acesso",
    "recorrencias_revisaorecorrencia",
    "recorrencias_competenciadevida",
    "notificacoes_eventonotificacao",
    "notificacoes_notificacao",
    "solicitacoes_solicitacao",
    "solicitacoes_parpagamento",
)


def forwards(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        raise RuntimeError("A revisão de exportação requer PostgreSQL")
    Revisao = apps.get_model("privacidade", "RevisaoExportacao")
    revisao, created = Revisao.objects.using(schema_editor.connection.alias).get_or_create(
        id=1, defaults={"epoca": uuid.uuid4(), "valor": 0}
    )
    if not created:
        # Reapplying after a rollback invalidates snapshots made before the gap.
        revisao.epoca = uuid.uuid4()
        revisao.save(using=schema_editor.connection.alias, update_fields=["epoca"])
    schema_editor.execute("""
        CREATE FUNCTION public.varal_revisao_exportacao() RETURNS trigger
        SECURITY DEFINER SET search_path = pg_catalog AS $$
        BEGIN
            UPDATE public.privacidade_revisaoexportacao SET valor = valor + 1 WHERE id = 1;
            IF NOT FOUND THEN RAISE EXCEPTION 'revisao ausente'; END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql
    """)
    quote = schema_editor.quote_name
    for table in TABLES:
        schema_editor.execute(
            f"CREATE TRIGGER revisao_exportacao AFTER INSERT OR UPDATE OR DELETE ON {quote(table)} "
            "FOR EACH STATEMENT EXECUTE FUNCTION public.varal_revisao_exportacao()"
        )
    schema_editor.execute("""
        CREATE TRIGGER revisao_usuario_criacao AFTER INSERT OR DELETE ON contas_usuario_usuario
        FOR EACH STATEMENT EXECUTE FUNCTION public.varal_revisao_exportacao()
    """)
    schema_editor.execute("""
        CREATE TRIGGER revisao_usuario_edicao AFTER UPDATE OF nome, email, telefone,
            prefs_notificacao, is_active, password ON contas_usuario_usuario
        FOR EACH STATEMENT EXECUTE FUNCTION public.varal_revisao_exportacao()
    """)


def backwards(apps, schema_editor):
    quote = schema_editor.quote_name
    for table in TABLES:
        schema_editor.execute(f"DROP TRIGGER IF EXISTS revisao_exportacao ON {quote(table)}")
    schema_editor.execute("DROP TRIGGER IF EXISTS revisao_usuario_criacao ON contas_usuario_usuario")
    schema_editor.execute("DROP TRIGGER IF EXISTS revisao_usuario_edicao ON contas_usuario_usuario")
    schema_editor.execute("DROP FUNCTION IF EXISTS public.varal_revisao_exportacao()")


class Migration(migrations.Migration):
    dependencies = [
        ("privacidade", "0001_initial"),
        ("contas_usuario", "0003_alter_usuario_managers"),
        ("espacos", "0006_janela_alerta_1_a_7"),
        ("lancamentos", "0004_lancamento_recorrencia_and_more"),
        ("boletos", "0004_pin_e_copia_pdf"),
        ("pagamentos", "0002_limpezacomprovante_geracao_and_more"),
        ("recorrencias", "0003_remove_recorrencia_criador_membro"),
        ("notificacoes", "0006_alter_eventonotificacao_tipo"),
        ("solicitacoes", "0001_initial"),
    ]
    operations = [migrations.RunPython(forwards, backwards)]
