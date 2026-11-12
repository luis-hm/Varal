import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.contas_usuario.models import Usuario


class Command(BaseCommand):
    help = "Create development data. Idempotent; refuses to run with DEBUG off."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed only runs with DJANGO_DEBUG=1")
        user, created = Usuario.objects.get_or_create(
            username="dev",
            defaults={"email": "dev@varal.local", "is_staff": True, "is_superuser": True},
        )
        if created:
            user.set_password(os.environ.get("SEED_PASSWORD", "varal-dev"))
            user.save()
        self.stdout.write(f"dev user {'created' if created else 'already exists'}: {user.email}")
