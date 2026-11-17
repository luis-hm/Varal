from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("privacidade", "0007_exportacao_formato_interno")]
    operations = [
        migrations.CreateModel(
            name="MarcaRestauracao",
            fields=[
                ("operation_id", models.UUIDField(primary_key=True, serialize=False)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="ExecucaoRestauracao",
            fields=[
                ("operation_id", models.UUIDField(primary_key=True, serialize=False)),
                ("fence_id", models.UUIDField()),
                ("journal_seq", models.PositiveBigIntegerField()),
                ("journal_record_mac", models.CharField(max_length=64)),
                ("target_lsn", models.CharField(max_length=32)),
                ("prova_sha256", models.CharField(max_length=64)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
