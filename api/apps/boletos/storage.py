"""Private immutable object storage and staging paths."""

from pathlib import Path

import boto3
from botocore.config import Config
from django.conf import settings
from django.core.files.storage import storages


def cliente(publico=False):
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_PUBLIC_ENDPOINT_URL if publico else settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.S3_REGION_NAME,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            connect_timeout=3,
            read_timeout=15,
            retries={"max_attempts": 1},
        ),
    )


def chave(pk):
    return f"boletos/{pk}.pdf"


def spool(pk):
    return Path(settings.PDF_SPOOL_DIR) / f"{pk}.pdf"


def armazenamento():
    return storages["pdf"]
