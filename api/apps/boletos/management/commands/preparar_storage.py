from botocore.exceptions import ClientError
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.boletos.storage import cliente


class Command(BaseCommand):
    help = "Create the private PDF bucket if it does not exist."

    def handle(self, *args, **options):
        s3 = cliente()
        try:
            s3.head_bucket(Bucket=settings.S3_BUCKET_NAME)
        except ClientError as exc:
            if exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode") != 404:
                raise
            options = {"Bucket": settings.S3_BUCKET_NAME}
            if settings.S3_REGION_NAME != "us-east-1":
                options["CreateBucketConfiguration"] = {
                    "LocationConstraint": settings.S3_REGION_NAME
                }
            s3.create_bucket(**options)
        s3.put_bucket_acl(Bucket=settings.S3_BUCKET_NAME, ACL="private")
        self.stdout.write("Armazenamento privado preparado.")
