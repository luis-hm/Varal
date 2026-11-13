from django.db import migrations


def criar_espacos_pessoais(apps, schema_editor):
    Usuario = apps.get_model("contas_usuario", "Usuario")
    Espaco = apps.get_model("espacos", "Espaco")
    for usuario in Usuario.objects.using(schema_editor.connection.alias).iterator():
        Espaco.objects.using(schema_editor.connection.alias).get_or_create(
            dono_id=usuario.pk, tipo="pessoal", defaults={"nome": "Pessoal"}
        )


class Migration(migrations.Migration):
    dependencies = [
        ("contas_usuario", "0002_alter_usuario_options_usuario_nome_and_more"),
        ("espacos", "0001_initial"),
    ]
    operations = [migrations.RunPython(criar_espacos_pessoais, migrations.RunPython.noop)]
