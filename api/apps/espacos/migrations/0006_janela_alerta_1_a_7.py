from django.db import migrations, models


def ajustar_janela(apps, schema_editor):
    # No row is lost: out-of-range windows (none expected, the default is 3) are clamped.
    Espaco = apps.get_model("espacos", "Espaco")
    Espaco.objects.filter(janela_alerta_dias__lt=1).update(janela_alerta_dias=1)
    Espaco.objects.filter(janela_alerta_dias__gt=7).update(janela_alerta_dias=7)


class Migration(migrations.Migration):
    dependencies = [("espacos", "0005_espaco_grupo_sem_dono")]
    operations = [
        migrations.RunPython(ajustar_janela, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="espaco",
            constraint=models.CheckConstraint(
                condition=models.Q(("janela_alerta_dias__gte", 1), ("janela_alerta_dias__lte", 7)),
                name="espaco_janela_alerta_1_a_7",
            ),
        ),
    ]
