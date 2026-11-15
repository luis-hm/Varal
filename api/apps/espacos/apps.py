import logging
import re

from django.apps import AppConfig

# RN31: the invite token travels in the URL path; keep it out of request logs.
TOKEN_NA_URL = re.compile(r"(/api/convites/|/c/)[^/\s?\"]+")


def sem_token_de_convite(record):
    mensagem = record.getMessage()
    limpa = TOKEN_NA_URL.sub(r"\1[token]", mensagem)
    if limpa != mensagem:
        record.msg, record.args = limpa, ()
    return True


class Config(AppConfig):
    name = "apps.espacos"

    def ready(self):
        from . import servicos  # noqa: F401  registers the RN04 pre_delete guard

        # Logger filters run before any handler, so every sink gets the redacted line.
        for nome in ("django.request", "django.server"):
            logging.getLogger(nome).addFilter(sem_token_de_convite)
