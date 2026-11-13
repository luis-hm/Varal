from pathlib import Path

import yaml
from django.core.management.base import BaseCommand

from config.schema import CombinedSchemaGenerator


class Command(BaseCommand):
    help = "Export and validate the complete DRF + allauth OpenAPI contract."

    def add_arguments(self, parser):
        parser.add_argument("--file", default="openapi.yaml")

    def handle(self, *args, **options):
        schema = CombinedSchemaGenerator().get_schema(public=True)
        Path(options["file"]).write_text(
            yaml.safe_dump(schema, sort_keys=True, allow_unicode=True), encoding="utf-8"
        )
        self.stdout.write(self.style.SUCCESS("Validated DRF + allauth OpenAPI exported."))
