import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.contas_usuario.models import Usuario
from apps.espacos.models import Espaco, Membro, Papel, Subgrupo


class Command(BaseCommand):
    help = "Create development data. Idempotent; refuses to run with DEBUG off."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed only runs with DJANGO_DEBUG=1")
        senha = os.environ.get("SEED_PASSWORD", "varal-dev")
        user, created = Usuario.objects.get_or_create(
            username="dev",
            defaults={"email": "dev@varal.local", "is_staff": True, "is_superuser": True},
        )
        if created:
            user.set_password(senha)
            user.save()
        self.stdout.write(f"dev user {'created' if created else 'already exists'}: {user.email}")

        # Group "Família": dev is admin, plus one user per other role and two houses.
        grupo = Espaco.objects.filter(
            tipo=Espaco.Tipo.GRUPO, nome="Família", membros__usuario=user
        ).first() or Espaco.objects.create(tipo=Espaco.Tipo.GRUPO, nome="Família")
        Membro.objects.get_or_create(espaco=grupo, usuario=user, defaults={"papel": Papel.ADMIN})
        for papel in (Papel.MEMBRO, Papel.PAGADOR, Papel.OBSERVADOR):
            pessoa, novo = Usuario.objects.get_or_create(
                username=papel, defaults={"email": f"{papel}@varal.local", "nome": papel.label}
            )
            if novo:
                pessoa.set_password(senha)
                pessoa.save()
            Membro.objects.get_or_create(espaco=grupo, usuario=pessoa, defaults={"papel": papel})
        for casa in ("Casa da cidade", "Casa da praia"):
            Subgrupo.objects.get_or_create(espaco=grupo, nome=casa)
        self.stdout.write(f"group {grupo.nome}: {grupo.membros.count()} members")
