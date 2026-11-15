import hashlib
import logging
import threading
import time
from datetime import timedelta
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import pytest
from django.apps import apps as registro
from django.contrib import admin
from django.contrib.messages.storage.cookie import CookieStorage
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, RequestFactory
from django.utils import timezone
from rest_framework.exceptions import NotFound

from apps.contas_usuario.models import Usuario
from apps.espacos import servicos
from apps.espacos.acesso import espaco_ou_404, espacos_do_usuario, papel, pode
from apps.espacos.models import Convite, Espaco, Membro, Subgrupo
from tests.test_autenticacao import AUTH, finish_google, google_settings

pytestmark = pytest.mark.django_db
PASSWORD = "Secure-family-pass-726!"
PAPEIS = ["admin", "membro", "pagador", "observador"]


def usuario(email):
    # No password: tests log in with force_login, and skipping the hasher keeps them fast.
    return Usuario.objects.create_user(username=email.split("@")[0], email=email)


def cliente(user=None, **kwargs):
    client = Client(**kwargs)
    if user:
        client.force_login(user)
    return client


@pytest.fixture
def g():
    """Group "Família" with one user per role, one house, and an outsider."""
    u = {nome: usuario(f"{nome}@example.com") for nome in [*PAPEIS, "fora"]}
    grupo = servicos.criar_grupo(u["admin"], "Família", ["Casa da praia"])
    for nome in ("membro", "pagador", "observador"):
        Membro.objects.create(espaco=grupo, usuario=u[nome], papel=nome)
    return SimpleNamespace(
        grupo=grupo,
        casa=grupo.subgrupos.get(),
        u=u,
        m={nome: Membro.objects.get(espaco=grupo, usuario=u[nome]) for nome in PAPEIS},
        url=f"/api/grupos/{grupo.pk}/",
    )


def convite(grupo, papel_="pagador", **campos):
    obj, token = servicos.gerar_convite(None, grupo, papel_)
    if campos:
        Convite.objects.filter(pk=obj.pk).update(**campos)
    return obj, token


def rodar_em_paralelo(*funcoes):
    """Run each callable in its own thread/DB connection; return results or exceptions."""
    resultados = [None] * len(funcoes)
    barreira = threading.Barrier(len(funcoes))

    def alvo(i, funcao):
        try:
            barreira.wait()
            resultados[i] = funcao()
        except Exception as exc:  # noqa: BLE001 - collected for assertions
            resultados[i] = exc
        finally:
            connection.close()

    threads = [threading.Thread(target=alvo, args=(i, f)) for i, f in enumerate(funcoes)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(10)
    return resultados


def lento(funcao, segundos=0.3):
    def wrapper(*args, **kwargs):
        resultado = funcao(*args, **kwargs)
        time.sleep(segundos)
        return resultado

    return wrapper


# ---- CA01 / RF04 ---------------------------------------------------------------------------


def test_rf04_rn04_criar_grupo_criador_unico_admin_e_casas():
    ana = usuario("ana@example.com")
    response = cliente(ana).post(
        "/api/grupos/",
        {"nome": "Família Martins", "casas": ["Praia", "Cidade"]},
        content_type="application/json",
    )
    assert response.status_code == 201, response.content
    body = response.json()
    grupo = Espaco.objects.get(pk=body["id"])
    assert grupo.tipo == "grupo" and grupo.dono is None
    assert list(grupo.membros.values_list("usuario", "papel")) == [(ana.pk, "admin")]
    assert sorted(grupo.subgrupos.values_list("nome", flat=True)) == ["Cidade", "Praia"]
    assert body["meu_papel"] == "admin" and len(body["casas"]) == 2


@pytest.mark.parametrize("payload", [{}, {"nome": ""}, {"nome": "   "}, {"nome": "x" * 151}])
def test_rf04_criar_grupo_nome_invalido_nao_grava(payload):
    response = cliente(usuario("ana@example.com")).post(
        "/api/grupos/", payload, content_type="application/json"
    )
    assert response.status_code == 400
    assert not Espaco.objects.filter(tipo="grupo").exists() and not Membro.objects.exists()


def test_rf04_rn04_criar_grupo_falha_no_meio_nao_grava():
    ana = usuario("ana@example.com")
    with patch.object(Subgrupo.objects, "bulk_create", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError):
            servicos.criar_grupo(ana, "Família", ["Praia"])
    assert not Espaco.objects.filter(tipo="grupo").exists() and not Membro.objects.exists()


def test_rn04_banco_recusa_grupo_com_dono_e_membro_duplicado(g):
    with pytest.raises(IntegrityError), transaction.atomic():
        Espaco.objects.create(tipo="grupo", nome="X", dono=g.u["admin"])
    with pytest.raises(IntegrityError), transaction.atomic():
        Membro.objects.create(espaco=g.grupo, usuario=g.u["membro"], papel="admin")


@pytest.mark.django_db(transaction=True)
def test_rn04_migracao_grupo_com_dono_vira_admin_sem_perder_dados():
    executor = MigrationExecutor(connection)
    final = executor.loader.graph.leaf_nodes()
    antes = [("espacos", "0003_membro_convite_subgrupo")]
    try:
        executor.migrate(antes)
        apps = executor.loader.project_state(antes).apps
        user = apps.get_model("contas_usuario", "Usuario").objects.create(
            username="legado", email="legado@example.com", password="hash"
        )
        EspacoAntigo = apps.get_model("espacos", "Espaco")
        pessoal = EspacoAntigo.objects.create(tipo="pessoal", nome="Pessoal", dono_id=user.pk)
        grupo = EspacoAntigo.objects.create(tipo="grupo", nome="Antigo", dono_id=user.pk)
        MigrationExecutor(connection).migrate(final)
        assert Espaco.objects.get(pk=pessoal.pk).dono_id == user.pk
        assert Espaco.objects.get(pk=grupo.pk).dono_id is None
        assert Membro.objects.get(espaco_id=grupo.pk).papel == "admin"
        migration = import_module("apps.espacos.migrations.0004_grupos_sem_dono")
        with connection.schema_editor() as editor:  # rerun is a no-op
            migration.dono_vira_admin(registro, editor)
        assert Membro.objects.filter(espaco_id=grupo.pk).count() == 1
    finally:
        MigrationExecutor(connection).migrate(final)


# ---- CA02 / RN03 ---------------------------------------------------------------------------


def test_rn03_espaco_pessoal_recusa_convite_pela_api():
    ana = usuario("ana@example.com")
    pessoal = Espaco.objects.get(dono=ana)
    client = cliente(ana)
    response = client.post(
        f"/api/grupos/{pessoal.pk}/convites/", {"papel": "membro"}, content_type="application/json"
    )
    assert response.status_code == 404
    assert client.get(f"/api/grupos/{pessoal.pk}/").status_code == 404
    assert not Convite.objects.exists() and not Membro.objects.exists()


def test_rn03_servico_recusa_convite_e_aceite_no_pessoal():
    ana, bia = usuario("ana@example.com"), usuario("bia@example.com")
    pessoal = Espaco.objects.get(dono=ana)
    with pytest.raises(servicos.Conflito):
        servicos.gerar_convite(ana, pessoal, "membro")
    # A row forged directly in the database still cannot add members to a personal space.
    Convite.objects.create(
        espaco=pessoal,
        papel="membro",
        token_hash=servicos.hash_token("forjado"),
        expira_em=timezone.now() + timedelta(days=1),
    )
    response = cliente(bia).post("/api/convites/forjado/aceitar/")
    assert response.status_code == 410
    assert not Membro.objects.exists()


# ---- CA03 / RN31 ---------------------------------------------------------------------------


def test_rf05_rn24_rn31_link_inteiro_uma_vez_e_banco_so_com_hash(g, caplog, settings):
    caplog.set_level(logging.DEBUG)
    client = cliente(g.u["admin"])
    response = client.post(
        g.url + "convites/", {"papel": "pagador"}, content_type="application/json"
    )
    assert response.status_code == 201, response.content
    body = response.json()
    assert body["url"].startswith(f"{settings.FRONTEND_URL}/c/")
    token = body["url"].rsplit("/", 1)[1]
    assert len(token) == 43  # token_urlsafe(32): 256 bits
    obj = Convite.objects.get(pk=body["id"])
    assert obj.token_hash == hashlib.sha256(token.encode()).hexdigest()
    colunas = Convite.objects.filter(pk=obj.pk).values().get()
    assert all(token not in str(valor) for valor in colunas.values())
    assert abs(obj.expira_em - (obj.criado_em + timedelta(days=7))) < timedelta(seconds=5)
    listagem = client.get(g.url + "convites/")
    assert listagem.status_code == 200 and token not in listagem.content.decode()
    assert [c["id"] for c in listagem.json()] == [str(obj.pk)]
    # 4xx responses are logged with the path by django.request; the token must be redacted.
    assert cliente(g.u["observador"]).post(f"/api/convites/{token}/aceitar/").status_code == 409
    assert "/api/convites/[token]/aceitar/" in caplog.text
    assert token not in caplog.text


def test_rn31_log_do_servidor_sem_token():
    from apps.espacos.apps import sem_token_de_convite

    record = logging.LogRecord(
        "django.server",
        logging.INFO,
        "",
        0,
        '"%s" %s %s',
        ("GET /api/convites/abc_-1/ HTTP/1.1", 410, 9),
        None,
    )
    sem_token_de_convite(record)
    assert record.getMessage() == '"GET /api/convites/[token]/ HTTP/1.1" 410 9'


def test_rn31_admin_django_nao_mostra_token_hash(g):
    obj, _ = convite(g.grupo)
    root = Usuario.objects.create_superuser("root", "root@example.com", None)
    content = cliente(root).get(f"/admin/espacos/convite/{obj.pk}/change/").content.decode()
    assert obj.token_hash not in content


# ---- CA04-CA06 / RF05, RN24 ----------------------------------------------------------------


def test_rf05_link_aberto_sem_sessao_e_aceito_depois_de_entrar(g):
    obj, token = convite(g.grupo, "pagador")
    anonimo = Client()
    response = anonimo.get(f"/api/convites/{token}/")
    assert response.status_code == 200
    assert response.json()["grupo_nome"] == "Família" and response.json()["papel"] == "pagador"
    assert anonimo.post(f"/api/convites/{token}/aceitar/").status_code == 403
    novo = usuario("novo@example.com")
    response = cliente(novo).post(f"/api/convites/{token}/aceitar/")
    assert response.status_code == 201
    assert response.json() == {"grupo_id": str(g.grupo.pk), "papel": "pagador"}
    assert Membro.objects.get(espaco=g.grupo, usuario=novo).papel == "pagador"
    obj.refresh_from_db()
    assert obj.usado_por == novo and obj.usado_em is not None
    assert anonimo.get(f"/api/convites/{token}/").status_code == 410


@pytest.mark.parametrize("estado", ["inexistente", "expirado", "usado", "revogado"])
def test_rn24_rn31_convite_invalido_mesma_resposta_e_nada_muda(g, estado):
    agora = timezone.now()
    campos = {
        "expirado": {"expira_em": agora - timedelta(seconds=1)},
        "usado": {"usado_em": agora, "usado_por": g.u["membro"]},
        "revogado": {"revogado_em": agora},
    }
    if estado == "inexistente":
        token = "nao-existe"
    else:
        _, token = convite(g.grupo, "admin", **campos[estado])
    antes = Membro.objects.count()
    for response in (
        Client().get(f"/api/convites/{token}/"),
        cliente(g.u["fora"]).post(f"/api/convites/{token}/aceitar/"),
    ):
        assert response.status_code == 410
        assert response.json() == {
            "detail": "Este convite não vale mais. Peça um novo a quem convidou."
        }
    assert Membro.objects.count() == antes


@pytest.mark.django_db(transaction=True)
def test_rn24_rn31_dois_aceites_simultaneos_geram_um_membro():
    admin_ = usuario("admin@example.com")
    grupo = servicos.criar_grupo(admin_, "Família")
    _, token = servicos.gerar_convite(admin_, grupo, "membro")
    a, b = usuario("a@example.com"), usuario("b@example.com")
    # Slow insert widens the race window: without the row lock both would get in.
    with patch.object(Membro.objects, "create", lento(Membro.objects.create)):
        resultados = rodar_em_paralelo(
            lambda: servicos.aceitar_convite(a, token), lambda: servicos.aceitar_convite(b, token)
        )
    assert sum(isinstance(r, Membro) for r in resultados) == 1
    assert sum(isinstance(r, servicos.ConviteInvalido) for r in resultados) == 1
    assert Membro.objects.filter(espaco=grupo).count() == 2


def test_rf05_quem_ja_e_membro_nao_muda_papel_nem_consome_convite(g):
    obj, token = convite(g.grupo, "admin")
    response = cliente(g.u["observador"]).post(f"/api/convites/{token}/aceitar/")
    assert response.status_code == 409
    g.m["observador"].refresh_from_db()
    assert g.m["observador"].papel == "observador"
    obj.refresh_from_db()
    assert obj.usado_em is None and obj.usado_por is None
    assert cliente(g.u["fora"]).post(f"/api/convites/{token}/aceitar/").status_code == 201


# ---- CA07 / CA08 / RN31 --------------------------------------------------------------------


def test_rn31_revogar_convite_pendente(g):
    obj, token = convite(g.grupo)
    client = cliente(g.u["admin"])
    assert client.delete(g.url + f"convites/{obj.pk}/").status_code == 204
    assert client.get(g.url + "convites/").json() == []
    assert Client().get(f"/api/convites/{token}/").status_code == 410
    assert client.delete(g.url + f"convites/{obj.pk}/").status_code == 404
    obj.refresh_from_db()
    assert obj.revogado_em is not None  # kept in the database


def test_rn31_revogar_so_vale_para_pendente_usado_da_404_e_membro_fica(g):
    obj, token = convite(g.grupo, "membro")
    assert cliente(g.u["fora"]).post(f"/api/convites/{token}/aceitar/").status_code == 201
    assert cliente(g.u["admin"]).delete(g.url + f"convites/{obj.pk}/").status_code == 404
    obj.refresh_from_db()
    assert obj.revogado_em is None
    assert Membro.objects.get(espaco=g.grupo, usuario=g.u["fora"]).papel == "membro"


@pytest.mark.parametrize("quem", ["membro", "pagador", "observador"])
def test_rn31_revogar_e_listar_convites_sem_ser_admin_403(g, quem):
    obj, _ = convite(g.grupo)
    client = cliente(g.u[quem])
    assert client.get(g.url + "convites/").status_code == 403
    assert client.delete(g.url + f"convites/{obj.pk}/").status_code == 403
    obj.refresh_from_db()
    assert obj.revogado_em is None


def test_rn31_limite_aceite_11a_tentativa_429_por_usuario(g):
    obj, token = convite(g.grupo)
    client = cliente(g.u["fora"])
    for i in range(10):
        assert client.post(f"/api/convites/errado-{i}/aceitar/").status_code == 410
    assert client.post(f"/api/convites/{token}/aceitar/").status_code == 429
    obj.refresh_from_db()
    assert obj.usado_em is None
    assert not Membro.objects.filter(usuario=g.u["fora"]).exists()
    outro = usuario("outro@example.com")  # the counter is per user
    assert cliente(outro).post(f"/api/convites/{token}/aceitar/").status_code == 201


# ---- CA09 / CA10 / CA11 / RN05, RN07 -------------------------------------------------------

TABELA = {  # RN05/RN07 + decision 6, written out independently of acesso.PERMISSOES
    "dono": {
        "ver_grupo",
        "criar_conta",
        "editar_conta",
        "pagar_qualquer",
        "pagar_propria",
        "gerenciar_grupo",
    },
    "admin": {
        "ver_grupo",
        "criar_conta",
        "editar_conta",
        "pagar_qualquer",
        "pagar_propria",
        "gerenciar_grupo",
    },
    "membro": {"ver_grupo", "criar_conta", "editar_conta", "pagar_qualquer", "pagar_propria"},
    "pagador": {"pagar_propria"},
    "observador": {"ver_grupo"},
}
ACOES = [
    "ver_grupo",
    "criar_conta",
    "editar_conta",
    "pagar_qualquer",
    "pagar_propria",
    "gerenciar_grupo",
]


@pytest.mark.parametrize("acao", ACOES)
@pytest.mark.parametrize("papel_", list(TABELA))
def test_rn05_tabela_papel_acao(g, papel_, acao):
    if papel_ == "dono":
        user, espaco = g.u["admin"], Espaco.objects.get(dono=g.u["admin"])
    else:
        user, espaco = g.u[papel_], g.grupo
    assert papel(user, espaco) == papel_
    assert pode(papel_, acao) is (acao in TABELA[papel_])
    if acao in TABELA[papel_]:
        assert espaco_ou_404(user, espaco.pk, acao).pk == espaco.pk
    else:
        with pytest.raises(Exception) as exc:
            espaco_ou_404(user, espaco.pk, acao)
        assert exc.value.status_code == 403


def gestao(g):
    """Every management call as (method, url, payload, check that nothing changed)."""
    obj, _ = convite(g.grupo)
    alvo, casa = g.m["membro"], g.casa
    return {
        "convidar": (
            "post",
            "convites/",
            {"papel": "membro"},
            lambda: Convite.objects.count() == 1,
        ),
        "listar_convites": ("get", "convites/", None, lambda: True),
        "revogar": (
            "delete",
            f"convites/{obj.pk}/",
            None,
            lambda: Convite.objects.get(pk=obj.pk).revogado_em is None,
        ),
        "mudar_papel": (
            "patch",
            f"membros/{alvo.pk}/",
            {"papel": "admin"},
            lambda: Membro.objects.get(pk=alvo.pk).papel == "membro",
        ),
        "remover": (
            "delete",
            f"membros/{alvo.pk}/",
            None,
            lambda: Membro.objects.filter(pk=alvo.pk).exists(),
        ),
        "criar_casa": (
            "post",
            "subgrupos/",
            {"nome": "Nova"},
            lambda: g.grupo.subgrupos.count() == 1,
        ),
        "renomear_casa": (
            "patch",
            f"subgrupos/{casa.pk}/",
            {"nome": "Outra"},
            lambda: Subgrupo.objects.get(pk=casa.pk).nome == "Casa da praia",
        ),
        "arquivar_casa": (
            "patch",
            f"subgrupos/{casa.pk}/",
            {"arquivado": True},
            lambda: not Subgrupo.objects.get(pk=casa.pk).arquivado,
        ),
    }


def chamar(client, g, metodo, caminho, payload):
    url = g.url + caminho
    if payload is None:
        return getattr(client, metodo)(url)
    return getattr(client, metodo)(url, payload, content_type="application/json")


ACOES_GESTAO = [
    "convidar",
    "listar_convites",
    "revogar",
    "mudar_papel",
    "remover",
    "criar_casa",
    "renomear_casa",
    "arquivar_casa",
]


@pytest.mark.parametrize("acao", ACOES_GESTAO)
@pytest.mark.parametrize("quem", ["membro", "pagador", "observador"])
def test_rn05_gestao_negada_a_quem_nao_e_admin(g, quem, acao):
    metodo, caminho, payload, intacto = gestao(g)[acao]
    response = chamar(cliente(g.u[quem]), g, metodo, caminho, payload)
    assert response.status_code == 403
    assert intacto()


@pytest.mark.parametrize("acao", ACOES_GESTAO)
def test_rn05_admin_gerencia(g, acao):
    metodo, caminho, payload, intacto = gestao(g)[acao]
    response = chamar(cliente(g.u["admin"]), g, metodo, caminho, payload)
    assert response.status_code in (200, 201, 204), response.content
    assert acao == "listar_convites" or not intacto()


@pytest.mark.parametrize("quem", PAPEIS)
def test_rn05_rn07_detalhe_grupo_por_papel(g, quem):
    response = cliente(g.u[quem]).get(g.url)
    if quem == "pagador":
        assert response.status_code == 403
        return
    assert response.status_code == 200
    body = response.json()
    assert body["meu_papel"] == quem
    assert {m["email"] for m in body["membros"]} == {f"{p}@example.com" for p in PAPEIS}
    assert [m["sou_eu"] for m in body["membros"] if m["email"] == f"{quem}@example.com"] == [True]
    assert [c["nome"] for c in body["casas"]] == ["Casa da praia"]


# ---- CA12 / CA13 / RN04 --------------------------------------------------------------------


def test_rn04_ultimo_admin_nao_se_rebaixa_remove_nem_sai(g):
    client = cliente(g.u["admin"])
    me = g.m["admin"].pk
    for response in (
        client.patch(
            g.url + f"membros/{me}/", {"papel": "membro"}, content_type="application/json"
        ),
        client.delete(g.url + f"membros/{me}/"),
        client.post(g.url + "sair/"),
    ):
        assert response.status_code == 409
        assert "pelo menos um admin" in response.json()["detail"]
    assert Membro.objects.get(pk=me).papel == "admin"


def test_rn04_com_outro_admin_pode_rebaixar_e_sair(g):
    client = cliente(g.u["admin"])
    url = g.url + f"membros/{g.m['membro'].pk}/"
    assert client.patch(url, {"papel": "admin"}, content_type="application/json").status_code == 200
    me = g.url + f"membros/{g.m['admin'].pk}/"
    response = client.patch(me, {"papel": "observador"}, content_type="application/json")
    assert response.status_code == 200 and response.json()["sou_eu"] is True
    assert cliente(g.u["membro"]).post(g.url + "sair/").status_code == 409  # now the only admin


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("operacao", ["rebaixar_um_ao_outro", "ambos_saem", "ambos_se_removem"])
def test_rn04_concorrencia_dois_admins_sobra_um(operacao):
    a, b = usuario("a@example.com"), usuario("b@example.com")
    grupo = servicos.criar_grupo(a, "Família")
    mb = Membro.objects.create(espaco=grupo, usuario=b, papel="admin")
    ma = Membro.objects.get(espaco=grupo, usuario=a)
    ops = {
        "rebaixar_um_ao_outro": (
            lambda: servicos.alterar_papel(grupo, mb.pk, "membro"),
            lambda: servicos.alterar_papel(grupo, ma.pk, "membro"),
        ),
        "ambos_saem": (lambda: servicos.sair(a, grupo), lambda: servicos.sair(b, grupo)),
        "ambos_se_removem": (
            lambda: servicos.remover_membro(grupo, ma.pk),
            lambda: servicos.remover_membro(grupo, mb.pk),
        ),
    }[operacao]
    # Slow fetch after the admin count widens the race window: without the lock both pass.
    with patch("apps.espacos.servicos.get_object_or_404", lento(servicos.get_object_or_404)):
        resultados = rodar_em_paralelo(*ops)
    assert sum(isinstance(r, servicos.UltimoAdmin) for r in resultados) == 1
    assert Membro.objects.filter(espaco=grupo, papel="admin").count() == 1


def test_rn04_exclusao_usuario_ultimo_admin_orm_e_queryset(g):
    admin_ = g.u["admin"]
    # The Collector's atomic(savepoint=False) would poison the test transaction otherwise.
    with pytest.raises(servicos.UltimoAdmin, match="Família"), transaction.atomic():
        admin_.delete()
    with pytest.raises(servicos.UltimoAdmin), transaction.atomic():
        Usuario.objects.filter(pk=admin_.pk).delete()
    assert Usuario.objects.filter(pk=admin_.pk).exists()
    assert Espaco.objects.filter(dono=admin_).exists()
    assert Membro.objects.filter(usuario=admin_, papel="admin").exists()
    g.u["membro"].delete()  # not an admin: allowed
    servicos.alterar_papel(g.grupo, g.m["observador"].pk, "admin")
    Usuario.objects.filter(pk=admin_.pk).delete()
    assert not Usuario.objects.filter(pk=admin_.pk).exists()
    assert Membro.objects.filter(espaco=g.grupo, papel="admin").count() == 1


def test_rn04_exclusao_usuario_ultimo_admin_admin_django(g):
    admin_ = g.u["admin"]
    root = Usuario.objects.create_superuser("root", "root@example.com", None)
    client = cliente(root)
    url = f"/admin/contas_usuario/usuario/{admin_.pk}/delete/"
    page = client.get(url)
    assert page.status_code == 200 and "único admin do grupo" in page.content.decode()
    assert client.post(url, {"post": "yes"}).status_code == 200
    bulk = client.post(
        "/admin/contas_usuario/usuario/",
        {"action": "delete_selected", "_selected_action": [str(admin_.pk)], "post": "yes"},
    )
    assert bulk.status_code == 200 and "único admin do grupo" in bulk.content.decode()
    assert Usuario.objects.filter(pk=admin_.pk).exists()
    # Race after the confirmation page: the pre_delete guard becomes a message, not a 500.
    request = RequestFactory().post("/")
    request.user = root
    request._messages = CookieStorage(request)
    model_admin = admin.site._registry[Usuario]
    model_admin.delete_queryset(request, Usuario.objects.filter(pk=admin_.pk))
    model_admin.delete_model(request, admin_)
    assert Usuario.objects.filter(pk=admin_.pk).exists()
    assert "único admin" in str(list(request._messages)[0])
    # With another admin the admin deletes the account, cascading its read-only rows.
    servicos.alterar_papel(g.grupo, g.m["membro"].pk, "admin")
    assert client.post(url, {"post": "yes"}).status_code == 302
    assert not Usuario.objects.filter(pk=admin_.pk).exists()


# ---- CA14 / CA15 / RN21, RN01, RN02, RNF01 -------------------------------------------------


def test_rn21_removido_e_quem_sai_perde_acesso_na_hora(g):
    assert cliente(g.u["admin"]).delete(g.url + f"membros/{g.m['membro'].pk}/").status_code == 204
    for quem in ("observador", "pagador"):  # leaving is allowed for every role (Q3)
        assert cliente(g.u[quem]).post(g.url + "sair/").status_code == 204
    for quem in ("membro", "observador", "pagador"):
        client = cliente(g.u[quem])
        assert client.get(g.url).status_code == 404
        assert client.get("/api/me/").json()["grupos"] == []
    assert list(g.grupo.membros.values_list("usuario", flat=True)) == [g.u["admin"].pk]


def rotas_do_grupo(g):
    obj, _ = convite(g.grupo)
    return [
        ("get", "", None),
        ("post", "sair/", None),
        ("get", "convites/", None),
        ("post", "convites/", {"papel": "membro"}),
        ("delete", f"convites/{obj.pk}/", None),
        ("patch", f"membros/{g.m['membro'].pk}/", {"papel": "admin"}),
        ("delete", f"membros/{g.m['membro'].pk}/", None),
        ("post", "subgrupos/", {"nome": "X"}),
        ("patch", f"subgrupos/{g.casa.pk}/", {"arquivado": True}),
    ]


def test_rnf01_rn01_fora_do_grupo_recebe_404_em_todas_as_rotas(g):
    client = cliente(g.u["fora"])
    for metodo, caminho, payload in rotas_do_grupo(g):
        response = chamar(client, g, metodo, caminho, payload)
        assert response.status_code == 404, (metodo, caminho)
    assert g.grupo.membros.count() == 4 and Convite.objects.get().revogado_em is None
    assert not Subgrupo.objects.get(pk=g.casa.pk).arquivado


def test_rnf01_ids_de_outro_grupo_na_url_do_meu_grupo_404(g):
    outro_admin = usuario("outro@example.com")
    outro = servicos.criar_grupo(outro_admin, "Outro", ["Casa alheia"])
    alheio = Membro.objects.create(espaco=outro, usuario=g.u["fora"], papel="membro")
    obj, _ = convite(outro)
    casa = outro.subgrupos.get()
    client = cliente(g.u["admin"])
    for metodo, caminho, payload in [
        ("delete", f"convites/{obj.pk}/", None),
        ("patch", f"membros/{alheio.pk}/", {"papel": "admin"}),
        ("delete", f"membros/{alheio.pk}/", None),
        ("patch", f"subgrupos/{casa.pk}/", {"nome": "Minha"}),
    ]:
        assert chamar(client, g, metodo, caminho, payload).status_code == 404, caminho
    alheio.refresh_from_db()
    casa.refresh_from_db()
    obj.refresh_from_db()
    assert (alheio.papel, casa.nome, obj.revogado_em) == ("membro", "Casa alheia", None)
    assert client.get(f"/api/grupos/{outro.pk}/").status_code == 404


def test_rn02_espaco_pessoal_de_outro_nunca_aparece(g):
    ana = g.u["admin"]
    pessoal_alheio = Espaco.objects.get(dono=g.u["fora"])
    ids = set(espacos_do_usuario(ana).values_list("pk", flat=True))
    assert ids == {Espaco.objects.get(dono=ana).pk, g.grupo.pk}
    with pytest.raises(NotFound):
        espaco_ou_404(ana, pessoal_alheio.pk)
    assert cliente(ana).get(f"/api/grupos/{pessoal_alheio.pk}/").status_code == 404
    assert cliente(g.u["fora"]).get("/api/grupos/").json() == []


# ---- CA16 / CA17 ---------------------------------------------------------------------------


def test_rf07_criar_renomear_arquivar_casa(g):
    client = cliente(g.u["admin"])
    response = client.post(
        g.url + "subgrupos/", {"nome": "Cidade"}, content_type="application/json"
    )
    assert response.status_code == 201
    casa = response.json()["id"]
    url = g.url + f"subgrupos/{casa}/"
    renomeada = client.patch(url, {"nome": "Centro"}, content_type="application/json")
    assert renomeada.json() == {"id": casa, "nome": "Centro", "arquivado": False}
    assert (
        client.patch(url, {"arquivado": True}, content_type="application/json").status_code == 200
    )
    assert [c["nome"] for c in client.get(g.url).json()["casas"]] == ["Casa da praia"]
    assert Subgrupo.objects.get(pk=casa).arquivado is True
    vazio = client.post(g.url + "subgrupos/", {"nome": ""}, content_type="application/json")
    assert vazio.status_code == 400


def test_rf05_me_e_lista_trazem_so_os_grupos_do_usuario(g):
    servicos.criar_grupo(g.u["fora"], "Alheio")
    me = cliente(g.u["pagador"]).get("/api/me/").json()
    assert me["grupos"] == [{"id": str(g.grupo.pk), "nome": "Família", "papel": "pagador"}]
    assert me["espaco_pessoal"]["id"] == str(Espaco.objects.get(dono=g.u["pagador"]).pk)
    lista = cliente(g.u["pagador"]).get("/api/grupos/").json()
    assert lista == [
        {
            "id": str(g.grupo.pk),
            "nome": "Família",
            "papel": "pagador",
            "membros_qtd": None,
            "casas_qtd": None,
        }
    ]
    Subgrupo.objects.create(espaco=g.grupo, nome="Velha", arquivado=True)
    lista = cliente(g.u["observador"]).get("/api/grupos/").json()
    assert (lista[0]["membros_qtd"], lista[0]["casas_qtd"]) == (4, 1)


# ---- RNF02: CSRF and the login return path -------------------------------------------------


def test_rnf02_mutacoes_de_grupo_exigem_csrf(g):
    client = cliente(g.u["admin"], enforce_csrf_checks=True)
    response = client.post("/api/grupos/", {"nome": "X"}, content_type="application/json")
    assert response.status_code == 403
    assert client.post(g.url + "sair/").status_code == 403


def test_rnf02_retorno_google_preserva_proximo_local(settings):
    google_settings(settings)
    client = Client()
    client.get(AUTH + "config")
    callback = "http://localhost:3000/entrar/retorno?proximo=/c/abc"
    response = client.post(
        AUTH + "auth/provider/redirect",
        {
            "provider": "google",
            "process": "login",
            "callback_url": callback,
            "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
        },
        HTTP_HOST="localhost:3000",
    )
    state = parse_qs(urlsplit(response["Location"]).query)["state"][0]
    final = finish_google(client, state)
    assert final.status_code == 302
    assert parse_qs(urlsplit(final["Location"]).query)["proximo"] == ["/c/abc"]
