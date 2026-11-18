import uuid

import pytest
from cryptography.fernet import Fernet
from django.db import transaction

from apps.espacos.models import Espaco
from apps.privacidade.models import RevisaoExportacao
from tests import test_contas
from tests.test_grupos import cliente
from tests.test_notificacoes import dados_push

contas_fixture = test_contas.f


@pytest.mark.django_db
def test_rn30_revisao_bulk_e_rollback(contas_fixture):
    revisao = lambda: RevisaoExportacao.objects.get(pk=1).valor  # noqa: E731
    antes = revisao()
    Espaco.objects.filter(pk=contas_fixture.grupo.pk).update(nome="Outro nome")
    depois = revisao()
    assert depois > antes
    with pytest.raises(ValueError), transaction.atomic():
        Espaco.objects.filter(pk=contas_fixture.grupo.pk).update(nome="Rollback")
        assert revisao() > depois
        raise ValueError
    assert revisao() == depois


@pytest.mark.django_db
def test_rnf10_instalacao_estado_so_dono_e_sessao(contas_fixture, settings):
    settings.WEBPUSH_ENABLED = True
    settings.WEBPUSH_PUBLIC_KEY = "publica"
    settings.NOTIFICACOES_STORAGE_KEY = Fernet.generate_key().decode()
    dono = cliente(contas_fixture.u["admin"])
    outro = cliente(contas_fixture.u["membro"])
    dados = dados_push()
    url = f"/api/notificacoes/push/instalacoes/{dados['instalacao']}/"
    assert (
        dono.post(
            "/api/notificacoes/push/inscricoes/", dados, content_type="application/json"
        ).status_code
        == 201
    )
    assert dono.get(url).json() == {"estado": "ativa"}
    resposta = outro.get(url)
    assert resposta.json() == {"estado": "indisponivel"}
    assert "no-store" in resposta["Cache-Control"]
    assert outro.delete(url).status_code == 204
    assert dono.get(url).json() == {"estado": "ativa"}
    assert dono.delete(url).status_code == 204
    assert dono.get(url).json() == {"estado": "revogada"}


@pytest.mark.django_db
def test_rnf10_identidade_cookie_divergente_bloqueia_mutacao(contas_fixture):
    cliente_a = cliente(contas_fixture.u["admin"])
    identidade_b = str(contas_fixture.u["membro"].pk)
    antes = Espaco.objects.count()
    resposta = cliente_a.post(
        "/api/grupos/",
        {"nome": "não criar"},
        content_type="application/json",
        HTTP_X_VARAL_IDENTIDADE_ESPERADA=identidade_b,
    )
    assert resposta.status_code == 409
    assert resposta["X-Varal-Identidade"] == str(contas_fixture.u["admin"].pk)
    assert "no-store" in resposta["Cache-Control"]
    assert Espaco.objects.count() == antes
    resposta = cliente_a.get(
        "/api/me/", HTTP_X_VARAL_IDENTIDADE_ESPERADA=str(contas_fixture.u["admin"].pk)
    )
    assert resposta.status_code == 200
    assert resposta["X-Varal-Identidade"] == str(contas_fixture.u["admin"].pk)


@pytest.mark.django_db
def test_rnf10_logout_atrasado_nao_encerra_outra_identidade(contas_fixture):
    cliente_b = cliente(contas_fixture.u["membro"])
    resposta = cliente_b.delete(
        "/api/auth/browser/v1/auth/session",
        HTTP_X_VARAL_IDENTIDADE_ESPERADA=str(contas_fixture.u["admin"].pk),
    )
    assert resposta.status_code == 409
    assert resposta["X-Varal-Identidade"] == str(contas_fixture.u["membro"].pk)
    assert cliente_b.get("/api/me/").status_code == 200


@pytest.mark.django_db(transaction=True)
def test_rn30_exportacao_501_contas_snapshot_sem_duplicar(settings, monkeypatch):
    import json
    from datetime import timedelta

    from django.contrib.auth import get_user_model
    from django.utils import timezone

    from apps.lancamentos.models import Lancamento
    from apps.privacidade.models import Exportacao
    from apps.privacidade.tasks import gerar_exportacao

    settings.CELERY_TASK_ALWAYS_EAGER = False
    user = get_user_model().objects.create_user(username="snapshot-test", email="snap@example.com")
    pessoal = user.espacos.get(tipo="pessoal")
    Lancamento.objects.bulk_create(
        [
            Lancamento(
                espaco=pessoal,
                criador=user,
                descricao=f"Conta {i}",
                valor_centavos=100,
                vencimento=timezone.localdate(),
            )
            for i in range(501)
        ]
    )
    job = Exportacao.objects.create(
        usuario=user,
        chave=uuid.uuid4(),
        corpo_hash="a" * 64,
        expira_em=timezone.now() + timedelta(hours=24),
    )
    objetos = {}

    class S3:
        def put_object(self, *, Key, Body, **kwargs):
            objetos[Key] = Body.read()

    monkeypatch.setattr("apps.privacidade.tasks.cliente", lambda: S3())
    monkeypatch.setattr("apps.privacidade.tasks.agendar", lambda *args: None)
    gerar_exportacao(str(job.pk))
    job.refresh_from_db()
    assert job.estado == "pronto"
    assert len(objetos) == 1
    dados = json.loads(next(iter(objetos.values())).removeprefix(b"VARAL-EXPORT-2\n"))
    assert dados["schema_version"] == 1
    assert len(dados["contas_pessoais"]) == 501
    assert len({item["id"] for item in dados["contas_pessoais"]}) == 501
    assert "password" not in dados["perfil"]


@pytest.mark.django_db(transaction=True)
def test_rn30_exclusao_registra_fora_do_banco_sem_apagar_grupo(contas_fixture, monkeypatch):
    from django.contrib.auth import get_user_model
    from django.contrib.sessions.models import Session

    from apps.privacidade.models import OperacaoExclusao
    from tests.conftest import REGISTROS

    monkeypatch.setattr("apps.privacidade.views.did_recently_reauthenticate", lambda request: True)
    user = contas_fixture.u["observador"]
    dono = user.pk
    c = cliente(user)
    chave_sessao = c.session.session_key
    intencao = c.post("/api/me/exclusao/intencoes/").json()
    response = c.delete(
        "/api/me/",
        {"id": intencao["id"], "segredo": intencao["segredo"], "confirmar": True},
        content_type="application/json",
    )
    assert response.status_code == 204, response.content
    assert response["X-Varal-Identidade"] == str(dono)
    assert "no-store" in response["Cache-Control"]
    assert not Session.objects.filter(session_key=chave_sessao).exists()
    assert not get_user_model().objects.filter(pk=dono).exists()
    assert Espaco.objects.filter(pk=contas_fixture.grupo.pk).exists()
    op = OperacaoExclusao.objects.get(owner_id=dono)
    # Published outside the database right after commit (ADR 0018).
    assert REGISTROS == [op]
    assert op.publicada_em is not None and op.intencao_id is not None


@pytest.mark.django_db(transaction=True)
def test_rn30_download_invalida_snapshot_apos_alteracao(monkeypatch):
    import io
    import json
    from datetime import timedelta

    from django.contrib.auth import get_user_model
    from django.utils import timezone

    from apps.privacidade.models import Exportacao
    from apps.privacidade.tasks import gerar_exportacao

    user = get_user_model().objects.create_user(username="baixar", email="baixar@example.com")
    job = Exportacao.objects.create(
        usuario=user,
        chave=uuid.uuid4(),
        corpo_hash="a" * 64,
        expira_em=timezone.now() + timedelta(hours=24),
    )
    objetos = {}

    class S3:
        def put_object(self, *, Key, Body, **kwargs):
            objetos[Key] = Body.read()

        def get_object(self, *, Key, **kwargs):
            class Bounded(io.BytesIO):
                def read(self, size=-1):
                    assert 0 < size <= 65536
                    return super().read(size)

            return {"Body": Bounded(objetos[Key])}

    monkeypatch.setattr("apps.privacidade.tasks.cliente", lambda: S3())
    monkeypatch.setattr("apps.privacidade.download.cliente", lambda publico=False: S3())
    monkeypatch.setattr("apps.privacidade.tasks.agendar", lambda *args: None)
    monkeypatch.setattr("apps.privacidade.views.did_recently_reauthenticate", lambda request: True)
    gerar_exportacao(str(job.pk))
    job.refresh_from_db()
    assert job.estado == "pronto"
    c = cliente(user)
    url = f"/api/me/exportacoes/{job.pk}/download/"
    response = c.get(url)
    assert response.status_code == 200
    assert json.loads(b"".join(response.streaming_content))["perfil"]["email"] == user.email
    chave_objeto = next(iter(objetos))
    original = objetos[chave_objeto]
    objetos[chave_objeto] = original + b"x"
    assert c.get(url).status_code == 409
    objetos[chave_objeto] = original
    user.nome = "Atualizado"
    user.save(update_fields=["nome"])
    assert c.get(url).status_code == 409


@pytest.mark.django_db
def test_rn30_prova_expirada_ao_entrar_barreira_nao_cria_job_ou_intencao(
    contas_fixture, monkeypatch
):
    from rest_framework.response import Response

    from apps.privacidade.models import Exportacao, IntencaoExclusao

    user = contas_fixture.u["admin"]
    c = cliente(user)
    calls = []

    def prova(request, *, travar=False):
        calls.append(travar)
        if travar:
            return Response(
                {"status": 401, "code": "reauth_required", "meta": {"is_authenticated": True}},
                status=401,
            )
        return None

    monkeypatch.setattr("apps.privacidade.views.sem_prova", prova)
    response = c.post(
        "/api/me/exportacoes/", {"chave": str(uuid.uuid4())}, content_type="application/json"
    )
    assert response.status_code == 401
    assert calls == [False, True]
    assert not Exportacao.objects.filter(usuario=user).exists()
    calls.clear()
    response = c.post("/api/me/exclusao/intencoes/")
    assert response.status_code == 401
    assert calls == [False, True]
    assert not IntencaoExclusao.objects.filter(usuario=user).exists()


@pytest.mark.django_db
def test_rnf10_rebind_push_so_depois_revogacao_terminal(contas_fixture, settings):
    settings.WEBPUSH_ENABLED = True
    settings.WEBPUSH_PUBLIC_KEY = "publica"
    settings.NOTIFICACOES_STORAGE_KEY = Fernet.generate_key().decode()
    a = cliente(contas_fixture.u["admin"])
    b = cliente(contas_fixture.u["membro"])
    dados = dados_push()
    antiga = dados["instalacao"]
    url = f"/api/notificacoes/push/instalacoes/{antiga}/"
    inscricoes = "/api/notificacoes/push/inscricoes/"
    assert a.post(inscricoes, dados, content_type="application/json").status_code == 201
    dados["instalacao"] = str(uuid.uuid4())
    assert b.post(inscricoes, dados, content_type="application/json").status_code == 409
    assert b.delete(url).status_code == 204
    assert a.get(url).json() == {"estado": "ativa"}
    assert a.delete(url).status_code == 204
    assert b.post(inscricoes, dados, content_type="application/json").status_code == 200
    assert a.delete(url).status_code == 204
    assert b.get(f"/api/notificacoes/push/instalacoes/{dados['instalacao']}/").json() == {
        "estado": "ativa"
    }


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("sem_agendamento_celery_concorrente")
def test_rn30_exclusoes_concorrentes_apagam_uma_vez(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor

    from django.contrib.auth import get_user_model
    from django.db import connection
    from django.test import Client

    from apps.privacidade.models import OperacaoExclusao

    monkeypatch.setattr("apps.privacidade.views.did_recently_reauthenticate", lambda request: True)
    user = get_user_model().objects.create_user(username="corrida", email="corrida@example.com")
    a = cliente(user)
    b = Client()
    b.cookies = a.cookies.copy()
    intent = a.post("/api/me/exclusao/intencoes/").json()
    payload = {"id": intent["id"], "segredo": intent["segredo"], "confirmar": True}

    def executar(client):
        try:
            return client.delete("/api/me/", payload, content_type="application/json").status_code
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        status = sorted(pool.map(executar, (a, b)))
    assert status[0] == 204 and status[1] in (401, 409)
    assert OperacaoExclusao.objects.filter(owner_id=user.pk).count() == 1


def test_rnf03_logs_nao_interpolam_tokens_e_traceback():
    import logging

    from config.logging_safe import SafeFilter, SafeFormatter

    segredo = "sentinela-token-ficticio"
    record = logging.LogRecord("django.request", logging.ERROR, __file__, 1, "%s", (segredo,), None)
    record.request = {"path": "/recuperar/" + segredo}
    assert SafeFilter().filter(record)
    assert "request" not in record.__dict__ and record.getMessage() == "application_log"
    saida = SafeFormatter().format(record)
    assert segredo not in saida
    assert '"level":"ERROR"' in saida


@pytest.mark.django_db(transaction=True)
def test_rn31_11_ips_concorrentes_limite_atomico(settings):
    from concurrent.futures import ThreadPoolExecutor
    from types import SimpleNamespace

    from rest_framework.exceptions import Throttled

    from apps.espacos.limite_convite import verificar

    requests = [
        SimpleNamespace(
            META={"REMOTE_ADDR": "198.51.100.42"}, user=SimpleNamespace(pk=uuid.uuid4())
        )
        for _ in range(11)
    ]

    def aceitar(request):
        try:
            verificar(request)
        except Throttled:
            return False
        return True

    with ThreadPoolExecutor(max_workers=11) as executor:
        resultados = list(executor.map(aceitar, requests))
    assert resultados.count(True) == 10
    assert resultados.count(False) == 1


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("sem_agendamento_celery_concorrente")
def test_rn30_worker_pdf_serializa_com_exclusao_sem_deadlock(monkeypatch, tmp_path):
    import threading
    from concurrent.futures import ThreadPoolExecutor

    from django.contrib.auth import get_user_model
    from django.db import connection

    from apps.boletos.models import DocumentoBoleto
    from apps.boletos.tasks import processar_pdf

    user = get_user_model().objects.create_user(username="pdf-race", email="pdf-race@example.com")
    doc = DocumentoBoleto.objects.create(
        espaco=user.espacos.get(tipo="pessoal"), criado_por=user, nome="a.pdf", tamanho=8
    )
    arquivo = tmp_path / "documento.pdf"
    arquivo.write_bytes(b"%PDF-1.4")
    locked, release, delete_started = threading.Event(), threading.Event(), threading.Event()
    original_save = DocumentoBoleto.save

    def save(instancia, *args, **kwargs):
        result = original_save(instancia, *args, **kwargs)
        if instancia.pk == doc.pk and instancia.estado == "lendo":
            locked.set()
            assert release.wait(15)
        return result

    class Storage:
        def save(self, key, content):
            return key

    monkeypatch.setattr(DocumentoBoleto, "save", save)
    monkeypatch.setattr("apps.boletos.tasks.spool", lambda pk: arquivo)
    monkeypatch.setattr("apps.boletos.tasks.armazenamento", lambda: Storage())
    monkeypatch.setattr("apps.boletos.tasks.agendar", lambda *args: None)
    monkeypatch.setattr("apps.boletos.tasks.extrair_isolado", lambda data: {"estado": "lido"})

    def worker():
        try:
            processar_pdf(str(doc.pk))
        finally:
            connection.close()

    def apagar():
        try:
            delete_started.set()
            user.delete()
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_worker = executor.submit(worker)
        assert locked.wait(15)
        future_delete = executor.submit(apagar)
        assert delete_started.wait(15)
        release.set()
        future_worker.result(timeout=30)
        future_delete.result(timeout=30)
    assert not get_user_model().objects.filter(pk=user.pk).exists()
    assert not DocumentoBoleto.objects.filter(pk=doc.pk).exists()


def test_rn30_schema_delete_tem_corpo_tipado():
    from config.schema import CombinedSchemaGenerator

    schema = CombinedSchemaGenerator().get_schema(public=True)
    body = schema["paths"]["/api/me/"]["delete"]["requestBody"]
    assert body["required"] is True
    ref = body["content"]["application/json"]["schema"]["$ref"]
    componente = schema["components"]["schemas"][ref.rsplit("/", 1)[-1]]
    assert set(componente["required"]) == {"id", "segredo", "confirmar"}


@pytest.mark.django_db(transaction=True)
def test_rnf10_google_ticket_so_consumido_pela_sessao_e_tentativa_validas(settings):
    from urllib.parse import parse_qs, urlsplit

    from django.contrib.auth import get_user_model

    from tests.test_autenticacao import browser, finish_google, google_settings

    google_settings(settings)
    tentativa = str(uuid.uuid4())
    cliente_google = browser()
    resposta = cliente_google.post(
        "/api/auth/browser/v1/auth/provider/redirect",
        {
            "provider": "google",
            "process": "login",
            "callback_url": f"http://localhost:3000/entrar/retorno?tentativa={tentativa}",
            "csrfmiddlewaretoken": cliente_google.cookies["csrftoken"].value,
        },
        HTTP_HOST="localhost:3000",
    )
    assert resposta.status_code == 302
    estado = parse_qs(urlsplit(resposta["Location"]).query)["state"][0]
    resposta = finish_google(cliente_google, estado)
    assert resposta.status_code == 302
    parametros = parse_qs(urlsplit(resposta["Location"]).query)
    assert parametros["tentativa"] == [tentativa]
    ticket = parametros["ticket"][0]
    alvo = "/api/auth/google/tickets/consumir/"
    outro = get_user_model().objects.create_user(
        username="outro-google", email="outro-google@example.com"
    )
    c_outro = cliente(outro)
    assert (
        c_outro.post(
            alvo, {"ticket": ticket, "tentativa": tentativa}, content_type="application/json"
        ).status_code
        == 409
    )
    assert (
        cliente_google.post(
            alvo,
            {"ticket": ticket, "tentativa": str(uuid.uuid4())},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=cliente_google.cookies["csrftoken"].value,
        ).status_code
        == 409
    )
    resposta = cliente_google.post(
        alvo,
        {"ticket": ticket, "tentativa": tentativa},
        content_type="application/json",
        HTTP_X_CSRFTOKEN=cliente_google.cookies["csrftoken"].value,
    )
    assert resposta.status_code == 200
    assert resposta.json()["id"] != str(outro.pk)
    assert (
        cliente_google.post(
            alvo,
            {"ticket": ticket, "tentativa": tentativa},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=cliente_google.cookies["csrftoken"].value,
        ).status_code
        == 409
    )


def test_rn31_proxy_so_aceita_xff_de_peer_confiavel(settings):
    from types import SimpleNamespace

    from apps.espacos.limite_convite import LimitadorIndisponivel, endereco

    settings.VARAL_TRUSTED_PROXY_COUNT = 1
    settings.VARAL_TRUSTED_PROXY_CIDRS = ("192.0.2.10/32",)
    externo = SimpleNamespace(
        META={"REMOTE_ADDR": "198.51.100.4", "HTTP_X_FORWARDED_FOR": "203.0.113.10"}
    )
    proxy = SimpleNamespace(
        META={"REMOTE_ADDR": "192.0.2.10", "HTTP_X_FORWARDED_FOR": "2001:db8::10"}
    )
    assert endereco(externo) == "198.51.100.4"
    assert endereco(proxy) == "2001:db8::10"
    proxy.META["HTTP_X_FORWARDED_FOR"] = "203.0.113.10, 198.51.100.4"
    with pytest.raises(LimitadorIndisponivel):
        endereco(proxy)


def test_rn31_redis_indisponivel_nao_permite_aceite(monkeypatch):
    from types import SimpleNamespace

    import redis

    from apps.espacos.limite_convite import LimitadorIndisponivel, verificar

    def indisponivel(*args, **kwargs):
        raise redis.ConnectionError()

    monkeypatch.setattr("apps.espacos.limite_convite.redis.Redis.from_url", indisponivel)
    request = SimpleNamespace(
        META={"REMOTE_ADDR": "198.51.100.2"}, user=SimpleNamespace(pk=uuid.uuid4())
    )
    with pytest.raises(LimitadorIndisponivel) as exc:
        verificar(request)
    assert exc.value.status_code == 503


@pytest.mark.django_db(transaction=True)
def test_rn32_exclusao_bloqueada_preserva_intencao_sem_registro(contas_fixture, monkeypatch):
    from apps.contas_usuario.models import Usuario
    from apps.privacidade.models import IntencaoExclusao, OperacaoExclusao
    from tests.conftest import REGISTROS

    user = contas_fixture.u["membro"]
    conta = test_contas.restrita(user, contas_fixture.grupo, descricao="segredo-restrito")
    monkeypatch.setattr("apps.privacidade.views.did_recently_reauthenticate", lambda request: True)
    c = cliente(user)
    intencao = c.post("/api/me/exclusao/intencoes/").json()
    resposta = c.delete(
        "/api/me/",
        {"id": intencao["id"], "segredo": intencao["segredo"], "confirmar": True},
        content_type="application/json",
    )
    assert resposta.status_code == 409
    assert "segredo-restrito" not in resposta.content.decode()
    assert str(conta.pk) not in resposta.content.decode()
    assert REGISTROS == []
    assert not OperacaoExclusao.objects.filter(owner_id=user.pk).exists()
    assert Usuario.objects.filter(pk=user.pk).exists()
    assert IntencaoExclusao.objects.get(pk=intencao["id"]).consumida_em is None
    assert c.get("/api/me/").status_code == 200


@pytest.mark.django_db
def test_rnf03_erro_csrf_nao_registra_token_em_log(contas_fixture, caplog, capsys):
    import logging

    from django.test import Client

    sentinela = "segredo-ficticio-na-url"
    c = Client(enforce_csrf_checks=True)
    c.force_login(contas_fixture.u["membro"])
    with caplog.at_level(logging.WARNING):
        resposta = c.post(f"/api/convites/{sentinela}/aceitar/")
    assert resposta.status_code == 403
    assert sentinela not in caplog.text
    assert sentinela not in capsys.readouterr().err


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("sem_agendamento_celery_concorrente")
def test_rn32_remocao_e_exclusao_serializam(contas_fixture, monkeypatch):
    import threading
    from concurrent.futures import ThreadPoolExecutor

    from django.db import connection

    from apps.contas_usuario.models import Usuario
    from apps.espacos import servicos as grupos
    from apps.espacos.acesso import quem_ve
    from apps.lancamentos.models import Historico
    from apps.privacidade import exclusao

    user = contas_fixture.u["membro"]
    user_id = user.pk
    observador_id = contas_fixture.u["observador"].pk
    conta = test_contas.restrita(
        user, contas_fixture.grupo, acesso=[observador_id], pagador=user_id
    )
    # The deletion holds the barrier while the removal runs in parallel and must wait for it.
    na_barreira, liberar = threading.Event(), threading.Event()
    real_barreira = exclusao.barreira

    def barreira():
        real_barreira()
        if threading.current_thread().name == "apagar":
            na_barreira.set()
            assert liberar.wait(10)

    monkeypatch.setattr(exclusao, "barreira", barreira)

    def apagar():
        threading.current_thread().name = "apagar"
        try:
            return user.delete()
        finally:
            connection.close()

    def remover():
        try:
            return grupos.remover_membro(contas_fixture.grupo, contas_fixture.m["membro"].pk)
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        excluir = executor.submit(apagar)
        assert na_barreira.wait(10)
        remocao = executor.submit(remover)
        liberar.set()
        assert isinstance(excluir.result(timeout=10), tuple)
        remocao.exception(timeout=10)  # the member is already gone; it must not undo anything
    assert not Usuario.objects.filter(pk=user_id).exists()
    conta.refresh_from_db()
    assert conta.criador_id is None and conta.status == "pendente"
    assert quem_ve(conta) == {observador_id}
    assert conta.historico.filter(acao=Historico.Acao.PAGADOR_REMOVIDO).count() == 1


@pytest.mark.django_db(transaction=True)
def test_rn30_download_501_documentos_lotes_e_manifesto_adulterado(monkeypatch):
    import io
    import json
    from datetime import timedelta

    from django.contrib.auth import get_user_model
    from django.utils import timezone

    from apps.boletos.models import DocumentoBoleto
    from apps.privacidade.models import Exportacao, ParteExportacao
    from apps.privacidade.tasks import gerar_exportacao

    user = get_user_model().objects.create_user(username="pdfs501", email="pdfs501@example.com")
    pessoal = user.espacos.get(tipo="pessoal")
    DocumentoBoleto.objects.bulk_create(
        [
            DocumentoBoleto(
                espaco=pessoal, criado_por=user, estado="lido", nome="arquivo.pdf", tamanho=1
            )
            for _ in range(501)
        ]
    )
    job = Exportacao.objects.create(
        usuario=user,
        chave=uuid.uuid4(),
        corpo_hash="a" * 64,
        expira_em=timezone.now() + timedelta(hours=24),
    )
    objetos = {}

    class S3:
        def put_object(self, *, Key, Body, **kwargs):
            objetos[Key] = Body.read()

        def get_object(self, *, Key, **kwargs):
            return {"Body": io.BytesIO(objetos[Key])}

        def generate_presigned_url(self, method, *, Params, ExpiresIn):
            assert method == "get_object" and ExpiresIn == 60
            return "https://example.invalid/" + Params["Key"]

    monkeypatch.setattr("apps.privacidade.tasks.cliente", lambda: S3())
    monkeypatch.setattr("apps.privacidade.download.cliente", lambda publico=False: S3())
    monkeypatch.setattr("apps.privacidade.tasks.agendar", lambda *args: None)
    monkeypatch.setattr("apps.privacidade.views.did_recently_reauthenticate", lambda request: True)
    gerar_exportacao(str(job.pk))
    job.refresh_from_db()
    assert job.estado == "pronto"
    assert job.manifestos["documentos_pdf"]["count"] == 501
    partes = ParteExportacao.objects.filter(exportacao=job, categoria="documentos_pdf")
    assert sorted(len(parte.dados) for parte in partes) == [1, 500]
    c = cliente(user)
    url = f"/api/me/exportacoes/{job.pk}/download/"
    resposta = c.get(url)
    assert resposta.status_code == 200
    documentos = json.loads(b"".join(resposta.streaming_content))["documentos_pdf"]
    assert len(documentos) == len({item["id"] for item in documentos}) == 501
    assert all(item["url_validade_segundos"] == 60 for item in documentos)
    partes.order_by("cursor").first().delete()
    assert c.get(url).status_code == 409


@pytest.mark.django_db(transaction=True)
def test_rn30_reaplicar_exclusoes_apos_restauracao_e_idempotente(contas_fixture, monkeypatch):
    import io
    import json
    from unittest.mock import MagicMock

    from django.core.management import call_command
    from django.core.management.base import CommandError

    from apps.contas_usuario.models import Usuario

    volta = contas_fixture.u["observador"]  # came back with an older dump
    bloqueado = contas_fixture.u["admin"]  # restored as the group's only admin
    sumido = uuid.uuid4()  # already absent from the restored database
    donos = [volta.pk, bloqueado.pk, sumido]
    s3 = MagicMock()
    s3.get_paginator.return_value.paginate.return_value = [
        {"Contents": [{"Key": f"exclusoes/{i}.json"} for i in range(len(donos))]}
    ]
    s3.get_object.side_effect = lambda Bucket, Key: {
        "Body": io.BytesIO(json.dumps({"owner_id": str(donos[int(Key[10:-5])])}).encode())
    }
    monkeypatch.setattr(
        "apps.privacidade.management.commands.reaplicar_exclusoes.cliente", lambda: s3
    )
    saida = io.StringIO()
    with pytest.raises(CommandError, match=str(bloqueado.pk)):
        call_command("reaplicar_exclusoes", stdout=saida)
    assert "3 registros, 1 contas apagadas de novo." in saida.getvalue()
    assert not Usuario.objects.filter(pk=volta.pk).exists()
    assert Usuario.objects.filter(pk=bloqueado.pk).exists()
    with pytest.raises(CommandError):
        call_command("reaplicar_exclusoes", stdout=saida)
    assert "3 registros, 0 contas apagadas de novo." in saida.getvalue()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mudanca", ["revisao", "sessao", "ttl"])
@pytest.mark.usefixtures("sem_agendamento_celery_concorrente")
def test_rn30_download_concorrente_invalida_autorizacao_entre_lotes(monkeypatch, mudanca):
    import io
    import threading
    from datetime import timedelta

    from django.contrib.auth import get_user_model
    from django.contrib.sessions.models import Session
    from django.db import close_old_connections, connection
    from django.utils import timezone

    from apps.boletos.models import DocumentoBoleto
    from apps.privacidade import download
    from apps.privacidade.models import Exportacao
    from apps.privacidade.tasks import gerar_exportacao

    user = get_user_model().objects.create_user(
        username=f"lote-{mudanca}", email=f"{mudanca}@example.com"
    )
    pessoal = user.espacos.get(tipo="pessoal")
    DocumentoBoleto.objects.bulk_create(
        [
            DocumentoBoleto(
                espaco=pessoal, criado_por=user, estado="lido", nome="arquivo.pdf", tamanho=1
            )
            for _ in range(501)
        ]
    )
    job = Exportacao.objects.create(
        usuario=user,
        chave=uuid.uuid4(),
        corpo_hash="a" * 64,
        expira_em=timezone.now() + timedelta(hours=24),
    )
    objetos = {}

    class S3:
        def put_object(self, *, Key, Body, **kwargs):
            objetos[Key] = Body.read()

        def get_object(self, *, Key, **kwargs):
            return {"Body": io.BytesIO(objetos[Key])}

    monkeypatch.setattr("apps.privacidade.tasks.cliente", lambda: S3())
    monkeypatch.setattr(download, "cliente", lambda publico=False: S3())
    monkeypatch.setattr("apps.privacidade.tasks.agendar", lambda *args: None)
    monkeypatch.setattr("apps.privacidade.views.did_recently_reauthenticate", lambda request: True)
    gerar_exportacao(str(job.pk))
    job.refresh_from_db()
    assert job.estado == "pronto"
    c = cliente(user)
    session_key = c.session.session_key
    pausa, liberar = threading.Event(), threading.Event()
    original = download.linha_manifesto
    chamadas = 0

    def linha(item):
        nonlocal chamadas
        assert not connection.in_atomic_block
        chamadas += 1
        if chamadas == 500:
            pausa.set()
            assert liberar.wait(15)
        return original(item)

    monkeypatch.setattr(download, "linha_manifesto", linha)
    resultados = []

    def baixar():
        close_old_connections()
        try:
            resultados.append(c.get(f"/api/me/exportacoes/{job.pk}/download/"))
        finally:
            close_old_connections()

    thread = threading.Thread(target=baixar)
    thread.start()
    try:
        assert pausa.wait(15), "download não chegou ao limite do primeiro lote"
        if mudanca == "revisao":
            user.nome = "Alterado durante exportação"
            user.save(update_fields=["nome"])
        elif mudanca == "sessao":
            Session.objects.filter(session_key=session_key).delete()
        else:
            Exportacao.objects.filter(pk=job.pk).update(
                expira_em=timezone.now() - timedelta(seconds=1)
            )
    finally:
        liberar.set()
        thread.join(15)
    assert not thread.is_alive()
    assert len(resultados) == 1
    assert resultados[0].status_code == (401 if mudanca == "sessao" else 409)
    assert not getattr(resultados[0], "streaming", False)


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("sem_agendamento_celery_concorrente")
def test_rn30_exportacao_lease_expirado_put_tardio_nao_publica(monkeypatch):
    import threading
    from datetime import timedelta

    from django.contrib.auth import get_user_model
    from django.db import close_old_connections
    from django.utils import timezone

    from apps.privacidade.models import Exportacao, LimpezaExportacao
    from apps.privacidade.tasks import chave_objeto, gerar_exportacao

    user = get_user_model().objects.create_user(username="put-tardio", email="put@example.com")
    job = Exportacao.objects.create(
        usuario=user,
        chave=uuid.uuid4(),
        corpo_hash="a" * 64,
        expira_em=timezone.now() + timedelta(hours=24),
    )
    pausado, liberar = threading.Event(), threading.Event()
    objetos = {}
    chamadas = []

    class S3:
        def put_object(self, *, Key, Body, **kwargs):
            dados = Body.read()
            chamadas.append(Key)
            if len(chamadas) == 1:
                pausado.set()
                assert liberar.wait(15)
            objetos[Key] = dados

    monkeypatch.setattr("apps.privacidade.tasks.cliente", lambda: S3())
    monkeypatch.setattr("apps.privacidade.tasks.agendar", lambda *args: None)

    def primeira():
        close_old_connections()
        try:
            gerar_exportacao(str(job.pk))
        finally:
            close_old_connections()

    thread = threading.Thread(target=primeira)
    thread.start()
    try:
        assert pausado.wait(15)
        job.refresh_from_db()
        antiga, tentativa_antiga = job.objeto_id, job.tentativa
        Exportacao.objects.filter(pk=job.pk).update(lease_ate=timezone.now() - timedelta(seconds=1))
        gerar_exportacao(str(job.pk))
        job.refresh_from_db()
        assert job.estado == "pronto"
        assert job.objeto_id != antiga and job.tentativa != tentativa_antiga
        vencedora = job.objeto_id
    finally:
        liberar.set()
        thread.join(15)
    assert not thread.is_alive()
    job.refresh_from_db()
    assert job.estado == "pronto" and job.objeto_id == vencedora
    assert set(objetos) == {chave_objeto(antiga), chave_objeto(vencedora)}
    assert LimpezaExportacao.objects.filter(pk=antiga).exists()


@pytest.mark.django_db(transaction=True)
def test_rn30_recuperar_comprovantes_barreira_apenas_no_update(monkeypatch):
    from django.core.management import call_command
    from django.db import connection

    from apps.pagamentos.management.commands import recuperar_comprovantes as command

    chamada = []
    original = command.barreira

    def guardar():
        assert connection.in_atomic_block
        chamada.append("barreira")
        original()

    def fora():
        assert not connection.in_atomic_block
        chamada.append("fora")

    monkeypatch.setattr(command, "barreira", guardar)
    monkeypatch.setattr(command, "limpar_expirados", fora)
    monkeypatch.setattr(command, "recuperar_limpeza", fora)
    call_command("recuperar_comprovantes")
    assert chamada == ["barreira", "fora", "fora"]
