"""Etapa 04: bills (contas). Rule ids in test names; CA ids in the section headers."""

import time
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.contrib import admin
from django.contrib.messages.storage.cookie import CookieStorage
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import RequestFactory

from apps.contas_usuario.models import Usuario
from apps.espacos import servicos as grupos
from apps.espacos.models import Espaco, Membro, Subgrupo
from apps.lancamentos import servicos as contas
from apps.lancamentos.models import Historico, Lancamento
from tests.test_grupos import PAPEIS, cliente, rodar_em_paralelo, usuario

pytestmark = pytest.mark.django_db
AGORA = datetime(2026, 11, 15, 15, 0, tzinfo=UTC)  # 12:00 in Fortaleza
HOJE = date(2026, 11, 15)
JSON = "application/json"


class Relogio:
    """Frozen at `base`, ticking one microsecond per call so history keeps its order."""

    def __init__(self):
        self.base, self.passos = AGORA, 0

    def __call__(self):
        self.passos += 1
        return self.base + timedelta(microseconds=self.passos)


@pytest.fixture(autouse=True)
def relogio():
    agora = Relogio()
    with patch("django.utils.timezone.now", new=agora):
        yield agora


def dias(n):
    return HOJE + timedelta(days=n)


def pessoa(nome):
    user = usuario(f"{nome}@example.com")
    Usuario.objects.filter(pk=user.pk).update(nome=nome.capitalize())
    user.refresh_from_db()
    return user


@pytest.fixture
def f():
    """Group "Família" (one user per role, one house) plus an outsider."""
    u = {nome: pessoa(nome) for nome in [*PAPEIS, "fora"]}
    grupo = grupos.criar_grupo(u["admin"], "Família", ["Casa da praia"])
    for nome in ("membro", "pagador", "observador"):
        Membro.objects.create(espaco=grupo, usuario=u[nome], papel=nome)
    return SimpleNamespace(
        grupo=grupo,
        casa=grupo.subgrupos.get(),
        u=u,
        m={nome: Membro.objects.get(espaco=grupo, usuario=u[nome]) for nome in PAPEIS},
        pessoal={nome: Espaco.objects.get(dono=u[nome]) for nome in u},
    )


def entrar(f, nome, papel="membro"):
    f.u[nome] = pessoa(nome)
    f.m[nome] = Membro.objects.create(espaco=f.grupo, usuario=f.u[nome], papel=papel)
    return f.u[nome]


def nova(criador, espaco, **campos):
    dados = {"descricao": "Luz", "valor_centavos": 1000, "vencimento": dias(10), **campos}
    return contas.criar(criador, espaco, dados)


def restrita(criador, espaco, acesso=(), **campos):
    return nova(criador, espaco, visibilidade="restrita", acesso=list(acesso), **campos)


def url(conta, sufixo=""):
    return f"/api/lancamentos/{conta.pk}/{sufixo}"


def lista_url(espaco):
    return f"/api/espacos/{espaco.pk}/lancamentos/"


def lista(client, espaco, **params):
    response = client.get(lista_url(espaco), params)
    assert response.status_code == 200, response.content
    return response.json()


def resumo(client, espaco):
    response = client.get(f"/api/espacos/{espaco.pk}/resumo/")
    assert response.status_code == 200, response.content
    return response.json()


def ids(itens):
    return {i["id"] for i in itens}


def historico(conta):
    return list(Historico.objects.filter(lancamento=conta).values_list("acao", flat=True))


def estado(conta):
    conta.refresh_from_db()
    acesso = set(conta.acesso.values_list("pk", flat=True))
    return (conta.status, conta.pagador_id, conta.descricao, acesso, historico(conta))


DADOS = {"descricao": "Água", "valor_centavos": 28743, "vencimento": "2026-11-20"}


# ---- CA01 / CA02 / RF10, RN11 --------------------------------------------------------------


@pytest.mark.parametrize("quem", ["dono", "admin", "membro"])
def test_rf10_criar_conta_nasce_pendente_com_historico(f, quem):
    user = f.u["admin" if quem == "dono" else quem]
    espaco = f.pessoal["admin"] if quem == "dono" else f.grupo
    response = cliente(user).post(lista_url(espaco), DADOS, content_type=JSON)
    assert response.status_code == 201, response.content
    body = response.json()
    conta = Lancamento.objects.get(pk=body["id"])
    assert (conta.status, conta.espaco, conta.criador, conta.valor_centavos) == (
        "pendente",
        espaco,
        user,
        28743,
    )
    assert body["status"] == "pendente" and body["status_exibido"] == "pendente"
    assert body["criador"] == {"nome": user.nome, "sou_eu": True}
    assert [(h["acao"], h["autor"]) for h in body["historico"]] == [("criada", user.nome)]
    assert "categoria" not in body  # ADR 0005
    if quem == "dono":  # decision 6: personal bills are paid and seen by the owner
        assert body["pagador"]["sou_eu"] and body["visibilidade"] == "grupo"


@pytest.mark.parametrize("valor", [0, -1, 10.5, "100", None, True, 2**31])
def test_rn11_valor_invalido_400_e_nada_grava(f, valor):
    client = cliente(f.u["membro"])
    response = client.post(
        lista_url(f.grupo), {**DADOS, "valor_centavos": valor}, content_type=JSON
    )
    assert response.status_code == 400 and "valor_centavos" in response.json()
    sem_valor = {k: v for k, v in DADOS.items() if k != "valor_centavos"}
    assert client.post(lista_url(f.grupo), sem_valor, content_type=JSON).status_code == 400
    assert not Lancamento.objects.exists()
    conta = nova(f.u["membro"], f.grupo)
    assert client.patch(url(conta), {"valor_centavos": valor}, content_type=JSON).status_code == 400
    conta.refresh_from_db()
    assert conta.valor_centavos == 1000 and historico(conta) == ["criada"]


def test_rn11_banco_recusa_valor_nao_positivo(f):
    with pytest.raises(IntegrityError), transaction.atomic():
        Lancamento.objects.create(espaco=f.grupo, descricao="X", valor_centavos=0, vencimento=HOJE)


# ---- CA03 / RN05 ---------------------------------------------------------------------------


@pytest.mark.parametrize("quem", ["dono", *PAPEIS])
def test_rn05_contas_por_papel(f, quem):
    user = f.u["admin" if quem == "dono" else quem]
    espaco = f.pessoal["admin"] if quem == "dono" else f.grupo
    pagador = user.pk if quem in ("admin", "membro", "pagador") else None
    conta = nova(f.u["admin"], espaco, pagador=pagador)
    client = cliente(user)
    assert client.get(url(conta)).status_code == 200
    respostas = [
        client.post(lista_url(espaco), DADOS, content_type=JSON),
        client.patch(url(conta), {"descricao": "Água"}, content_type=JSON),
        client.post(url(conta, "cancelar/")),
    ]
    if quem in ("pagador", "observador"):
        assert [r.status_code for r in respostas] == [403, 403, 403]
        assert Lancamento.objects.count() == 1
        assert estado(conta)[0:3] == ("pendente", pagador, "Luz")
        assert client.get(url(conta)).json()["pode_editar"] is False
    else:
        assert [r.status_code for r in respostas] == [201, 200, 200]
        assert estado(conta)[0] == "cancelada"


# ---- CA04 / RF11 ---------------------------------------------------------------------------


def test_rf11_casa_pagador_e_escolhidos_validados(f):
    outro = grupos.criar_grupo(f.u["fora"], "Outro", ["Casa alheia"])
    arquivada = Subgrupo.objects.create(espaco=f.grupo, nome="Velha", arquivado=True)
    invalidos = [
        {"subgrupo": str(outro.subgrupos.get().pk)},
        {"subgrupo": str(arquivada.pk)},
        {"pagador": str(f.u["fora"].pk)},
        {"pagador": str(f.u["observador"].pk)},
        {"visibilidade": "restrita", "acesso": [str(f.u["fora"].pk)]},
        {"visibilidade": "restrita", "acesso": [str(f.u["pagador"].pk)]},
        {"visibilidade": "secreta"},
    ]
    client = cliente(f.u["membro"])
    for extra in invalidos:
        response = client.post(lista_url(f.grupo), {**DADOS, **extra}, content_type=JSON)
        assert response.status_code == 400, extra
    assert not Lancamento.objects.exists()
    validos = {
        "subgrupo": str(f.casa.pk),
        "pagador": str(f.u["pagador"].pk),
        "visibilidade": "restrita",
        "acesso": [str(f.u["observador"].pk), str(f.u["admin"].pk)],
        "categoria": "ignorada",
    }
    response = client.post(lista_url(f.grupo), {**DADOS, **validos}, content_type=JSON)
    assert response.status_code == 201, response.content
    assert "categoria" not in response.json()
    # Q20: a bill whose house was archived keeps it (and its name) on unrelated edits.
    conta = Lancamento.objects.get()
    Subgrupo.objects.filter(pk=f.casa.pk).update(arquivado=True)
    response = client.patch(
        url(conta), {"descricao": "Gás", "subgrupo": str(f.casa.pk)}, content_type=JSON
    )
    assert response.status_code == 200 and response.json()["subgrupo"]["nome"] == "Casa da praia"


# ---- CA05 / CA06 / RN01, RN02, RNF01 -------------------------------------------------------


def test_rn02_conta_pessoal_so_o_dono_ve(f):
    conta = nova(f.u["membro"], f.pessoal["membro"])
    for quem in ("admin", "observador", "fora"):
        client = cliente(f.u[quem])
        assert client.get(url(conta)).status_code == 404
        assert client.patch(url(conta), {"descricao": "X"}, content_type=JSON).status_code == 404
        assert client.post(url(conta, "cancelar/")).status_code == 404
        assert client.get(lista_url(f.pessoal["membro"])).status_code == 404
        assert str(conta.pk) not in ids(lista(client, f.pessoal[quem])["itens"])
        assert resumo(client, f.pessoal[quem])["total_centavos"] == 0
    assert estado(conta)[0:3] == ("pendente", f.u["membro"].pk, "Luz")
    assert lista(cliente(f.u["membro"]), f.pessoal["membro"])["total_centavos"] == 1000


def test_rn01_rnf01_conta_de_outro_grupo_404_e_so_no_proprio_espaco(f):
    conta = nova(f.u["admin"], f.grupo)
    client = cliente(f.u["fora"])
    assert client.get(url(conta)).status_code == 404
    assert client.patch(url(conta), {"descricao": "X"}, content_type=JSON).status_code == 404
    assert client.post(url(conta, "cancelar/")).status_code == 404
    assert client.get(lista_url(f.grupo)).status_code == 404
    assert client.get(f"/api/espacos/{f.grupo.pk}/resumo/").status_code == 404
    assert client.post(lista_url(f.grupo), DADOS, content_type=JSON).status_code == 404
    # A member of both groups sees the bill only in its own space.
    outro = grupos.criar_grupo(f.u["membro"], "Outro")
    membro = cliente(f.u["membro"])
    assert str(conta.pk) not in ids(lista(membro, outro)["itens"])
    assert str(conta.pk) not in ids(lista(membro, f.pessoal["membro"])["itens"])
    assert str(conta.pk) in ids(lista(membro, f.grupo)["itens"])
    assert estado(conta)[2] == "Luz"


# ---- CA07 / CA08 / CA09 / RN06, RN07, ADR 0008 ---------------------------------------------


def consultas(client, f, *extra):
    """Everything a user can read about the group's bills, as plain JSON."""
    alvo = [lista_url(f.grupo)]
    for status in ("todas", "a_pagar", "vencidas", "pagas", "canceladas"):
        alvo.append(f"{lista_url(f.grupo)}?status={status}")
    for mes in ("2026-10", "2026-12"):
        alvo.append(f"{lista_url(f.grupo)}?mes={mes}")
    alvo += [
        f"{lista_url(f.grupo)}?subgrupo={f.casa.pk}",
        f"{lista_url(f.grupo)}?pagador=nenhum",
        f"{lista_url(f.grupo)}?pagador={f.u['membro'].pk}",
        f"/api/espacos/{f.grupo.pk}/resumo/",
        *extra,
    ]
    respostas = [client.get(u) for u in alvo]
    return [(r.status_code, r.json()) for r in respostas]


def test_rn06_admin_nao_escolhido_404_e_agregados_sem_a_conta(f):
    visivel = nova(f.u["membro"], f.grupo, subgrupo=f.casa.pk, pagador=f.u["membro"].pk)
    nova(f.u["membro"], f.grupo, vencimento=dias(-40))
    entrar(f, "outro")  # CA07: admin, member and observer, none of them chosen
    nao_escolhidos = {q: cliente(f.u[q]) for q in ("admin", "outro", "observador")}
    antes = {q: consultas(c, f, url(visivel)) for q, c in nao_escolhidos.items()}
    escondidas = [
        restrita(
            f.u["membro"],
            f.grupo,
            subgrupo=f.casa.pk,
            pagador=f.u["membro"].pk,
            vencimento=venc,
            descricao="Segredo",
        )
        for venc in (dias(1), dias(-3), dias(-40), dias(20), dias(40))
    ]
    contas.cancelar(f.u["membro"], escondidas[-1].pk)
    Lancamento.objects.filter(pk=escondidas[3].pk).update(status="paga")
    escolhida = restrita(f.u["membro"], f.grupo, acesso=[f.u["observador"].pk])
    for q, client in nao_escolhidos.items():
        depois = consultas(client, f, url(visivel))
        if q != "observador":  # the observer is chosen in `escolhida` below
            assert depois == antes[q]
        for conta in escondidas:
            assert client.get(url(conta)).status_code == 404
            patch_ = client.patch(url(conta), {"descricao": "X"}, content_type=JSON)
            assert patch_.status_code == 404  # never 403: existence is not revealed
            assert client.post(url(conta, "cancelar/")).status_code == 404
    assert cliente(f.u["observador"]).get(url(escolhida)).status_code == 200
    assert cliente(f.u["admin"]).get(url(escolhida)).status_code == 404
    criador = lista(cliente(f.u["membro"]), f.grupo, status="todas")
    assert {str(c.pk) for c in escondidas[:2]} <= ids(criador["itens"])
    assert estado(escondidas[0])[2] == "Segredo"


@pytest.mark.parametrize("quem", ["membro", "pagador"])
def test_rn06_pagador_nao_escolhido_ve_a_conta(f, quem):
    conta = restrita(f.u["admin"], f.grupo, acesso=[f.u["observador"].pk], pagador=f.u[quem].pk)
    client = cliente(f.u[quem])
    assert client.get(url(conta)).status_code == 200
    assert str(conta.pk) in ids(lista(client, f.grupo)["itens"])
    assert lista(client, f.grupo)["total_centavos"] == 1000
    assert resumo(client, f.grupo)["total_centavos"] == 1000


def test_rn07_pagador_so_ve_as_contas_dele(f):
    dele = nova(f.u["admin"], f.grupo, pagador=f.u["pagador"].pk, descricao="Dele")
    outras = [
        nova(f.u["admin"], f.grupo, pagador=f.u["membro"].pk),
        nova(f.u["admin"], f.grupo),
        restrita(f.u["admin"], f.grupo, acesso=[f.u["observador"].pk]),
    ]
    client = cliente(f.u["pagador"])
    assert ids(lista(client, f.grupo)["itens"]) == {str(dele.pk)}
    corpo = resumo(client, f.grupo)
    assert corpo["total_centavos"] == 1000 and corpo["qtd"] == 1
    for conta in outras:
        assert client.get(url(conta)).status_code == 404
    assert client.get(url(dele)).json()["pode_editar"] is False  # Q5: no Editar


def test_rn06_rn07_acesso_explicito_prevalece(f):
    conta = restrita(f.u["admin"], f.grupo, acesso=[f.u["observador"].pk])
    de_grupo = nova(f.u["admin"], f.grupo)
    admin = cliente(f.u["admin"])
    response = admin.patch(
        f"/api/grupos/{f.grupo.pk}/membros/{f.m['observador'].pk}/",
        {"papel": "pagador"},
        content_type=JSON,
    )
    assert response.status_code == 200
    client = cliente(f.u["observador"])
    assert client.get(url(conta)).status_code == 200  # still in "Quem vê"
    assert client.get(url(de_grupo)).status_code == 404  # RN07 for the rest
    assert ids(lista(client, f.grupo)["itens"]) == {str(conta.pk)}
    # Kept chosen people stay valid on edits (decision 7), new payers-by-role do not.
    edicao = {"descricao": "Luz 2", "acesso": [str(f.u["observador"].pk)]}
    assert admin.patch(url(conta), edicao, content_type=JSON).status_code == 200
    novo = {"acesso": [str(f.u["observador"].pk), str(f.u["pagador"].pk)]}
    assert admin.patch(url(conta), novo, content_type=JSON).status_code == 400


# ---- CA10 / CA11 / RN12, RN13, RNF11 -------------------------------------------------------


@pytest.mark.parametrize(
    "delta,esperado", [(4, "pendente"), (3, "vence"), (0, "vence"), (-1, "vencida")]
)
def test_rn12_status_calculado_com_janela_3(f, delta, esperado):
    conta = nova(f.u["admin"], f.grupo, vencimento=dias(delta))
    body = cliente(f.u["admin"]).get(url(conta)).json()
    assert (body["status"], body["status_exibido"], body["dias_para_vencer"]) == (
        "pendente",
        esperado,
        delta,
    )
    assert Lancamento.objects.get(pk=conta.pk).status == "pendente"  # never stored


def test_rn12_so_pendente_vira_vence_ou_vencida(f):
    conta = nova(f.u["admin"], f.grupo, vencimento=dias(-5))
    for status in ("aguardando", "paga", "confirmada", "cancelada"):
        Lancamento.objects.filter(pk=conta.pk).update(status=status)
        assert cliente(f.u["admin"]).get(url(conta)).json()["status_exibido"] == status


def test_rnf11_hoje_em_fortaleza(f, relogio):
    conta = nova(f.u["admin"], f.grupo, vencimento=HOJE)
    client = cliente(f.u["admin"])
    relogio.base = datetime(2026, 11, 16, 2, 30, tzinfo=UTC)  # 23:30 on the 15th
    assert client.get(url(conta)).json()["status_exibido"] == "vence"
    relogio.base = datetime(2026, 11, 16, 3, 30, tzinfo=UTC)  # 00:30 on the 16th
    assert client.get(url(conta)).json()["status_exibido"] == "vencida"


def test_rn13_janela_editavel_so_pelo_admin(f):
    conta = nova(f.u["admin"], f.grupo, vencimento=dias(5))
    grupo_url = f"/api/grupos/{f.grupo.pk}/"
    admin = cliente(f.u["admin"])
    assert admin.get(url(conta)).json()["status_exibido"] == "pendente"
    response = admin.patch(grupo_url, {"janela_alerta_dias": 5}, content_type=JSON)
    assert response.status_code == 200 and response.json()["janela_alerta_dias"] == 5
    assert admin.get(url(conta)).json()["status_exibido"] == "vence"
    assert resumo(admin, f.grupo)["janela_alerta_dias"] == 5
    for valor in (0, 8, "x", None):
        bad = admin.patch(grupo_url, {"janela_alerta_dias": valor}, content_type=JSON)
        assert bad.status_code == 400
    for quem in ("membro", "pagador", "observador"):
        response = cliente(f.u[quem]).patch(grupo_url, {"janela_alerta_dias": 2}, content_type=JSON)
        assert response.status_code == 403
    pessoal = f.pessoal["admin"]
    response = admin.patch(
        f"/api/grupos/{pessoal.pk}/", {"janela_alerta_dias": 7}, content_type=JSON
    )
    assert response.status_code == 404
    pessoal.refresh_from_db()
    f.grupo.refresh_from_db()
    assert (pessoal.janela_alerta_dias, f.grupo.janela_alerta_dias) == (3, 5)
    with pytest.raises(IntegrityError), transaction.atomic():
        Espaco.objects.filter(pk=f.grupo.pk).update(janela_alerta_dias=8)


@pytest.mark.django_db(transaction=True)
def test_rn13_migracao_janela_fora_do_intervalo_e_ajustada_sem_perda():
    executor = MigrationExecutor(connection)
    final = executor.loader.graph.leaf_nodes()
    antes = [("espacos", "0005_espaco_grupo_sem_dono")]
    try:
        executor.migrate(antes)
        apps = executor.loader.project_state(antes).apps
        EspacoAntigo = apps.get_model("espacos", "Espaco")
        grupo = EspacoAntigo.objects.create(tipo="grupo", nome="Antigo", janela_alerta_dias=9)
        MigrationExecutor(connection).migrate(final)
        assert Espaco.objects.get(pk=grupo.pk).janela_alerta_dias == 7
    finally:
        MigrationExecutor(connection).migrate(final)


# ---- CA12 / CA13 / CA14 / RN22, D2 ---------------------------------------------------------


def test_rn22_edicao_registra_autor_e_so_o_que_mudou(f):
    conta = nova(f.u["admin"], f.grupo)
    client = cliente(f.u["membro"])
    mudanca = {
        "descricao": "Luz",
        "valor_centavos": 2000,
        "vencimento": "2026-11-30",
        "subgrupo": str(f.casa.pk),
        "pagador": str(f.u["pagador"].pk),
        "visibilidade": "restrita",
        "acesso": [str(f.u["observador"].pk), str(f.u["membro"].pk)],
        "espaco": str(f.pessoal["membro"].pk),
    }
    response = client.patch(url(conta), mudanca, content_type=JSON)
    assert response.status_code == 200, response.content
    ultimo = response.json()["historico"][-1]
    assert (ultimo["acao"], ultimo["autor"], ultimo["sou_eu"]) == ("editada", "Membro", True)
    assert ultimo["dados"] == {
        "valor_centavos": [1000, 2000],
        "vencimento": ["2026-11-25", "2026-11-30"],
        "subgrupo": [None, "Casa da praia"],
        "pagador": [None, "Pagador"],
        "visibilidade": ["grupo", "restrita"],
        "acesso": [[], ["Membro", "Observador"]],
    }
    conta.refresh_from_db()
    assert conta.espaco == f.grupo  # the space never changes
    assert client.patch(url(conta), mudanca, content_type=JSON).status_code == 200
    assert historico(conta) == ["criada", "editada"]  # nothing changed, nothing logged


def test_rn22_cancelar_nao_apaga_e_so_aberta(f):
    conta = nova(f.u["admin"], f.grupo)
    client = cliente(f.u["membro"])
    response = client.post(url(conta, "cancelar/"))
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "cancelada" and body["pode_editar"] is False
    assert [(h["acao"], h["autor"]) for h in body["historico"]] == [
        ("criada", "Admin"),
        ("cancelada", "Membro"),
    ]
    assert Lancamento.objects.filter(pk=conta.pk, status="cancelada").exists()
    assert client.patch(url(conta), {"descricao": "X"}, content_type=JSON).status_code == 409
    assert client.post(url(conta, "cancelar/")).status_code == 409
    for status in ("paga", "confirmada"):
        outra = nova(f.u["admin"], f.grupo)
        Lancamento.objects.filter(pk=outra.pk).update(status=status)
        assert client.post(url(outra, "cancelar/")).status_code == 409
        assert Lancamento.objects.get(pk=outra.pk).status == status
    assert historico(conta) == ["criada", "cancelada"]


def test_d2_cancelada_fora_de_tudo_menos_do_filtro_canceladas(f):
    viva = nova(f.u["admin"], f.grupo, subgrupo=f.casa.pk, vencimento=dias(1))
    morta = nova(f.u["admin"], f.grupo, subgrupo=f.casa.pk, vencimento=dias(-1), valor_centavos=5)
    contas.cancelar(f.u["admin"], morta.pk)
    client = cliente(f.u["membro"])
    todas = lista(client, f.grupo)
    assert ids(todas["itens"]) == {str(viva.pk)} and todas["total_centavos"] == 1000
    assert todas["contagens"] == {
        "todas": 1,
        "a_pagar": 1,
        "vencidas": 0,
        "pagas": 0,
        "canceladas": 1,
    }
    assert ids(lista(client, f.grupo, status="a_pagar")["itens"]) == {str(viva.pk)}
    canceladas = lista(client, f.grupo, status="canceladas")["itens"]
    assert [(c["id"], c["status"]) for c in canceladas] == [(str(morta.pk), "cancelada")]
    corpo = resumo(client, f.grupo)
    assert (corpo["total_centavos"], corpo["qtd"], corpo["vencidas_qtd"]) == (1000, 1, 0)
    assert ids(corpo["atencao"]) == {str(viva.pk)}
    assert corpo["por_casa"] == [
        {"id": str(f.casa.pk), "nome": "Casa da praia", "total_centavos": 1000, "qtd": 1}
    ]


# ---- CA15 / CA16 / RF13 --------------------------------------------------------------------


def test_rf13_filtros_mes_status_casa_pagador_e_contagens(f):
    a, m = f.u["admin"], f.u["membro"].pk
    casa = nova(a, f.grupo, subgrupo=f.casa.pk, pagador=m, valor_centavos=1000)
    solta = nova(a, f.grupo, valor_centavos=2000)
    vencida = nova(a, f.grupo, vencimento=dias(-2), valor_centavos=500, pagador=m)
    paga = nova(a, f.grupo, valor_centavos=300)
    Lancamento.objects.filter(pk=paga.pk).update(status="paga")
    contas.cancelar(a, nova(a, f.grupo, valor_centavos=700).pk)
    dezembro = nova(a, f.grupo, vencimento=date(2026, 12, 5), valor_centavos=4000)
    nova(a, f.grupo, vencimento=date(2026, 10, 5), valor_centavos=800)
    client = cliente(f.u["observador"])
    novembro = lista(client, f.grupo)
    assert novembro["mes"] == "2026-11" and novembro["total_centavos"] == 3800
    assert novembro["contagens"] == {
        "todas": 4,
        "a_pagar": 3,
        "vencidas": 1,
        "pagas": 1,
        "canceladas": 1,
    }
    assert [i["id"] for i in novembro["itens"]] == [
        str(vencida.pk),
        str(casa.pk),
        str(solta.pk),
        str(paga.pk),
    ]
    assert novembro["opcoes"]["casas"] == [{"id": str(f.casa.pk), "nome": "Casa da praia"}]
    assert [p["nome"] for p in novembro["opcoes"]["pagadores"]] == ["Membro"]
    assert novembro["opcoes"]["sem_pagador"] is True
    assert ids(lista(client, f.grupo, status="vencidas")["itens"]) == {str(vencida.pk)}
    assert ids(lista(client, f.grupo, status="pagas")["itens"]) == {str(paga.pk)}
    dez = lista(client, f.grupo, mes="2026-12")
    assert ids(dez["itens"]) == {str(dezembro.pk)} and dez["total_centavos"] == 4000
    por_casa = lista(client, f.grupo, subgrupo=str(f.casa.pk))
    assert ids(por_casa["itens"]) == {str(casa.pk)} and por_casa["contagens"]["todas"] == 1
    sem = lista(client, f.grupo, pagador="nenhum")
    assert ids(sem["itens"]) == {str(solta.pk), str(paga.pk)}
    do_membro = lista(client, f.grupo, pagador=str(m), status="a_pagar")
    assert ids(do_membro["itens"]) == {str(casa.pk), str(vencida.pk)}
    assert do_membro["total_centavos"] == 1500
    for params in ({"mes": "2026-13"}, {"mes": "nov"}, {"status": "x"}, {"subgrupo": "x"}):
        assert client.get(lista_url(f.grupo), params).status_code == 400


def test_rf13_resumo_total_do_mes_atencao_e_por_casa(f):
    a = f.u["admin"]
    outubro = nova(a, f.grupo, vencimento=date(2026, 10, 28), descricao="Outubro")
    vence = nova(a, f.grupo, vencimento=dias(2), subgrupo=f.casa.pk, valor_centavos=200)
    nova(a, f.grupo, vencimento=dias(10), valor_centavos=300)
    nova(a, f.grupo, vencimento=date(2026, 12, 1), valor_centavos=9999)
    corpo = resumo(cliente(f.u["observador"]), f.grupo)
    assert corpo["mes"] == "2026-11" and corpo["janela_alerta_dias"] == 3
    assert (corpo["total_centavos"], corpo["qtd"]) == (500, 2)
    assert [c["id"] for c in corpo["atencao"]] == [str(outubro.pk), str(vence.pk)]
    assert [c["status_exibido"] for c in corpo["atencao"]] == ["vencida", "vence"]
    assert (corpo["vencidas_qtd"], corpo["vence_qtd"]) == (1, 1)
    assert corpo["por_casa"] == [
        {"id": str(f.casa.pk), "nome": "Casa da praia", "total_centavos": 200, "qtd": 1}
    ]
    assert "pagas_qtd" not in corpo  # Q23
    nova(a, f.pessoal["admin"])
    assert resumo(cliente(a), f.pessoal["admin"])["por_casa"] == []


# ---- CA18 / RN21 ---------------------------------------------------------------------------


@pytest.mark.parametrize("saida", ["sair", "remover"])
def test_rn21_abertas_perdem_pagador_pagas_mantem_e_criadas_ficam(f, saida):
    a, m = f.u["admin"], f.u["membro"]
    aberta = nova(a, f.grupo, pagador=m.pk)
    paga = nova(a, f.grupo, pagador=m.pk)
    Lancamento.objects.filter(pk=paga.pk).update(status="paga")
    criada = nova(m, f.grupo)
    escolhido = restrita(a, f.grupo, acesso=[m.pk, f.u["observador"].pk])
    if saida == "sair":
        assert cliente(m).post(f"/api/grupos/{f.grupo.pk}/sair/").status_code == 204
    else:
        response = cliente(a).delete(f"/api/grupos/{f.grupo.pk}/membros/{f.m['membro'].pk}/")
        assert response.status_code == 204
    aberta.refresh_from_db()
    paga.refresh_from_db()
    assert aberta.pagador is None and paga.pagador == m
    assert historico(aberta) == ["criada", "pagador_removido"]
    automatico = Historico.objects.get(lancamento=aberta, acao="pagador_removido")
    assert automatico.usuario is None and automatico.dados == {"pagador": ["Membro", None]}
    assert historico(paga) == ["criada"]
    assert Lancamento.objects.get(pk=criada.pk).espaco == f.grupo
    assert set(escolhido.acesso.values_list("pk", flat=True)) == {f.u["observador"].pk}
    assert historico(escolhido) == ["criada", "acesso_removido"]
    admin = cliente(a)
    body = admin.get(url(aberta)).json()
    assert body["pagador"] is None
    assert (body["historico"][-1]["autor"], body["historico"][-1]["automatica"]) == (None, True)
    assert admin.get(url(criada)).json()["criador"]["nome"] == "Membro"
    for conta in (aberta, criada, escolhido):
        assert cliente(m).get(url(conta)).status_code == 404


# ---- CA19 / RN32: the person acts ----------------------------------------------------------


def sair(user, f, resolucoes=None):
    corpo = {} if resolucoes is None else {"resolucoes": resolucoes}
    return cliente(user).post(f"/api/grupos/{f.grupo.pk}/sair/", corpo, content_type=JSON)


def test_rn32_sair_bloqueado_lista_contas_e_nada_muda(f):
    m = f.u["membro"]
    orfa = restrita(m, f.grupo, descricao="Presente", pagador=m.pk)
    paga = restrita(m, f.grupo, descricao="Paga")
    Lancamento.objects.filter(pk=paga.pk).update(status="paga")
    confirmada = restrita(m, f.grupo, descricao="Confirmada")
    Lancamento.objects.filter(pk=confirmada.pk).update(status="confirmada")
    contas.cancelar(m, restrita(m, f.grupo, descricao="Cancelada").pk)
    antes = estado(orfa)
    response = sair(m, f)
    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "conta_restrita_orfa" and "escolha outra pessoa" in body["detail"]
    assert body["contas"] == [{"id": str(orfa.pk), "descricao": "Presente"}]
    assert body["pessoas"] == [
        {"id": str(f.u["admin"].pk), "nome": "Admin"},
        {"id": str(f.u["observador"].pk), "nome": "Observador"},
    ]  # the payer-by-role cannot be chosen; names only, never e-mail
    assert "@" not in response.content.decode()
    assert Membro.objects.filter(pk=f.m["membro"].pk).exists()
    assert estado(orfa) == antes
    # After choosing someone else to see it, leaving goes through.
    edicao = {"acesso": [str(f.u["observador"].pk)]}
    assert cliente(m).patch(url(orfa), edicao, content_type=JSON).status_code == 200
    assert sair(m, f).status_code == 204


def test_rn32_sair_pagador_quando_o_criador_ja_saiu(f):
    conta = restrita(f.u["membro"], f.grupo, pagador=f.u["pagador"].pk)
    assert sair(f.u["membro"], f).status_code == 204  # the payer still sees it
    response = sair(f.u["pagador"], f)
    assert response.status_code == 409
    assert response.json()["contas"] == [{"id": str(conta.pk), "descricao": "Luz"}]
    assert Lancamento.objects.get(pk=conta.pk).pagador == f.u["pagador"]


def test_rn32_exclusao_usuario_orm_e_queryset_bloqueada(f):
    m = f.u["membro"]
    orfa = restrita(m, f.grupo)
    antes = estado(orfa)
    with pytest.raises(grupos.ContaRestritaSemQuemVeja), transaction.atomic():
        m.delete()
    with pytest.raises(grupos.ContaRestritaSemQuemVeja), transaction.atomic():
        Usuario.objects.filter(pk=m.pk).delete()
    assert Usuario.objects.filter(pk=m.pk).exists() and estado(orfa) == antes
    contas.cancelar(m, orfa.pk)  # closed bills do not block
    Usuario.objects.filter(pk=m.pk).delete()
    orfa.refresh_from_db()
    assert orfa.criador is None and orfa.espaco == f.grupo


def test_rn32_exclusao_usuario_admin_django(f):
    m = f.u["membro"]
    orfa = restrita(m, f.grupo, descricao="Presente")
    root = Usuario.objects.create_superuser("root", "root@example.com", None)
    client = cliente(root)
    pagina = f"/admin/contas_usuario/usuario/{m.pk}/delete/"
    response = client.get(pagina)
    assert (
        response.status_code == 200 and "única pessoa que vê a conta" in response.content.decode()
    )
    assert client.post(pagina, {"post": "yes"}).status_code == 200
    assert Usuario.objects.filter(pk=m.pk).exists()
    request = RequestFactory().post("/")
    request.user = root
    request._messages = CookieStorage(request)
    model_admin = admin.site._registry[Usuario]
    model_admin.delete_model(request, m)  # race after the confirmation page
    model_admin.delete_queryset(request, Usuario.objects.filter(pk=m.pk))
    assert Usuario.objects.filter(pk=m.pk).exists()
    assert "só você vê" in str(list(request._messages)[0])
    contas.cancelar(m, orfa.pk)
    assert client.post(pagina, {"post": "yes"}).status_code == 302
    assert not Usuario.objects.filter(pk=m.pk).exists()


@pytest.mark.django_db(transaction=True)
def test_rn32_concorrencia_os_dois_unicos_que_veem_saem_juntos(f):
    m, o = f.u["membro"], f.u["observador"]
    conta = restrita(m, f.grupo, acesso=[o.pk])
    resultados = rodar_em_paralelo(lambda: grupos.sair(m, f.grupo), lambda: grupos.sair(o, f.grupo))
    assert sum(r is None for r in resultados) == 1
    assert sum(isinstance(r, grupos.ContaRestritaSemQuemVeja) for r in resultados) == 1
    assert Membro.objects.filter(espaco=f.grupo, usuario__in=[m, o]).count() == 1
    assert Lancamento.objects.get(pk=conta.pk).status == "pendente"


# ---- CA20 / CA21 / RN32: removal by the admin ----------------------------------------------


def test_rn32_remocao_admin_cancela_orfa(f):
    m = f.u["membro"]
    orfa = restrita(m, f.grupo, descricao="Presente")
    vista = restrita(m, f.grupo, acesso=[f.u["observador"].pk])
    paga = nova(f.u["admin"], f.grupo, pagador=m.pk)
    admin = cliente(f.u["admin"])
    response = admin.delete(f"/api/grupos/{f.grupo.pk}/membros/{f.m['membro'].pk}/")
    assert response.status_code == 204 and response.content == b""
    orfa.refresh_from_db()
    assert orfa.status == "cancelada"
    auto = Historico.objects.get(lancamento=orfa, acao="cancelada_automaticamente")
    assert auto.usuario is None
    assert auto.dados == {"motivo": "sem_quem_veja", "removido": str(m.pk)}
    assert estado(vista)[0] == "pendente" and historico(vista) == ["criada"]
    assert Lancamento.objects.get(pk=paga.pk).pagador is None  # RN21 only
    assert admin.get(url(orfa)).status_code == 404  # never escalated to the admin
    assert cliente(f.u["observador"]).get(url(orfa)).status_code == 404


@pytest.mark.django_db(transaction=True)
def test_rn32_remocao_admin_concorrencia_cancela_uma_vez(f):
    entrar(f, "chefe", "admin")
    m, o = f.u["membro"], f.u["observador"]
    conta = restrita(m, f.grupo, acesso=[o.pk])
    resultados = rodar_em_paralelo(
        lambda: grupos.remover_membro(f.grupo, f.m["membro"].pk),
        lambda: grupos.remover_membro(f.grupo, f.m["observador"].pk),
    )
    assert resultados == [None, None]
    assert historico(conta).count("cancelada_automaticamente") == 1
    assert Lancamento.objects.get(pk=conta.pk).status == "cancelada"


def test_rn32_rn06_remocao_admin_sem_sinal(f):
    entrar(f, "outro")
    restrita(f.u["membro"], f.grupo, pagador=f.u["membro"].pk, subgrupo=f.casa.pk)
    visivel = nova(f.u["admin"], f.grupo, subgrupo=f.casa.pk)
    admin = cliente(f.u["admin"])

    def visao():
        grupo = admin.get(f"/api/grupos/{f.grupo.pk}/").json()
        membros = [m for m in grupo.pop("membros") if m["nome"] not in ("Membro", "Outro")]
        return consultas(admin, f, url(visivel)), grupo, membros

    antes = visao()
    tempos, respostas = [], []
    for nome in ("membro", "outro"):  # with orphans, then without
        inicio = time.perf_counter()
        respostas.append(admin.delete(f"/api/grupos/{f.grupo.pk}/membros/{f.m[nome].pk}/"))
        tempos.append(time.perf_counter() - inicio)
    com, sem = respostas
    assert com.status_code == sem.status_code == 204
    assert com.content == sem.content and dict(com.headers) == dict(sem.headers)
    assert abs(tempos[0] - tempos[1]) < 0.5  # same order of magnitude, no shortcut
    assert visao() == antes
    assert Historico.objects.filter(acao="cancelada_automaticamente").count() == 1


# ---- CA23 / ADR 0007 -----------------------------------------------------------------------


def test_rn05_rn32_excecao_so_na_saida(f):
    o = f.u["observador"]
    conta = restrita(f.u["membro"], f.grupo, acesso=[o.pk], descricao="Presente")
    outra = restrita(f.u["membro"], f.grupo, acesso=[o.pk], descricao="Outra")
    assert sair(f.u["membro"], f).status_code == 204
    de_grupo = nova(f.u["admin"], f.grupo)
    obs = cliente(o)
    assert obs.patch(url(conta), {"descricao": "X"}, content_type=JSON).status_code == 403
    assert obs.post(url(conta, "cancelar/")).status_code == 403
    antes = (estado(conta), estado(outra))
    nao_bloqueia = [{"lancamento": str(de_grupo.pk), "acao": "cancelar"}]
    assert sair(o, f, nao_bloqueia).status_code == 400
    so_uma = [{"lancamento": str(conta.pk), "acao": "cancelar"}]
    assert sair(o, f, so_uma).status_code == 409  # one still orphan: nothing changes
    pagador = [
        {"lancamento": str(conta.pk), "acao": "acesso", "usuarios": [str(f.u["pagador"].pk)]}
    ]
    assert sair(o, f, pagador).status_code == 400
    assert (estado(conta), estado(outra)) == antes
    assert Membro.objects.filter(pk=f.m["observador"].pk).exists()
    resolucoes = [
        {"lancamento": str(conta.pk), "acao": "acesso", "usuarios": [str(f.u["admin"].pk)]},
        {"lancamento": str(outra.pk), "acao": "cancelar"},
    ]
    assert sair(o, f, resolucoes).status_code == 204
    assert not Membro.objects.filter(pk=f.m["observador"].pk).exists()
    editada = Historico.objects.get(lancamento=conta, acao="editada")
    assert editada.usuario == o and editada.dados["motivo"] == "saida_rn32"
    assert editada.dados["acesso"] == [["Observador"], ["Admin", "Observador"]]
    cancelada = Historico.objects.get(lancamento=outra, acao="cancelada")
    assert cancelada.usuario == o and cancelada.dados == {"motivo": "saida_rn32"}
    assert cliente(f.u["admin"]).get(url(conta)).status_code == 200
    assert Lancamento.objects.get(pk=outra.pk).status == "cancelada"


def test_rn05_rn32_pagador_resolve_na_saida(f):
    """CA23 for the payer role: the last one who sees a restricted bill cancels it while leaving."""
    p = f.u["pagador"]
    conta = restrita(f.u["membro"], f.grupo, pagador=p.pk, descricao="Presente")
    assert sair(f.u["membro"], f).status_code == 204
    assert cliente(p).post(url(conta, "cancelar/")).status_code == 403  # outside the exit: RN05
    assert sair(p, f).status_code == 409
    assert sair(p, f, [{"lancamento": str(conta.pk), "acao": "cancelar"}]).status_code == 204
    cancelada = Historico.objects.get(lancamento=conta, acao="cancelada")
    assert cancelada.usuario == p and cancelada.dados == {"motivo": "saida_rn32"}
    conta.refresh_from_db()
    assert conta.status == "cancelada" and conta.pagador == p  # Q7: cancelled bills keep the payer


def test_rn05_fora_da_saida_observador_403_404(f):
    obs = cliente(f.u["observador"])
    vista = nova(f.u["admin"], f.grupo)
    invisivel = restrita(f.u["admin"], f.grupo)
    assert obs.patch(url(vista), {"descricao": "X"}, content_type=JSON).status_code == 403
    assert obs.post(url(vista, "cancelar/")).status_code == 403
    assert obs.patch(url(invisivel), {"descricao": "X"}, content_type=JSON).status_code == 404
    assert obs.post(url(invisivel, "cancelar/")).status_code == 404
    corpo = {"resolucoes": [{"lancamento": str(vista.pk), "acao": "cancelar"}]}
    assert obs.patch(url(vista), corpo, content_type=JSON).status_code == 403
    assert estado(vista)[0:3] == ("pendente", None, "Luz")


# ---- CA24 / CA25 / ADR 0008, Q19b ----------------------------------------------------------


def test_rn06_rn07_alterar_papel_preserva_acesso(f):
    entrar(f, "outro")
    m = f.u["membro"]
    so_dela = restrita(m, f.grupo, descricao="Só dela")
    compartilhada = restrita(m, f.grupo, acesso=[f.u["observador"].pk])
    admin = cliente(f.u["admin"])

    def para_pagador(nome):
        return admin.patch(
            f"/api/grupos/{f.grupo.pk}/membros/{f.m[nome].pk}/",
            {"papel": "pagador"},
            content_type=JSON,
        )

    com, sem = para_pagador("membro"), para_pagador("outro")
    assert com.status_code == sem.status_code == 200
    assert com.json() == {
        "id": str(f.m["membro"].pk),
        "usuario": str(f.m["membro"].usuario_id),
        "nome": "Membro",
        "email": "membro@example.com",
        "papel": "pagador",
        "sou_eu": False,
    }
    assert com.json().keys() == sem.json().keys() and com.headers.keys() == sem.headers.keys()
    assert set(so_dela.acesso.values_list("pk", flat=True)) == {m.pk}
    auto = Historico.objects.get(lancamento=so_dela, acao="acesso_preservado")
    assert auto.usuario is None and auto.dados == {"motivo": "papel_pagador"}
    assert historico(compartilhada) == ["criada"]  # someone else still sees it
    assert set(compartilhada.acesso.values_list("pk", flat=True)) == {f.u["observador"].pk}
    assert cliente(m).get(url(so_dela)).status_code == 200
    assert cliente(m).get(url(compartilhada)).status_code == 404
    assert admin.get(url(so_dela)).status_code == 404


def test_rn32_editar_sem_quem_veja_400(f):
    entrar(f, "outro")
    m = f.u["membro"]
    conta = restrita(f.u["outro"], f.grupo, acesso=[m.pk])
    assert sair(f.u["outro"], f).status_code == 204  # membro is now the only one who sees it
    antes = estado(conta)
    response = cliente(m).patch(url(conta), {"acesso": []}, content_type=JSON)
    assert response.status_code == 400
    assert response.json() == {"acesso": [contas.SO_VOCE_VE]}
    assert estado(conta) == antes
    troca = {"acesso": [str(f.u["observador"].pk)]}
    assert cliente(m).patch(url(conta), troca, content_type=JSON).status_code == 200
    # Another way: the only one who sees it is its payer, who takes themselves out as payer.
    entrar(f, "terceiro")
    paga_so_ele = restrita(f.u["terceiro"], f.grupo, pagador=m.pk)
    assert sair(f.u["terceiro"], f).status_code == 204
    antes = estado(paga_so_ele)
    response = cliente(m).patch(url(paga_so_ele), {"pagador": None}, content_type=JSON)
    assert response.status_code == 400 and contas.SO_VOCE_VE in str(response.json())
    assert estado(paga_so_ele) == antes


# ---- CA26 / RN30 ---------------------------------------------------------------------------


def test_rn30_criador_excluido_ex_membro(f):
    entrar(f, "outro")
    o = f.u["outro"]
    conta = nova(o, f.grupo, pagador=o.pk)
    contas.editar(o, conta.pk, {"descricao": "Luz nova"})
    assert sair(o, f).status_code == 204
    o.delete()
    body = cliente(f.u["admin"]).get(url(conta)).json()
    assert body["criador"] == {"nome": "Ex-membro", "sou_eu": False}
    assert [(h["acao"], h["autor"], h["automatica"]) for h in body["historico"]] == [
        ("criada", "Ex-membro", False),
        ("editada", "Ex-membro", False),
        ("pagador_removido", None, True),
    ]


def test_rn32_admin_removendo_a_si_mesmo_e_saida_voluntaria(f):
    entrar(f, "chefe", "admin")
    orfa = restrita(f.u["admin"], f.grupo)
    response = cliente(f.u["admin"]).delete(f"/api/grupos/{f.grupo.pk}/membros/{f.m['admin'].pk}/")
    assert response.status_code == 409 and response.json()["code"] == "conta_restrita_orfa"
    assert estado(orfa)[0] == "pendente" and Membro.objects.filter(pk=f.m["admin"].pk).exists()
