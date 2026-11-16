import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("boletos", "0003_documentoboleto_tentativa")]

    operations = [
        migrations.AddField(
            model_name="limpezapdf",
            name="geracao",
            field=models.PositiveBigIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="limpezapdf",
            name="incerta",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="PinPDF",
            fields=[
                ("reserva_id", models.UUIDField(primary_key=True, serialize=False)),
                ("documento_id", models.UUIDField(db_index=True)),
                ("tamanho", models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name="TentativaCopiaPDF",
            fields=[
                ("id", models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ("reserva_id", models.UUIDField(db_index=True)),
                ("fonte_id", models.UUIDField()),
                ("destino_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("estado", models.CharField(default="ativa", max_length=16)),
                ("tamanho", models.PositiveIntegerField(null=True)),
                ("sha256", models.CharField(blank=True, max_length=64)),
                ("incerta", models.BooleanField(default=True)),
            ],
        ),
    ]
