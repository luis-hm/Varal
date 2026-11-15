from django.db import migrations


def dono_vira_admin(apps, schema_editor):
    """Groups stop having an owner: any legacy owner becomes an admin Membro (RN04)."""
    db = schema_editor.connection.alias
    Espaco = apps.get_model("espacos", "Espaco")
    Membro = apps.get_model("espacos", "Membro")
    for grupo in Espaco.objects.using(db).filter(tipo="grupo", dono__isnull=False):
        Membro.objects.using(db).update_or_create(
            espaco_id=grupo.pk, usuario_id=grupo.dono_id, defaults={"papel": "admin"}
        )
        grupo.dono_id = None
        grupo.save(update_fields=["dono"])


class Migration(migrations.Migration):
    dependencies = [("espacos", "0003_membro_convite_subgrupo")]
    operations = [migrations.RunPython(dono_vira_admin, migrations.RunPython.noop)]
