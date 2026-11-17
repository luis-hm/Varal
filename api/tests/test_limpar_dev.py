import pytest
from django.core.management import call_command

from apps.contas_usuario.models import Usuario
from apps.espacos import servicos
from apps.espacos.models import Espaco

pytestmark = pytest.mark.django_db(transaction=True)


def usuario(email, username=None):
    return Usuario.objects.create_user(username=username or email.split("@")[0], email=email)


def test_limpar_dev_apaga_sobras_de_teste_e_preserva_pessoas(monkeypatch):
    monkeypatch.setattr(
        "apps.espacos.management.commands.limpar_dev.verificar_disponibilidade", lambda: None
    )
    dev = usuario("dev@varal.local", "dev")
    ana = usuario("ana@varal.local")
    burst = usuario("burst-1@varal.test")
    e2e = usuario("e2e-abc@varal.test")
    servicos.criar_grupo(ana, "x")
    servicos.criar_grupo(ana, "Teste UI 123")
    servicos.criar_grupo(burst, "Só do burst")  # left without members
    familia = servicos.criar_grupo(dev, "Família")
    servicos.aceitar_convite(e2e, servicos.gerar_convite(dev, familia, "membro")[1])
    servicos.criar_grupo(ana, "Teste UIx")  # no space after "Teste UI": kept

    call_command("limpar_dev", "--sim")

    assert set(Usuario.objects.values_list("email", flat=True)) == {dev.email, ana.email}
    assert set(Espaco.objects.filter(tipo="grupo").values_list("nome", flat=True)) == {
        "Família",
        "Teste UIx",
    }
    assert list(familia.membros.values_list("usuario", flat=True)) == [dev.pk]


def test_limpar_dev_informa_interrupcao_parcial_e_preserva_dev(monkeypatch):
    from django.core.management.base import CommandError

    from apps.privacidade.exclusao import excluir_privilegiado

    monkeypatch.setattr(
        "apps.espacos.management.commands.limpar_dev.verificar_disponibilidade", lambda: None
    )
    dev = usuario("dev@varal.local", "dev")
    a = usuario("burst-a@varal.test")
    b = usuario("e2e-b@varal.test")
    chamadas = []

    def excluir(user, **kwargs):
        chamadas.append(user.pk)
        if len(chamadas) == 2:
            raise RuntimeError("falha simulada")
        return excluir_privilegiado(user, **kwargs)

    monkeypatch.setattr("apps.espacos.management.commands.limpar_dev.excluir_privilegiado", excluir)
    with pytest.raises(CommandError, match="usuários concluídos: 1; usuários ainda presentes: 1"):
        call_command("limpar_dev", "--sim")
    assert Usuario.objects.filter(pk=dev.pk).exists()
    assert Usuario.objects.filter(pk__in=[a.pk, b.pk]).count() == 1
