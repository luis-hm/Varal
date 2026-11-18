"""Re-apply account deletions recorded outside the database, after restoring a backup (ADR 0018)."""

import json
import uuid

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.boletos.storage import cliente
from apps.contas_usuario.models import Usuario
from apps.espacos.servicos import ContaRestritaSemQuemVeja, UltimoAdmin
from apps.privacidade.exclusao import PREFIXO, excluir_privilegiado


class Command(BaseCommand):
    help = "Apaga de novo as contas excluídas que voltaram com a restauração do banco."

    def handle(self, *args, **options):
        s3 = cliente()
        donos = set()
        # ponytail: reads every record on each run; fine for a family app's deletion count.
        for pagina in s3.get_paginator("list_objects_v2").paginate(
            Bucket=settings.S3_BUCKET_NAME, Prefix=PREFIXO
        ):
            for objeto in pagina.get("Contents", []):
                corpo = s3.get_object(Bucket=settings.S3_BUCKET_NAME, Key=objeto["Key"])["Body"]
                donos.add(uuid.UUID(json.loads(corpo.read())["owner_id"]))
        bloqueadas = []
        apagadas = 0
        for usuario in Usuario.objects.filter(pk__in=donos):
            try:
                excluir_privilegiado(usuario)
            except (UltimoAdmin, ContaRestritaSemQuemVeja):
                # The same guards as the original deletion; the restored state needs a person.
                bloqueadas.append(str(usuario.pk))
                continue
            apagadas += 1
        self.stdout.write(f"{len(donos)} registros, {apagadas} contas apagadas de novo.")
        if bloqueadas:
            raise CommandError(
                "Bloqueadas pelas regras de grupo; resolva e rode de novo: " + ", ".join(bloqueadas)
            )
