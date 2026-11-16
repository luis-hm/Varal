"""Etapa05: instruments use the bill's permissions, locks, atomicity and history."""

from datetime import date

import pytest
from django.contrib import admin
from django.db import IntegrityError, transaction
from django.test import Client, RequestFactory
from rest_framework.exceptions import NotFound

from apps.boletos.models import Instrumento
from apps.contas_usuario.models import Usuario
from apps.espacos.acesso import lancamento_ou_404
from apps.lancamentos.models import Historico, Lancamento
from tests import test_contas
from tests.test_boletos_parser import DYNAMIC, STATIC, arrec, bancario, crc
from tests.test_contas import (
    HOJE,
    cliente,
    lista_url,
    nova,
    url,
)

pytestmark = pytest.mark.django_db
LER = "/api/boletos/ler/"
JSON = "application/json"
contas_fixture = test_contas.f
relogio_fixture = test_contas.relogio


@pytest.fixture
def f(contas_fixture):
    return contas_fixture


def dados(codigo=None, chave_pix=None, **campos):
    instrumento = {"codigo": codigo or bancario(1000)}
    if chave_pix:
        instrumento = {"chave_pix": chave_pix}
    return {
        "descricao": "Conta com código",
        "valor_centavos": 12345,
        "vencimento": "2025-02-22",
        "instrumento": instrumento,
        **campos,
    }


def criar(f, **campos):
    response = cliente(f.u["membro"]).post(lista_url(f.grupo), dados(**campos), content_type=JSON)
    assert response.status_code == 201, response.content
    return Lancamento.objects.get(pk=response.json()["id"]), response.json()


def test_rf08_preview_autenticado_nao_grava(f):
    assert Client().post(LER, {"codigo": bancario(1000)}, content_type=JSON).status_code == 403
    linha = bancario(1000)
    response = cliente(f.u["observador"]).post(
        LER, {"codigo": linha[:5] + "." + linha[5:10] + " " + linha[10:]}, content_type=JSON
    )
    assert response.status_code == 200
    body = response.json()
    assert body["instrumento"] == {
        "tipo": "boleto_bancario",
        "codigo": linha,
        "chave_pix": None,
        "beneficiario": None,
    }
    assert body["valor_centavos"] == 12345
    assert body["vencimento"] == "2025-02-22"
    assert body["vencimentos_possiveis"] == ["2025-02-22", "2000-07-03"]
    assert body["avisos"]
    assert not Lancamento.objects.exists()
    assert not Instrumento.objects.exists()
    assert not Historico.objects.exists()


def test_rnf01_preview_exige_csrf_da_sessao(f):
    client = Client(enforce_csrf_checks=True)
    client.force_login(f.u["membro"])
    response = client.post(LER, {"codigo": bancario(1000)}, content_type=JSON)
    assert response.status_code == 403 and "CSRF" in response.json()["detail"]


@pytest.mark.parametrize("entrada", [{"codigo": STATIC + "\x00"}, {"chave_pix": "ana\x00@x.com"}])
def test_rf09_campos_textuais_rejeitam_nul_no_preview_e_save(f, entrada):
    client = cliente(f.u["membro"])
    assert client.post(LER, entrada, content_type=JSON).status_code == 400
    response = client.post(lista_url(f.grupo), dados(instrumento=entrada), content_type=JSON)
    assert response.status_code == 400
    assert not Instrumento.objects.exists()
    assert not Lancamento.objects.exists()
    assert not Historico.objects.exists()


@pytest.mark.parametrize(
    "entrada",
    [
        {},
        {"codigo": bancario(1000), "chave_pix": "user@example.com"},
        {"codigo": "0" * 4097},
        {"codigo": ""},
        {"codigo": "1" * 47},
        {"codigo": None},
        {"codigo": 123},
        {"chave_pix": 52998224725},
        {"chave_pix": "a" * 78},
        {"chave_pix": "invalid"},
    ],
)
def test_rn08_rf09_preview_invalido_400_sem_gravar(f, entrada):
    response = cliente(f.u["membro"]).post(LER, entrada, content_type=JSON)
    assert response.status_code == 400, response.content
    assert not Lancamento.objects.exists()
    assert not Instrumento.objects.exists()


@pytest.mark.parametrize("codigo", [STATIC, DYNAMIC, arrec("7")])
def test_rf09_rn10_preview_campos_ausentes_permanecem_ausentes(f, codigo):
    response = cliente(f.u["membro"]).post(LER, {"codigo": codigo}, content_type=JSON)
    assert response.status_code == 200
    body = response.json()
    assert body["valor_centavos"] is None and body["vencimento"] is None
    assert body["vencimentos_possiveis"] == []
    assert body["instrumento"]["codigo"] == codigo


@pytest.mark.parametrize(
    "codigo,chave,tipo",
    [
        (bancario(1000), None, "boleto_bancario"),
        (arrec("6"), None, "boleto_arrecadacao"),
        (STATIC, None, "pix"),
        (DYNAMIC, None, "pix"),
        (None, "USER@example.com", "pix"),
    ],
)
def test_rf08_rf09_criar_instrumento_e_detalhe_sem_payload_em_listas(f, codigo, chave, tipo):
    conta, body = criar(f, codigo=codigo, chave_pix=chave)
    inst = conta.instrumento
    assert inst.tipo == body["instrumento"]["tipo"] == tipo
    assert inst.pk == conta.pk
    assert inst.codigo == codigo
    assert inst.chave_pix == ("user@example.com" if chave else None)
    assert conta.status == "pendente"
    client = cliente(f.u["membro"])
    assert client.get(url(conta)).json()["instrumento"] == body["instrumento"]
    itens = client.get(lista_url(f.grupo), {"mes": "2025-02"}).json()["itens"]
    assert all("instrumento" not in item for item in itens)
    resumo = client.get(f"/api/espacos/{f.grupo.pk}/resumo/").json()
    assert all("instrumento" not in item for item in resumo["atencao"])
    historico = list(conta.historico.values_list("dados", flat=True))
    if codigo:
        assert codigo not in str(historico)
    assert "user@example.com" not in str(historico)


@pytest.mark.parametrize("vencimento", ["2025-02-22", "2000-07-03"])
def test_rn09_salvar_fator_ambiguo_somente_datas_codificadas(f, vencimento):
    conta, _ = criar(f, vencimento=vencimento)
    assert conta.vencimento.isoformat() == vencimento


@pytest.mark.parametrize(
    "extra",
    [
        {"valor_centavos": 12346},
        {"vencimento": "2026-11-16"},
        {"instrumento": {"codigo": bancario(1000)[:-1] + "9"}},
    ],
)
def test_rn09_rn11_save_revalida_400_sem_gravacao_parcial(f, extra):
    client = cliente(f.u["membro"])
    preview = client.post(LER, {"codigo": bancario(1000)}, content_type=JSON)
    assert preview.status_code == 200
    response = client.post(lista_url(f.grupo), dados(**extra), content_type=JSON)
    assert response.status_code == 400, response.content
    assert not Lancamento.objects.exists()
    assert not Instrumento.objects.exists()
    assert not Historico.objects.exists()


def test_rf09_pix_estatico_valor_codificado_e_dinamico_ignorado(f):
    static = crc(STATIC[:-8].replace("5802BR", "54041.005802BR"))
    client = cliente(f.u["membro"])
    bad = client.post(lista_url(f.grupo), dados(codigo=static), content_type=JSON)
    assert bad.status_code == 400 and "valor_centavos" in bad.json()
    conta, _ = criar(f, codigo=static, valor_centavos=100)
    assert conta.valor_centavos == 100
    dynamic = crc(DYNAMIC[:-8].replace("5802BR", "54041.005802BR"))
    conta, _ = criar(f, codigo=dynamic, valor_centavos=54321)
    assert conta.valor_centavos == 54321 and conta.instrumento.codigo == dynamic


@pytest.mark.parametrize("papel", ["observador", "pagador"])
def test_rn05_instrumento_so_edita_quem_pode_editar_conta(f, papel):
    conta, _ = criar(f, pagador=str(f.u["pagador"].pk))
    client = cliente(f.u[papel])
    assert client.get(url(conta)).status_code == 200
    assert client.get(url(conta)).json()["instrumento"]["codigo"] == bancario(1000)
    assert client.patch(url(conta), {"instrumento": None}, content_type=JSON).status_code == 403
    assert client.post(lista_url(f.grupo), dados(), content_type=JSON).status_code == 403
    assert Instrumento.objects.get(lancamento=conta).codigo == bancario(1000)


@pytest.mark.parametrize("tipo", ["restrita", "pessoal", "alheia"])
def test_rn01_rn02_rn06_instrumento_herda_404_conta(f, tipo):
    if tipo == "pessoal":
        espaco = f.pessoal["membro"]
        campos = {}
    else:
        espaco = f.grupo
        campos = {"visibilidade": "restrita"} if tipo == "restrita" else {}
    client_autor = cliente(f.u["membro"])
    response = client_autor.post(lista_url(espaco), dados(**campos), content_type=JSON)
    assert response.status_code == 201, response.content
    conta = Lancamento.objects.get(pk=response.json()["id"])
    invasor = f.u["admin"] if tipo == "restrita" else f.u["fora"]
    client = cliente(invasor)
    assert client.get(url(conta)).status_code == 404
    assert client.patch(url(conta), {"instrumento": None}, content_type=JSON).status_code == 404
    assert client.get(f"/api/boletos/instrumentos/{conta.pk}/").status_code == 404


def test_rn22_editar_trocar_remover_preservar_e_noop_sem_payload_historico(f):
    conta, _ = criar(f)
    client = cliente(f.u["membro"])
    linha = bancario(1000)
    h0 = conta.historico.count()
    response = client.patch(url(conta), {"descricao": "Novo nome"}, content_type=JSON)
    assert response.status_code == 200 and response.json()["instrumento"]["codigo"] == linha
    h1 = conta.historico.count()
    assert h1 == h0 + 1
    response = client.patch(url(conta), {"instrumento": {"codigo": linha}}, content_type=JSON)
    assert response.status_code == 200 and conta.historico.count() == h1
    response = client.patch(
        url(conta), {"instrumento": {"chave_pix": "USER@example.com"}}, content_type=JSON
    )
    assert response.status_code == 200
    assert response.json()["instrumento"]["chave_pix"] == "user@example.com"
    assert conta.historico.last().dados == {
        "instrumento": ["boleto_bancario", "pix"],
        "codigo_alterado": True,
    }
    response = client.patch(url(conta), {"instrumento": None}, content_type=JSON)
    assert response.status_code == 200 and response.json()["instrumento"] is None
    assert not Instrumento.objects.filter(lancamento=conta).exists()
    assert conta.historico.last().dados["instrumento"] == ["pix", "manual"]
    assert linha not in str(list(conta.historico.values_list("dados", flat=True)))
    assert "user@example.com" not in str(list(conta.historico.values_list("dados", flat=True)))


@pytest.mark.parametrize("campo,valor", [("valor_centavos", 100), ("vencimento", "2026-11-16")])
def test_rn09_patch_instrumento_ausente_ainda_valida_valor_data(f, campo, valor):
    conta, _ = criar(f)
    antes = (conta.valor_centavos, conta.vencimento, conta.historico.count())
    response = cliente(f.u["membro"]).patch(url(conta), {campo: valor}, content_type=JSON)
    assert response.status_code == 400 and campo in response.json()
    conta.refresh_from_db()
    assert (conta.valor_centavos, conta.vencimento, conta.historico.count()) == antes
    assert conta.instrumento.codigo == bancario(1000)


def test_rn09_patch_troca_fator_ambiguo_exige_data_e_sem_parcial(f):
    conta, _ = criar(f)
    antes = conta.historico.count()
    client = cliente(f.u["membro"])
    response = client.patch(
        url(conta), {"instrumento": {"codigo": bancario(1001)}}, content_type=JSON
    )
    assert response.status_code == 400 and "vencimento" in response.json()
    assert Instrumento.objects.get(lancamento=conta).codigo == bancario(1000)
    assert conta.historico.count() == antes
    response = client.patch(
        url(conta),
        {"instrumento": {"codigo": bancario(1001)}, "vencimento": "2000-07-04"},
        content_type=JSON,
    )
    assert response.status_code == 200
    conta.refresh_from_db()
    assert conta.vencimento == date(2000, 7, 4)


@pytest.mark.parametrize("status_", ["paga", "confirmada", "cancelada"])
@pytest.mark.parametrize("instrumento", [None, {"chave_pix": "+5585999999999"}])
def test_rn22_instrumento_fechada_nao_troca_nem_remove(f, status_, instrumento):
    conta, _ = criar(f)
    Lancamento.objects.filter(pk=conta.pk).update(status=status_)
    h = conta.historico.count()
    response = cliente(f.u["membro"]).patch(
        url(conta), {"instrumento": instrumento}, content_type=JSON
    )
    assert response.status_code == 409, response.content
    assert Instrumento.objects.get(lancamento=conta).codigo == bancario(1000)
    assert conta.historico.count() == h


def test_rn12_aguardando_anexa_instrumento_e_vira_pendente_atomicamente(f):
    conta = nova(f.u["membro"], f.grupo)
    Lancamento.objects.filter(pk=conta.pk).update(status="aguardando")
    client = cliente(f.u["membro"])
    antes = conta.historico.count()
    invalida = client.patch(url(conta), {"instrumento": {"codigo": "inválido"}}, content_type=JSON)
    assert invalida.status_code == 400
    conta.refresh_from_db()
    assert conta.status == "aguardando" and conta.historico.count() == antes
    assert not Instrumento.objects.filter(lancamento=conta).exists()
    response = client.patch(
        url(conta),
        {"instrumento": {"chave_pix": "+5585999999999"}, "confirmar_chegada": True},
        content_type=JSON,
    )
    assert response.status_code == 200 and response.json()["status"] == "pendente"
    assert conta.historico.last().dados["status"] == ["aguardando", "pendente"]
    response = client.patch(url(conta), {"status": "paga"}, content_type=JSON)
    assert response.status_code == 200 and response.json()["status"] == "pendente"


def test_rf10_manual_legada_sem_instrumento_e_null_noop(f):
    conta = nova(f.u["membro"], f.grupo)
    client = cliente(f.u["membro"])
    assert client.get(url(conta)).json()["instrumento"] is None
    h = conta.historico.count()
    response = client.patch(url(conta), {"instrumento": None}, content_type=JSON)
    assert response.status_code == 200 and response.json()["instrumento"] is None
    assert conta.historico.count() == h
    assert not Instrumento.objects.exists()
    response = client.post(
        lista_url(f.grupo),
        {"descricao": "Manual", "valor_centavos": 100, "vencimento": HOJE.isoformat()},
        content_type=JSON,
    )
    assert response.status_code == 201 and response.json()["instrumento"] is None


def test_rnf01_m5_instrumento_sem_admin_ou_exposicao_em_cascata(f):
    response = cliente(f.u["membro"]).post(
        lista_url(f.pessoal["membro"]), dados(), content_type=JSON
    )
    assert response.status_code == 201
    conta = Lancamento.objects.get(pk=response.json()["id"])
    assert not admin.site.is_registered(Instrumento)
    root = Usuario.objects.create_superuser("root", "root@example.com", None)
    request = RequestFactory().get("/admin/")
    request.user = root
    assert not admin.site._registry[Lancamento].get_queryset(request).exists()
    pagina = cliente(root).get(f"/admin/contas_usuario/usuario/{f.u['membro'].pk}/delete/")
    assert pagina.status_code == 200
    assert conta.instrumento.codigo not in pagina.content.decode()
    assert conta.descricao not in pagina.content.decode()


@pytest.mark.parametrize(
    "campos",
    [
        {"tipo": "manual", "codigo": "1" * 47},
        {"tipo": "pix", "codigo": None, "chave_pix": None},
        {"tipo": "pix", "codigo": STATIC, "chave_pix": "+5585999999999"},
        {"tipo": "boleto_bancario", "codigo": None},
        {"tipo": "boleto_bancario", "codigo": "1" * 46},
        {"tipo": "boleto_arrecadacao", "codigo": "1" * 48},
    ],
)
def test_rf08_rf09_banco_recusa_instrumento_incoerente(f, campos):
    conta = nova(f.u["membro"], f.grupo)
    with pytest.raises(IntegrityError), transaction.atomic():
        Instrumento.objects.create(lancamento=conta, **campos)
    assert not Instrumento.objects.exists()


def test_rf08_mesmo_codigo_em_contas_distintas_e_vinculo_unico(f):
    conta, _ = criar(f)
    outra, _ = criar(f)
    assert Instrumento.objects.count() == 2
    assert conta.instrumento.codigo == outra.instrumento.codigo
    with pytest.raises(IntegrityError), transaction.atomic():
        Instrumento.objects.create(lancamento=conta, tipo="pix", chave_pix="user@example.com")


def test_rn06_detalhe_nao_entrega_instrumento_novo_apos_revogar_acesso(f):
    from apps.lancamentos.views import _detalhe

    leitor = f.u["observador"]
    conta, _ = criar(f, visibilidade="restrita", acesso=[str(leitor.pk)])
    autorizada = lancamento_ou_404(leitor, conta.pk)
    response = cliente(f.u["membro"]).patch(
        url(conta),
        {"acesso": [], "instrumento": {"chave_pix": "novo@example.com"}},
        content_type=JSON,
    )
    assert response.status_code == 200
    assert response.json()["instrumento"]["chave_pix"] == "novo@example.com"
    request = RequestFactory().get(url(conta))
    request.user = leitor
    with pytest.raises(NotFound):
        _detalhe(request, conta.pk, autorizada.espaco)
