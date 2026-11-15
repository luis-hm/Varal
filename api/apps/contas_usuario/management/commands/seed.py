import os
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.contas_usuario.models import Usuario
from apps.espacos.models import Espaco, Membro, Papel, Subgrupo
from apps.lancamentos import servicos as contas
from apps.lancamentos.models import Lancamento, Status


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
        pessoas = {}
        for papel in (Papel.MEMBRO, Papel.PAGADOR, Papel.OBSERVADOR):
            pessoas[papel] = pessoa, novo = Usuario.objects.get_or_create(
                username=papel, defaults={"email": f"{papel}@varal.local", "nome": papel.label}
            )
            if novo:
                pessoa.set_password(senha)
                pessoa.save()
            Membro.objects.get_or_create(espaco=grupo, usuario=pessoa, defaults={"papel": papel})
        casas = [
            Subgrupo.objects.get_or_create(espaco=grupo, nome=casa)[0]
            for casa in ("Casa da cidade", "Casa da praia")
        ]
        self.stdout.write(f"group {grupo.nome}: {grupo.membros.count()} members")
        self._contas(user, grupo, casas, {p: u for p, (u, _) in pessoas.items()})

    def _contas(self, user, grupo, casas, pessoas):
        """One bill per state the Etapa 04 screens show; keyed by description (idempotent)."""
        hoje = timezone.localdate()
        mes_passado = hoje.replace(day=1) - timedelta(days=3)

        def conta(espaco, descricao, vencimento, valor, status=None, **campos):
            if Lancamento.objects.filter(espaco=espaco, descricao=descricao).exists():
                return
            dados = {"descricao": descricao, "valor_centavos": valor, "vencimento": vencimento}
            nova = contas.criar(user, espaco, {**dados, **campos})
            if status == Status.CANCELADA:
                contas.cancelar(user, nova.pk)
            elif status:  # aguardando only comes from recurrences (Etapa 08)
                Lancamento.objects.filter(pk=nova.pk).update(status=status)

        pessoal = Espaco.objects.get(dono=user, tipo=Espaco.Tipo.PESSOAL)
        conta(pessoal, "Cartão de crédito", hoje - timedelta(days=4), 125043)
        conta(pessoal, "Internet", hoje + timedelta(days=2), 9990)
        conta(pessoal, "Seguro do carro", hoje + timedelta(days=40), 31000)
        cidade, praia = casas
        restrita = {"visibilidade": "restrita"}
        conta(grupo, "Energia", mes_passado, 28743, subgrupo=cidade.pk, pagador=user.pk)
        conta(grupo, "Água", hoje + timedelta(days=1), 8920, subgrupo=praia.pk)
        conta(grupo, "Condomínio", hoje + timedelta(days=12), 65000, subgrupo=cidade.pk)
        conta(grupo, "IPTU", hoje + timedelta(days=45), 41200, subgrupo=praia.pk)
        conta(grupo, "Gás", hoje + timedelta(days=6), 11000, status=Status.CANCELADA)
        conta(grupo, "Faxina", hoje + timedelta(days=8), 18000, status=Status.AGUARDANDO)
        conta(grupo, "Diarista", hoje + timedelta(days=3), 15000, pagador=pessoas[Papel.PAGADOR].pk)
        conta(
            grupo,
            "Presente da mãe",
            hoje + timedelta(days=9),
            25000,
            acesso=[pessoas[Papel.OBSERVADOR].pk],
            **restrita,
        )
        conta(
            grupo,
            "Remédios",
            hoje + timedelta(days=5),
            7350,
            pagador=pessoas[Papel.PAGADOR].pk,
            acesso=[pessoas[Papel.MEMBRO].pk],
            **restrita,
        )
        self.stdout.write(f"bills: {Lancamento.objects.filter(criador=user).count()}")
