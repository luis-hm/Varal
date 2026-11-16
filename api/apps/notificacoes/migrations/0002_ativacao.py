from django.db import migrations
from django.utils import timezone


def ativar(apps, schema_editor):
    Controle = apps.get_model('notificacoes', 'ControleNotificacoes')
    Controle.objects.get_or_create(chave='ativacao_09', defaults={'ativado_em': timezone.now()})


class Migration(migrations.Migration):
    dependencies = [('notificacoes', '0001_initial')]
    operations = [migrations.RunPython(ativar, migrations.RunPython.noop)]
