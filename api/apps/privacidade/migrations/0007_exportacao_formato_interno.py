from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("privacidade", "0006_alter_operacaoexclusao_intencao_id")]

    operations = [
        migrations.AddField(
            model_name="exportacao",
            name="formato_interno",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="exportacao",
            name="artefato_sha256",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="exportacao",
            name="manifestos",
            field=models.JSONField(default=dict),
        ),
    ]
