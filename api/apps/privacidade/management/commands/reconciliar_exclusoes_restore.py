"""Reconcile authenticated journal commits in an isolated restored database."""

import hashlib
import json
import secrets
import uuid
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from apps.privacidade.exclusao import collector_autorizado
from apps.privacidade.journal import JournalIndisponivel, _chave, canonico, ler_fence
from apps.privacidade.models import ExecucaoRestauracao, MarcaRestauracao, RevisaoExportacao
from apps.privacidade.restore import guardas_conjunto, validar_fence, validar_journal, validar_prova
from apps.solicitacoes.coordenacao import barreira


class Command(BaseCommand):
    help = "Reconcile authenticated deletion commits in an isolated restore; never enables traffic."

    def add_arguments(self, parser):
        parser.add_argument("--ancora", required=True)
        parser.add_argument("--isolado", action="store_true")
        parser.add_argument("--prova")
        parser.add_argument("--prova-chave")
        parser.add_argument("--operacao")
        parser.add_argument("--fence")

    def handle(
        self,
        *args,
        ancora,
        isolado=False,
        prova=None,
        prova_chave=None,
        operacao=None,
        fence=None,
        **options,
    ):
        if not settings.VARAL_RESTORE_MODE or not isolado:
            raise CommandError("Restore isolado e VARAL_RESTORE_MODE=1 são obrigatórios.")
        try:
            raw = Path(ancora).read_bytes()
            if len(raw) > 4096:
                raise ValueError
            checkpoint = json.loads(raw)
            if canonico(checkpoint) != raw.strip():
                raise ValueError
            nonce = secrets.token_hex(32)
            selo = validar_fence(ler_fence(nonce), nonce)
            owners, atual = validar_journal(checkpoint, com_checkpoint=True)
            nonce = secrets.token_hex(32)
            posterior = validar_fence(ler_fence(nonce), nonce)
            if (
                selo != posterior
                or selo["seq"] != atual["seq"]
                or selo["record_mac"] != atual["mac"]
            ):
                raise JournalIndisponivel()
            if (
                not all((prova, prova_chave, operacao, fence))
                or str(uuid.UUID(fence)) != selo["fence_id"]
            ):
                raise ValueError
            raw_prova = Path(prova).read_bytes()
            if len(raw_prova) > 16384:
                raise ValueError
            dados = json.loads(raw_prova)
            if canonico(dados) != raw_prova.strip():
                raise ValueError
            validar_prova(dados, _chave(prova_chave), operacao=operacao, fence=selo)
            with connection.cursor() as cursor:
                cursor.execute("SELECT system_identifier::text FROM pg_control_system()")
                identificador = cursor.fetchone()[0]
            if dados["system_identifier"] != identificador:
                raise ValueError
            digest = hashlib.sha256(canonico(dados)).hexdigest()
            with transaction.atomic():
                barreira()
                marker = (
                    MarcaRestauracao.objects.select_for_update()
                    .filter(operation_id=operacao)
                    .first()
                )
                if not marker:
                    raise ValueError
                anterior = ExecucaoRestauracao.objects.filter(operation_id=operacao).first()
                if anterior:
                    if anterior.prova_sha256 != digest:
                        raise ValueError
                else:
                    usuarios = guardas_conjunto(owners)
                    with collector_autorizado():
                        for usuario in usuarios:
                            usuario.delete()
                    RevisaoExportacao.objects.filter(pk=1).update(epoca=uuid.uuid4())
                    ExecucaoRestauracao.objects.create(
                        operation_id=operacao,
                        fence_id=fence,
                        journal_seq=selo["seq"],
                        journal_record_mac=selo["record_mac"],
                        target_lsn=dados["target_lsn"],
                        prova_sha256=digest,
                    )
            nonce = secrets.token_hex(32)
            if validar_fence(ler_fence(nonce), nonce) != selo:
                raise JournalIndisponivel()
        except (OSError, ValueError, TypeError, JournalIndisponivel):
            raise CommandError(
                "Journal ou provas sem validação completa; restore permanece fechado."
            ) from None
        self.stdout.write(
            "Exclusões reconciliadas; restore permanece isolado até o cutover verificado."
        )
