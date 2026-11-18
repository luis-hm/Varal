"""COR-10 / ADR 0017: the admin sets, per category, what each membro/observador may do."""

import uuid

import pytest
from django.utils import timezone

from apps.espacos.acesso import quem_ve
from apps.espacos.models import HistoricoPermissao, Subgrupo
from tests import test_contas
from tests.test_contas import lista, nova, restrita, resumo, url
from tests.test_grupos import cliente

pytestmark = pytest.mark.django_db
JSON = "application/json"
f = test_contas.f
relogio = test_contas.relogio
NADA = {"ver": False, "criar": False, "editar": False, "pagar": False, "recorrencias": False}
TUDO = dict.fromkeys(NADA, True)


def permissoes_url(f, casa):
    return f"/api/grupos/{f.grupo.pk}/subgrupos/{casa.pk}/permissoes/"


def salvar(f, casa, personalizada=True, nome="admin", versao=None, **por_pessoa):
    """`por_pessoa`: membro=dict(...), observador=dict(...); left out = the role default."""
    casa.refresh_from_db()
    corpo = {
        "personalizada": personalizada,
        "versao": casa.versao if versao is None else versao,
        "membros": [
            {"membro_id": str(f.m[quem].pk), **NADA, **caps} for quem, caps in por_pessoa.items()
        ],
    }
    return cliente(f.u[nome]).put(permissoes_url(f, casa), corpo, content_type=JSON)


def personalizar(f, casa, **por_pessoa):
    response = salvar(f, casa, **por_pessoa)
    assert response.status_code == 200, response.content
    return response.json()


def criar_api(f, nome, casa=None, **extra):
    corpo = {"descricao": "Luz", "valor_centavos": 1000, "vencimento": "2026-11-25", **extra}
    if casa is not None:
        corpo["subgrupo"] = str(casa.pk)
    return cliente(f.u[nome]).post(
        f"/api/espacos/{f.grupo.pk}/lancamentos/", corpo, content_type=JSON
    )


def pagar(f, conta, nome):
    return cliente(f.u[nome]).post(
        url(conta, "pagamentos/"),
        {"pago_em": timezone.localdate().isoformat(), "valor_centavos_esperado": 1000},
        content_type=JSON,
    )


@pytest.fixture
def energia(f):
    return Subgrupo.objects.create(espaco=f.grupo, nome="Energia", icone="luz")


def test_cor10_sem_personalizar_nada_muda(f, energia):
    conta = nova(f.u["admin"], f.grupo, subgrupo=energia.pk)
    assert any(c["id"] == str(conta.pk) for c in lista(cliente(f.u["membro"]), f.grupo)["itens"])
    assert criar_api(f, "membro", energia).status_code == 201
    assert criar_api(f, "observador", energia).status_code == 403
    assert pagar(f, conta, "membro").status_code == 201
    estado = cliente(f.u["admin"]).get(permissoes_url(f, energia)).json()
    padrao = {m["papel"]: {c: m[c] for c in NADA} for m in estado["membros"]}
    assert estado["personalizada"] is False
    assert padrao == {"membro": TUDO, "observador": {**NADA, "ver": True}}


def test_cor10_observador_pode_criar_se_admin_permitir(f, energia):
    personalizar(f, energia, observador={"ver": True, "criar": True})
    assert criar_api(f, "observador", energia).status_code == 201
    # Only there: no category and other categories keep the role default.
    assert criar_api(f, "observador").status_code == 403
    assert criar_api(f, "observador", f.casa).status_code == 403


def test_cor10_membro_sem_ver_nao_lista_nem_abre_detalhe(f, energia):
    conta = nova(f.u["admin"], f.grupo, subgrupo=energia.pk, valor_centavos=4321)
    personalizar(f, energia, membro=NADA, observador={"ver": True})
    membro = cliente(f.u["membro"])
    dados = lista(membro, f.grupo)
    assert all(c["id"] != str(conta.pk) for c in dados["itens"])
    assert all(c["id"] != str(energia.pk) for c in dados["opcoes"]["casas"])
    assert lista(membro, f.grupo, subgrupo=str(energia.pk))["itens"] == []
    assert membro.get(url(conta)).status_code == 404
    assert membro.get(url(conta, "pdf/")).status_code == 404
    painel = resumo(membro, f.grupo)
    assert painel["total_centavos"] == 0
    assert all(c["id"] != str(energia.pk) for c in painel["por_casa"])
    grupo = membro.get(f"/api/grupos/{f.grupo.pk}/").json()
    assert [c["nome"] for c in grupo["casas"]] == ["Casa da praia"]
    # The observer granted "ver" and the admin still see it.
    assert cliente(f.u["observador"]).get(url(conta)).status_code == 200
    assert cliente(f.u["admin"]).get(url(conta)).status_code == 200


def test_cor10_ver_nao_abre_restrita(f, energia):
    conta = restrita(f.u["admin"], f.grupo, subgrupo=energia.pk)
    personalizar(f, energia, membro=TUDO)
    assert cliente(f.u["membro"]).get(url(conta)).status_code == 404


def test_cor10_criador_e_pagador_sempre_veem(f, energia):
    criada = nova(f.u["membro"], f.grupo, subgrupo=energia.pk)
    paga_por = nova(f.u["admin"], f.grupo, subgrupo=energia.pk, pagador=f.u["membro"].pk)
    personalizar(f, energia, membro=NADA, observador=NADA)
    membro = cliente(f.u["membro"])
    assert membro.get(url(criada)).status_code == 200
    assert membro.get(url(paga_por)).status_code == 200
    # The assigned payer still pays (RN07); someone else's bill is not editable.
    assert pagar(f, paga_por, "membro").status_code == 201
    assert membro.patch(url(criada), {"descricao": "x"}, content_type=JSON).status_code == 403


def test_cor10_pagar_exige_permissao_ou_ser_pagador(f, energia):
    conta = nova(f.u["admin"], f.grupo, subgrupo=energia.pk)
    personalizar(f, energia, membro={"ver": True})
    assert pagar(f, conta, "membro").status_code == 403
    assert cliente(f.u["membro"]).get(url(conta)).json()["pode_pagar"] is False
    personalizar(f, energia, membro={"ver": True, "pagar": True})
    assert cliente(f.u["membro"]).get(url(conta)).json()["pode_pagar"] is True
    assert pagar(f, conta, "membro").status_code == 201


def test_cor10_editar_e_cancelar_exigem_editar(f, energia):
    conta = nova(f.u["admin"], f.grupo, subgrupo=energia.pk)
    personalizar(f, energia, membro={"ver": True})
    membro = cliente(f.u["membro"])
    assert membro.get(url(conta)).json()["pode_editar"] is False
    assert membro.patch(url(conta), {"descricao": "x"}, content_type=JSON).status_code == 403
    assert membro.post(url(conta, "cancelar/"), {}, content_type=JSON).status_code == 403
    personalizar(f, energia, membro={"ver": True, "editar": True})
    assert membro.patch(url(conta), {"descricao": "x"}, content_type=JSON).status_code == 200


def test_cor10_mudar_categoria_exige_criar_na_nova(f, energia):
    conta = nova(f.u["admin"], f.grupo, subgrupo=f.casa.pk)
    personalizar(f, energia, membro={"ver": True})
    membro = cliente(f.u["membro"])
    mover = {"subgrupo": str(energia.pk)}
    assert membro.patch(url(conta), mover, content_type=JSON).status_code == 403
    personalizar(f, energia, membro={"ver": True, "criar": True})
    assert membro.patch(url(conta), mover, content_type=JSON).status_code == 200


def test_cor10_recorrencias_exige_permissao(f, energia):
    personalizar(f, energia, membro={"ver": True, "criar": True})
    corpo = {
        "chave_idempotencia": str(uuid.uuid4()),
        "descricao": "Energia",
        "dia_vencimento": 28,
        "valor_tipo": "variavel",
        "valor_centavos": None,
        "subgrupo": str(energia.pk),
    }
    membro = cliente(f.u["membro"])
    rota = f"/api/espacos/{f.grupo.pk}/recorrencias/"
    assert membro.post(rota, corpo, content_type=JSON).status_code == 403
    personalizar(f, energia, membro={"ver": True, "recorrencias": True})
    criada = membro.post(rota, corpo, content_type=JSON)
    assert criada.status_code == 201, criada.content
    modelo = criada.json()["recorrencia"]["id"]
    personalizar(f, energia, membro={"ver": True})
    pausar = membro.post(f"/api/recorrencias/{modelo}/pausar/", {}, content_type=JSON)
    assert pausar.status_code == 403


def test_cor10_so_admin_altera_permissoes(f, energia):
    assert salvar(f, energia, nome="membro").status_code == 403
    assert cliente(f.u["membro"]).get(permissoes_url(f, energia)).status_code == 403
    assert salvar(f, energia, nome="fora").status_code == 404


def test_cor10_versao_antiga_da_409(f, energia):
    personalizar(f, energia, membro=TUDO)
    response = salvar(f, energia, versao=1, membro={"ver": True})
    assert response.status_code == 409
    energia.refresh_from_db()
    assert energia.versao == 2


def test_cor10_permissao_sem_ver_da_400(f, energia):
    assert salvar(f, energia, membro={"pagar": True}).status_code == 400
    assert salvar(f, energia, pagador={"ver": True}).status_code == 400  # payer is not editable
    energia.refresh_from_db()
    assert energia.personalizada is False


def test_cor10_ids_de_outro_grupo_nao_dao_acesso(f, energia):
    outro = test_contas.grupos.criar_grupo(f.u["fora"], "Outro", ["Dele"])
    casa_dele = outro.subgrupos.get()
    admin = cliente(f.u["admin"])
    cruzada = f"/api/grupos/{f.grupo.pk}/subgrupos/{casa_dele.pk}/permissoes/"
    assert admin.get(cruzada).status_code == 404
    assert criar_api(f, "membro", casa_dele).status_code == 400


def test_cor10_revogar_vale_na_proxima_consulta_e_nos_avisos(f, energia):
    conta = nova(f.u["admin"], f.grupo, subgrupo=energia.pk)
    membro = cliente(f.u["membro"])
    assert membro.get(url(conta)).status_code == 200
    assert f.u["membro"].pk in quem_ve(conta)
    personalizar(f, energia, membro=NADA, observador={"ver": True})
    assert membro.get(url(conta)).status_code == 404
    assert f.u["membro"].pk not in quem_ve(conta)  # reminders and notices use quem_ve
    personalizar(f, energia, personalizada=False)
    assert membro.get(url(conta)).status_code == 200


def test_cor10_historico_sem_nomes_e_membro_removido_perde_permissoes(f, energia):
    personalizar(f, energia, membro=TUDO)
    registro = HistoricoPermissao.objects.get(subgrupo=energia)
    assert registro.autor == f.u["admin"]
    assert registro.antes["personalizada"] is False and registro.depois["personalizada"] is True
    assert "Membro" not in str(registro.depois)
    f.m["membro"].delete()
    assert not energia.permissoes.exists()


def test_cor10_capacidades_na_categoria(f, energia):
    personalizar(f, energia, membro={"ver": True, "criar": True})
    casas = cliente(f.u["membro"]).get(f"/api/grupos/{f.grupo.pk}/").json()["casas"]
    por_nome = {c["nome"]: c["capacidades"] for c in casas}
    assert por_nome == {
        "Casa da praia": ["ver", "criar", "editar", "pagar", "recorrencias"],
        "Energia": ["ver", "criar"],
    }


# ---- security review (18/11/2026) -----------------------------------------------------------


def test_cor10_trocar_papel_traz_o_padrao_do_novo_papel(f, energia):
    personalizar(f, energia, membro={"ver": True}, observador=NADA)
    admin = cliente(f.u["admin"])
    rota = f"/api/grupos/{f.grupo.pk}/membros/{f.m['membro'].pk}/"
    # Demoted: the observer default (only "ver"); the old grant is gone.
    assert admin.patch(rota, {"papel": "observador"}, content_type=JSON).status_code == 200
    assert not energia.permissoes.filter(membro=f.m["membro"]).exists()
    assert criar_api(f, "membro", energia).status_code == 403
    assert cliente(f.u["membro"]).get(f"/api/grupos/{f.grupo.pk}/").status_code == 200
    # Promoted: the member default (everything), even in the personalised category.
    assert admin.patch(rota, {"papel": "membro"}, content_type=JSON).status_code == 200
    assert criar_api(f, "membro", energia).status_code == 201


def test_cor10_membro_novo_recebe_o_padrao_do_papel(f, energia):
    personalizar(f, energia, membro=NADA, observador=NADA)
    novo = test_contas.entrar(f, "novo", papel="observador")
    conta = nova(f.u["admin"], f.grupo, subgrupo=energia.pk)
    assert cliente(novo).get(url(conta)).status_code == 200
    estado = cliente(f.u["admin"]).get(permissoes_url(f, energia)).json()
    linha = next(m for m in estado["membros"] if m["membro_id"] == str(f.m["novo"].pk))
    assert {c: linha[c] for c in NADA} == {**NADA, "ver": True}
    assert cliente(f.u["membro"]).get(url(conta)).status_code == 404


def test_cor10_editar_nao_vira_pagar_por_se_atribuir(f, energia):
    conta = nova(f.u["admin"], f.grupo, subgrupo=energia.pk)
    personalizar(f, energia, membro={"ver": True, "criar": True, "editar": True})
    membro = cliente(f.u["membro"])
    eu = {"pagador": str(f.u["membro"].pk)}
    assert membro.patch(url(conta), eu, content_type=JSON).status_code == 403
    assert pagar(f, conta, "membro").status_code == 403
    # Creating, the creator is born payer (owner, 18/11/2026).
    assert criar_api(f, "membro", energia, **eu).status_code == 201
    # Naming someone else still works.
    outro = {"pagador": str(f.u["admin"].pk)}
    assert membro.patch(url(conta), outro, content_type=JSON).status_code == 200


def test_cor10_solicitacao_exige_criar_sem_categoria(f, energia):
    personalizar(f, energia, observador={"ver": True, "criar": True})
    origem = nova(f.u["observador"], f.pessoal["observador"])
    detalhe = cliente(f.u["observador"]).get(url(origem)).json()
    payload = {
        "nonce": str(uuid.uuid4()),
        "grupo_id": str(f.grupo.pk),
        "pagador_id": str(f.u["pagador"].pk),
        "mensagem": "Por favor",
        "confirmar_compartilhamento": True,
        "versao_compartilhamento": detalhe["versao_compartilhamento"],
    }
    resposta = cliente(f.u["observador"]).post(
        url(origem, "solicitacoes/"), payload, content_type=JSON
    )
    assert resposta.status_code == 403


def test_cor10_recorrencias_e_comprovante_sem_ver(f, energia):
    corpo = {
        "chave_idempotencia": str(uuid.uuid4()),
        "descricao": "Energia",
        "dia_vencimento": 28,
        "valor_tipo": "variavel",
        "valor_centavos": None,
        "subgrupo": str(energia.pk),
    }
    admin = cliente(f.u["admin"])
    criada = admin.post(f"/api/espacos/{f.grupo.pk}/recorrencias/", corpo, content_type=JSON)
    assert criada.status_code == 201, criada.content
    modelo = criada.json()["recorrencia"]["id"]
    personalizar(f, energia, membro=NADA, observador={"ver": True})
    membro = cliente(f.u["membro"])
    lista_rec = membro.get(f"/api/espacos/{f.grupo.pk}/recorrencias/").json()
    assert all(r["id"] != modelo for r in lista_rec)
    assert membro.get(f"/api/recorrencias/{modelo}/").status_code == 404
    assert cliente(f.u["observador"]).get(f"/api/recorrencias/{modelo}/").status_code == 200


def test_cor10_cancelar_proximos_pula_conta_sem_editar(f, energia):
    from apps.lancamentos.models import Lancamento, Status

    corpo = {
        "chave_idempotencia": str(uuid.uuid4()),
        "descricao": "Energia",
        "dia_vencimento": 28,
        "valor_tipo": "fixo",
        "valor_centavos": 1000,
    }
    membro = cliente(f.u["membro"])
    criada = membro.post(f"/api/espacos/{f.grupo.pk}/recorrencias/", corpo, content_type=JSON)
    assert criada.status_code == 201, criada.content
    conta = Lancamento.objects.get(pk=criada.json()["ocorrencia"]["id"])
    outra = nova(f.u["admin"], f.grupo, subgrupo=energia.pk)
    Lancamento.objects.filter(pk=outra.pk).update(
        recorrencia=conta.recorrencia, competencia=conta.competencia.replace(month=12)
    )
    personalizar(f, energia, membro={"ver": True})
    resposta = membro.post(url(conta, "cancelar/"), {"escopo": "proximos"}, content_type=JSON)
    assert resposta.status_code == 200, resposta.content
    assert Lancamento.objects.get(pk=conta.pk).status == Status.CANCELADA
    assert Lancamento.objects.get(pk=outra.pk).status != Status.CANCELADA


def test_cor10_lista_de_grupos_conta_so_categorias_visiveis(f, energia):
    personalizar(f, energia, membro=NADA, observador={"ver": True})
    grupos = cliente(f.u["membro"]).get("/api/grupos/").json()
    assert next(g for g in grupos if g["id"] == str(f.grupo.pk))["casas_qtd"] == 1
    grupos = cliente(f.u["admin"]).get("/api/grupos/").json()
    assert next(g for g in grupos if g["id"] == str(f.grupo.pk))["casas_qtd"] == 2
