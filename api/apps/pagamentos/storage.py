from pathlib import Path

from django.conf import settings
from django.core.files.storage import storages


def chave(pk):
    return f"comprovantes/{pk}"


def spool(pk):
    return Path(settings.PDF_SPOOL_DIR) / "comprovantes" / str(pk)


def armazenamento():
    return storages["comprovantes"]
