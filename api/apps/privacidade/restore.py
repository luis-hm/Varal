"""Verify the independent deletion journal before touching a restored database."""

import hmac
import re
import uuid

from django.conf import settings

from .journal import JournalIndisponivel, _chave, _mac, canonico, ler_pagina

ZERO = "0" * 64


def _uuid(value):
    return isinstance(value, str) and str(uuid.UUID(value)) == value


def validar_checkpoint(checkpoint):
    campos = {"version", "epoch", "seq", "mac", "checkpoint_key_id", "checkpoint_mac"}
    if not isinstance(checkpoint, dict) or set(checkpoint) != campos:
        raise JournalIndisponivel()
    try:
        if (
            type(checkpoint["version"]) is not int
            or checkpoint["version"] != 1
            or not _uuid(checkpoint["epoch"])
            or checkpoint["epoch"] != str(uuid.UUID(settings.JOURNAL_EPOCH))
            or type(checkpoint["seq"]) is not int
            or checkpoint["seq"] < 0
            or not re.fullmatch(r"[0-9a-f]{64}", checkpoint["mac"])
            or not re.fullmatch(r"[0-9a-f]{64}", checkpoint["checkpoint_mac"])
            or checkpoint["checkpoint_key_id"] != settings.JOURNAL_CHECKPOINT_KEY_ID
        ):
            raise ValueError
        sem_mac = {k: v for k, v in checkpoint.items() if k != "checkpoint_mac"}
        esperado = _mac(
            _chave(settings.JOURNAL_CHECKPOINT_KEY_FILE),
            b"varal-journal-checkpoint-v1\n",
            canonico(sem_mac),
        )
        if not hmac.compare_digest(esperado, checkpoint["checkpoint_mac"]):
            raise ValueError
    except (ValueError, TypeError, KeyError):
        raise JournalIndisponivel() from None
    return checkpoint


def validar_journal(ancora, *, com_checkpoint=False):
    """Read full authenticated chain; unresolved PREPARE always stops recovery."""
    ancora = validar_checkpoint(ancora)
    chave_cadeia = _chave(settings.JOURNAL_CHAIN_KEY_FILE)
    campos = {
        "version",
        "epoch",
        "operation_id",
        "owner_id",
        "kind",
        "fence",
        "prepare_seq",
        "seq",
        "recorded_at",
        "prev_mac",
        "chain_key_id",
        "mac",
    }
    seq, anterior, operacoes = 0, ZERO, {}
    ancora_ok = ancora["seq"] == 0 and ancora["mac"] == ZERO
    checkpoint_atual = None
    while True:
        pagina = ler_pagina(seq)
        checkpoint = validar_checkpoint(pagina["checkpoint"])
        if checkpoint_atual is None:
            checkpoint_atual = checkpoint
        elif checkpoint != checkpoint_atual:
            raise JournalIndisponivel()
        registros = pagina["records"]
        if not isinstance(registros, list) or len(registros) > 500:
            raise JournalIndisponivel()
        for record in registros:
            try:
                if not isinstance(record, dict) or set(record) != campos:
                    raise ValueError
                seq += 1
                if (
                    type(record["version"]) is not int
                    or record["version"] != 1
                    or record["epoch"] != ancora["epoch"]
                    or type(record["seq"]) is not int
                    or record["seq"] != seq
                    or not _uuid(record["operation_id"])
                    or not _uuid(record["owner_id"])
                    or type(record["fence"]) is not int
                    or record["fence"] < 1
                    or record["chain_key_id"] != settings.JOURNAL_CHAIN_KEY_ID
                    or record["prev_mac"] != anterior
                    or not isinstance(record["recorded_at"], str)
                    or not re.fullmatch(r"[0-9a-f]{64}", record["mac"])
                ):
                    raise ValueError
                sem_mac = {k: v for k, v in record.items() if k != "mac"}
                esperado = _mac(chave_cadeia, b"varal-journal-record-v1\n", canonico(sem_mac))
                if not hmac.compare_digest(esperado, record["mac"]):
                    raise ValueError
                anterior = record["mac"]
                if seq == ancora["seq"]:
                    ancora_ok = anterior == ancora["mac"]
                op_id, tipo = record["operation_id"], record["kind"]
                if tipo == "PREPARE":
                    if op_id in operacoes or record["prepare_seq"] is not None:
                        raise ValueError
                    operacoes[op_id] = {
                        "owner": record["owner_id"],
                        "fence": record["fence"],
                        "prepare": seq,
                        "terminal": None,
                    }
                else:
                    op = operacoes.get(op_id)
                    if (
                        tipo not in {"COMMIT", "ABORT"}
                        or not op
                        or op["terminal"]
                        or op["owner"] != record["owner_id"]
                        or op["fence"] != record["fence"]
                        or type(record["prepare_seq"]) is not int
                        or record["prepare_seq"] != op["prepare"]
                    ):
                        raise ValueError
                    op["terminal"] = tipo
                    op["terminal_seq"] = seq
            except (TypeError, ValueError, KeyError):
                raise JournalIndisponivel() from None
        if seq > checkpoint["seq"] or (not registros and seq != checkpoint["seq"]):
            raise JournalIndisponivel()
        if seq == checkpoint["seq"]:
            break
    if not ancora_ok or anterior != checkpoint_atual["mac"]:
        raise JournalIndisponivel()
    if any(op["terminal"] is None for op in operacoes.values()):
        raise JournalIndisponivel()
    owners = {
        op["owner"]
        for op in operacoes.values()
        if op["terminal"] == "COMMIT" and op["terminal_seq"] > ancora["seq"]
    }
    return (owners, checkpoint_atual) if com_checkpoint else owners


def validar_fence(envelope, nonce):
    """Authenticate a fresh sealed receipt; it does not authorize restore alone."""
    campos = {"version", "epoch", "fence_id", "state", "seq", "record_mac", "key_id", "mac"}
    try:
        fence, fresh = envelope["fence"], envelope["freshness"]
        if (
            set(envelope) != {"fence", "freshness"}
            or set(fence) != campos
            or set(fresh) != campos | {"nonce"}
        ):
            raise ValueError
        if (
            type(fence["version"]) is not int
            or fence["version"] != 1
            or not _uuid(fence["epoch"])
            or fence["epoch"] != str(uuid.UUID(settings.JOURNAL_EPOCH))
            or not _uuid(fence["fence_id"])
            or fence["state"] != "sealed"
            or type(fence["seq"]) is not int
            or fence["seq"] < 0
            or not re.fullmatch(r"[0-9a-f]{64}", fence["record_mac"])
            or fence["key_id"] != settings.JOURNAL_RECEIPT_KEY_ID
            or fresh["nonce"] != nonce
            or not re.fullmatch(r"[0-9a-f]{64}", nonce)
            or any(fresh[k] != fence[k] for k in campos - {"mac"})
        ):
            raise ValueError
        key = _chave(settings.JOURNAL_RECEIPT_KEY_FILE)
        for receipt, domain in (
            (fence, b"varal-journal-fence-v1\n"),
            (fresh, b"varal-journal-fence-read-v1\n"),
        ):
            expected = _mac(key, domain, canonico({k: v for k, v in receipt.items() if k != "mac"}))
            if not isinstance(receipt["mac"], str) or not hmac.compare_digest(
                expected, receipt["mac"]
            ):
                raise ValueError
        return fence
    except (KeyError, TypeError, ValueError, AttributeError):
        raise JournalIndisponivel() from None


def guardas_conjunto(owners):
    """Validate all post-checkpoint deletions together; caller holds atomic + B."""
    from django.db import connection

    from apps.contas_usuario.models import Usuario
    from apps.espacos.acesso import quem_ve
    from apps.espacos.models import Membro, Papel
    from apps.espacos.servicos import ContaRestritaSemQuemVeja, UltimoAdmin, _admins_travados
    from apps.lancamentos.models import ABERTOS, Lancamento, Visibilidade

    from .exclusao import guardas

    if not connection.in_atomic_block:
        raise RuntimeError("Restore guard requires an atomic domain barrier")
    alvos = set(Usuario.objects.filter(pk__in=owners).values_list("pk", flat=True))
    grupos = list(Membro.objects.filter(usuario_id__in=alvos).values_list("espaco_id", flat=True))
    _admins_travados(grupos)
    membros = list(Membro.objects.select_for_update().filter(espaco_id__in=grupos).order_by("pk"))
    admins = {}
    for membro in membros:
        if membro.papel == Papel.ADMIN:
            admins.setdefault(membro.espaco_id, set()).add(membro.usuario_id)
    if any(usuarios & alvos and not usuarios - alvos for usuarios in admins.values()):
        raise UltimoAdmin()
    contas = (
        Lancamento.objects.select_for_update()
        .filter(espaco_id__in=grupos, status__in=ABERTOS)
        .select_related("espaco")
        .order_by("pk")
    )
    for conta in contas:
        if conta.visibilidade == Visibilidade.RESTRITA:
            visiveis = quem_ve(conta)
            if visiveis & alvos and not visiveis - alvos:
                raise ContaRestritaSemQuemVeja([], mensagem=ContaRestritaSemQuemVeja.EXCLUIR)
    usuarios = list(Usuario.objects.filter(pk__in=alvos).order_by("pk"))
    for usuario in usuarios:
        guardas(usuario)
    return usuarios


def validar_prova(prova, chave, *, operacao, fence):
    """Authenticate the isolated verifier's attestation and its journal binding."""
    campos = {
        "version",
        "operation_id",
        "snapshot_id",
        "epoch",
        "fence_id",
        "journal_seq",
        "journal_record_mac",
        "system_identifier",
        "timeline",
        "target_lsn",
        "replay_lsn",
        "wal_checkpoint_seq",
        "wal_chain_mac",
        "base_cipher_sha256",
        "objects_cipher_sha256",
        "objects_manifest_sha256",
        "pins_manifest_sha256",
        "key_id",
        "mac",
    }
    try:
        if not isinstance(prova, dict) or set(prova) != campos:
            raise ValueError
        if (
            type(prova["version"]) is not int
            or prova["version"] != 1
            or any(
                not _uuid(prova[k]) for k in ("operation_id", "snapshot_id", "epoch", "fence_id")
            )
            or prova["operation_id"] != str(uuid.UUID(str(operacao)))
            or prova["fence_id"] != str(uuid.UUID(str(fence["fence_id"])))
            or prova["epoch"] != fence["epoch"]
            or prova["journal_seq"] != fence["seq"]
            or prova["journal_record_mac"] != fence["record_mac"]
            or type(prova["journal_seq"]) is not int
            or type(prova["wal_checkpoint_seq"]) is not int
            or prova["wal_checkpoint_seq"] < 1
            or not re.fullmatch(r"[0-9]+", prova["system_identifier"])
            or not re.fullmatch(r"[0-9A-F]{8}", prova["timeline"])
            or prova["key_id"] != "restore-proof-v1"
        ):
            raise ValueError
        for nome in (
            "journal_record_mac",
            "wal_chain_mac",
            "base_cipher_sha256",
            "objects_cipher_sha256",
            "objects_manifest_sha256",
            "pins_manifest_sha256",
            "mac",
        ):
            if not re.fullmatch(r"[0-9a-f]{64}", prova[nome]):
                raise ValueError

        def lsn(value):
            if not re.fullmatch(r"[0-9A-F]{1,8}/[0-9A-F]{1,8}", value):
                raise ValueError
            high, low = value.split("/")
            return (int(high, 16) << 32) | int(low, 16)

        if lsn(prova["replay_lsn"]) < lsn(prova["target_lsn"]):
            raise ValueError
        esperado = _mac(
            chave,
            b"varal-restore-proof-v1\n",
            canonico({k: v for k, v in prova.items() if k != "mac"}),
        )
        if not hmac.compare_digest(esperado, prova["mac"]):
            raise ValueError
        return prova
    except (KeyError, TypeError, ValueError, AttributeError):
        raise JournalIndisponivel() from None
