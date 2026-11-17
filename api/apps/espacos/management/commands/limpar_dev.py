from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

from apps.contas_usuario.models import Usuario
from apps.espacos import servicos
from apps.espacos.models import Espaco, Membro
from apps.privacidade.exclusao import excluir_privilegiado
from apps.privacidade.journal import verificar_disponibilidade
from apps.solicitacoes.coordenacao import barreira

USUARIOS_DE_TESTE = (Q(email__startswith="burst-") | Q(email__startswith="e2e-")) & Q(
    email__endswith="@varal.test"
)
GRUPOS_DE_TESTE = Q(nome="x") | Q(nome__startswith="Teste UI ")


class Command(BaseCommand):
    help = (
        "Delete test leftovers from the dev database: group 'x', 'Teste UI ...' groups, "
        "burst-*/e2e-*@varal.test users and groups left without members. DEBUG only."
    )

    def add_arguments(self, parser):
        parser.add_argument("--sim", action="store_true", help="Delete without asking.")

    def handle(self, *args, sim=False, **options):
        if not settings.DEBUG:
            raise CommandError("limpar_dev only runs with DJANGO_DEBUG=1")
        usuarios = Usuario.objects.filter(USUARIOS_DE_TESTE).exclude(username="dev")
        usuarios_ids = list(usuarios.values_list("pk", flat=True))
        usuarios = Usuario.objects.filter(pk__in=usuarios_ids)
        ficam = Usuario.objects.exclude(pk__in=usuarios_ids)
        # Test groups, plus every group that would end up with no member left.
        grupos = Espaco.objects.filter(tipo=Espaco.Tipo.GRUPO).filter(
            GRUPOS_DE_TESTE | ~Q(pk__in=Membro.objects.filter(usuario__in=ficam).values("espaco"))
        )
        grupos_ids = list(grupos.values_list("pk", flat=True))
        grupos = Espaco.objects.filter(pk__in=grupos_ids)

        de_teste = grupos.filter(GRUPOS_DE_TESTE).order_by("nome")
        self._listar("Grupos de teste", [f"{g.nome} ({g.pk})" for g in de_teste], tudo=True)
        sem_membros = grupos.exclude(GRUPOS_DE_TESTE).order_by("nome")
        self._listar("Grupos que ficam sem membros", [g.nome for g in sem_membros])
        for prefixo in ("burst-", "e2e-"):
            emails = usuarios.filter(email__startswith=prefixo).order_by("email")
            self._listar(f"Usuarios {prefixo}*@varal.test", emails.values_list("email", flat=True))
        if not grupos.exists() and not usuarios.exists():
            self.stdout.write("Nada a apagar.")
            return

        self.stdout.write(
            "A limpeza confirma grupos e usuários em etapas; uma falha pode deixá-la parcial."
        )
        if not sim:
            try:
                resposta = input("Apagar? [s/N] ")
            except EOFError:
                resposta = ""
            if resposta.strip().lower() not in ("s", "sim"):
                self.stdout.write("Nada foi apagado.")
                return

        # Freeze the previewed scope. Group removal and each user deletion commit
        # independently because journal I/O cannot be done in a DB transaction.
        concluidos = 0
        grupos_apagados = False
        desligamentos = 0
        try:
            if usuarios_ids:
                verificar_disponibilidade()
            with transaction.atomic():
                barreira()
                atuais = (
                    Usuario.objects.filter(pk__in=usuarios_ids)
                    .filter(USUARIOS_DE_TESTE)
                    .exclude(username="dev")
                )
                if atuais.count() != Usuario.objects.filter(pk__in=usuarios_ids).count():
                    raise CommandError("O escopo de usuários mudou; revise a prévia.")
                ficam_agora = Usuario.objects.exclude(pk__in=atuais.values("pk"))
                permitidos = Espaco.objects.filter(
                    pk__in=grupos_ids, tipo=Espaco.Tipo.GRUPO
                ).filter(
                    GRUPOS_DE_TESTE
                    | ~Q(pk__in=Membro.objects.filter(usuario__in=ficam_agora).values("espaco"))
                )
                if permitidos.count() != Espaco.objects.filter(pk__in=grupos_ids).count():
                    raise CommandError("O escopo de grupos mudou; revise a prévia.")
                permitidos.delete()
            grupos_apagados = bool(grupos_ids)
            for membro in Membro.objects.filter(usuario_id__in=usuarios_ids).select_related(
                "espaco"
            ):
                with transaction.atomic():
                    barreira()
                    if (
                        not Usuario.objects.filter(pk=membro.usuario_id)
                        .filter(USUARIOS_DE_TESTE)
                        .exclude(username="dev")
                        .exists()
                    ):
                        raise CommandError("O escopo de usuários mudou; revise a prévia.")
                    servicos.remover_membro(membro.espaco, membro.pk)
                desligamentos += 1
            for usuario_id in usuarios_ids:
                usuario = (
                    Usuario.objects.filter(pk=usuario_id)
                    .filter(USUARIOS_DE_TESTE)
                    .exclude(username="dev")
                    .first()
                )
                if not usuario and Usuario.objects.filter(pk=usuario_id).exists():
                    raise CommandError("O escopo de usuários mudou; revise a prévia.")
                if usuario:
                    excluir_privilegiado(
                        usuario,
                        elegivel=lambda u: (
                            u.username != "dev"
                            and u.email.endswith("@varal.test")
                            and u.email.startswith(("burst-", "e2e-"))
                        ),
                    )
                concluidos += 1
        except (Exception, KeyboardInterrupt):
            # No exception text, email or token is emitted; report the actual partial state.
            pendentes = Usuario.objects.filter(pk__in=usuarios_ids).count()
            concluidos = len(usuarios_ids) - pendentes
            raise CommandError(
                f"Limpeza interrompida. Grupos planejados removidos: {grupos_apagados}; "
                f"desligamentos confirmados: {desligamentos}; usuários concluídos: {concluidos}; "
                f"usuários ainda presentes: {pendentes}. Revise e execute novamente."
            ) from None
        self.stdout.write(self.style.SUCCESS("Limpeza feita."))

    def _listar(self, titulo, linhas, tudo=False, limite=10):
        linhas = list(linhas)
        self.stdout.write(f"{titulo}: {len(linhas)}")
        for linha in linhas if tudo else linhas[:limite]:
            self.stdout.write(f"  {linha}")
        if not tudo and len(linhas) > limite:
            self.stdout.write(f"  ... e mais {len(linhas) - limite}")
