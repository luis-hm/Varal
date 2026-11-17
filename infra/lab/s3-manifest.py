"""Emit a deterministic, private object manifest; caller must encrypt stdout."""
import hashlib
import json
import os

import boto3
from botocore.config import Config

bucket = os.environ["S3_BUCKET_NAME"]
client = boto3.client(
    "s3",
    endpoint_url=os.environ["S3_ENDPOINT_URL"],
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    region_name=os.environ.get("S3_REGION_NAME", "us-east-1"),
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
)
objects = []
for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket):
    for item in page.get("Contents", []):
        key = item["Key"]
        response = client.get_object(Bucket=bucket, Key=key)
        digest = hashlib.sha256()
        size = 0
        stream = response["Body"]
        try:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
                size += len(chunk)
        finally:
            stream.close()
        if size != item["Size"]:
            raise RuntimeError("object size changed during manifest")
        objects.append({"key": key, "size": size, "sha256": digest.hexdigest()})
objects.sort(key=lambda item: item["key"])
print(json.dumps({"version": 1, "bucket": bucket, "objects": objects}, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
