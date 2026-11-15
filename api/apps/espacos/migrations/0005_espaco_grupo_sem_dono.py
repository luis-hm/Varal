from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("espacos", "0004_grupos_sem_dono")]
    operations = [
        migrations.AddConstraint(
            model_name="espaco",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("tipo", "grupo"), _negated=True),
                    ("dono__isnull", True),
                    _connector="OR",
                ),
                name="espaco_grupo_sem_dono",
            ),
        ),
    ]
