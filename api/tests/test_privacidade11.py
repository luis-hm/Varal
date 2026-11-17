import hashlib
import hmac
import uuid

import pytest
from cryptography.fernet import Fernet
from django.db import transaction

from apps.espacos.models import Espaco
from apps.notificacoes.witness import testemunhar as _testemunhar_real
from apps.privacidade.journal import JournalIndisponivel, canonico, validar_recibo
from apps.privacidade.models import RevisaoExportacao
from tests import test_contas
from tests.test_grupos import cliente
from tests.test_notificacoes import dados_push

contas_fixture = test_contas.f


def test_rn30_receipt_journal_validado_e_alteracao_recusada(settings, tmp_path):
    key = b"a" * 32
    arquivo = tmp_path / "receipt-key"
    arquivo.write_bytes(key + b"\n")
    settings.JOURNAL_RECEIPT_KEY_FILE = str(arquivo)
    settings.JOURNAL_RECEIPT_KEY_ID = "receipt-v1"
    mensagem = {
        "version": 1,
        "epoch": str(uuid.uuid4()),
        "operation_id": str(uuid.uuid4()),
        "owner_id": str(uuid.uuid4()),
        "kind": "PREPARE",
        "fence": 1,
        "prepare_seq": None,
    }
    recibo = {
        **mensagem,
        "request_digest": hashlib.sha256(canonico(mensagem)).hexdigest(),
        "seq": 1,
        "record_mac": "a" * 64,
        "checkpoint_seq": 1,
        "checkpoint_mac": "b" * 64,
        "receipt_key_id": "receipt-v1",
    }
    recibo["receipt_mac"] = hmac.new(
        key, b"varal-journal-receipt-v1\n" + canonico(recibo), hashlib.sha256
    ).hexdigest()
    assert validar_recibo(recibo, mensagem) == recibo
    recibo["owner_id"] = str(uuid.uuid4())
    with pytest.raises(JournalIndisponivel):
        validar_recibo(recibo, mensagem)


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
def test_rn30_exclusao_tem_prepare_e_commit_sem_apagar_grupo(monkeypatch):
    from django.contrib.auth import get_user_model

    from apps.privacidade.models import OperacaoExclusao

    monkeypatch.setattr("apps.privacidade.views.did_recently_reauthenticate", lambda request: True)
    eventos = []

    def registrar(operation_id, owner_id, kind, fence, prepare_seq=None):
        eventos.append(kind)
        return {"seq": 1 if kind == "PREPARE" else 2}

    monkeypatch.setattr("apps.privacidade.exclusao.registrar", registrar)
    user = get_user_model().objects.create_user(username="excluir-test", email="delete@example.com")
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
    from django.contrib.sessions.models import Session

    assert not Session.objects.filter(session_key=chave_sessao).exists()
    assert not get_user_model().objects.filter(pk=dono).exists()
    op = OperacaoExclusao.objects.get(owner_id=dono)
    assert op.estado == "commitada"
    assert eventos == ["PREPARE", "COMMIT"]


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
def test_rn30_commit_nunca_vira_abort_em_exclusoes_concorrentes(monkeypatch):
    import threading
    from concurrent.futures import ThreadPoolExecutor

    from django.contrib.auth import get_user_model
    from django.db import connection
    from django.test import Client

    from apps.privacidade import exclusao
    from apps.privacidade.models import OperacaoExclusao

    monkeypatch.setattr("apps.privacidade.views.did_recently_reauthenticate", lambda request: True)
    user = get_user_model().objects.create_user(username="corrida", email="corrida@example.com")
    a = cliente(user)
    b = Client()
    b.cookies = a.cookies.copy()
    intent = a.post("/api/me/exclusao/intencoes/").json()
    payload = {"id": intent["id"], "segredo": intent["segredo"], "confirmar": True}
    prontos = threading.Barrier(2)
    b_pronto = threading.Event()
    committed = threading.Event()
    b_publicou = threading.Event()
    mensagens = []
    real_publicar = exclusao.publicar_terminal
    real_barreira = exclusao.barreira
    contagens = {}

    def registrar(operation_id, owner_id, kind, fence, prepare_seq=None):
        if kind == "PREPARE":
            prontos.wait(timeout=15)
            return {"seq": 1}
        mensagens.append(kind)
        return {"seq": 2}

    def publicar(op_id):
        if threading.current_thread().name == "delete-a":
            committed.set()
            assert b_publicou.wait(15)
            real_publicar(op_id)
        else:
            try:
                real_publicar(op_id)
            finally:
                b_publicou.set()

    def barreira():
        nome = threading.current_thread().name
        contagens[nome] = contagens.get(nome, 0) + 1
        if contagens[nome] == 2:
            if nome == "delete-a":
                assert b_pronto.wait(15)
            else:
                b_pronto.set()
                assert committed.wait(15)
        real_barreira()

    monkeypatch.setattr(exclusao, "registrar", registrar)
    monkeypatch.setattr(exclusao, "publicar_terminal", publicar)
    monkeypatch.setattr(exclusao, "barreira", barreira)

    def executar(client, nome):
        threading.current_thread().name = nome
        try:
            return client.delete("/api/me/", payload, content_type="application/json").status_code
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futuro_a = pool.submit(executar, a, "delete-a")
        futuro_b = pool.submit(executar, b, "delete-b")
        status_a, status_b = futuro_a.result(timeout=30), futuro_b.result(timeout=30)
    op = OperacaoExclusao.objects.get(owner_id=user.pk)
    assert status_a == 204
    assert status_b in (401, 409)
    assert op.estado == "commitada"
    assert mensagens and set(mensagens) == {"COMMIT"}


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


def test_rn30_wal_ack_mac_e_segmento_validados():
    import json

    from apps.notificacoes.witness import WitnessIndisponivel, _canonico, _validar

    key = b"k" * 32
    segmento = "000000010000000000000001"
    epoch = str(uuid.uuid4())
    ack = {
        "version": 1,
        "epoch": epoch,
        "segment": segmento,
        "timeline": segmento[:8],
        "plaintext_sha256": "a" * 64,
        "ciphertext_sha256": "b" * 64,
        "nonce": "c" * 24,
        "key_id": "wal-v1",
    }
    ack["mac"] = hmac.new(
        key, b"varal-wal-witness-v1\n" + _canonico(ack), hashlib.sha256
    ).hexdigest()
    _validar(json.dumps(ack).encode(), segmento, epoch, key)
    with pytest.raises(WitnessIndisponivel):
        _validar(json.dumps(ack).encode(), "000000010000000000000002", epoch, key)
    ack["ciphertext_sha256"] = "d" * 64
    with pytest.raises(WitnessIndisponivel):
        _validar(json.dumps(ack).encode(), segmento, epoch, key)


@pytest.mark.django_db
def test_rnf07_falha_wal_witness_nao_envia_email(contas_fixture, monkeypatch):
    from datetime import UTC, datetime, timedelta
    from unittest.mock import Mock, patch

    from django.utils import timezone

    from apps.notificacoes import servicos, witness
    from apps.notificacoes.entregas import enviar_email_entrega
    from apps.notificacoes.models import EntregaNotificacao

    agora = datetime(2026, 11, 16, 12, 0, tzinfo=UTC)
    with patch("django.utils.timezone.now", return_value=agora) as relogio:
        test_contas.nova(
            contas_fixture.u["admin"],
            contas_fixture.grupo,
            pagador=contas_fixture.u["membro"].pk,
            vencimento=timezone.localdate() + timedelta(days=3),
        )
        servicos.varrer_lembretes()
        entrega = EntregaNotificacao.objects.filter(canal="email").first()
        assert entrega is not None
        enviar = Mock()
        monkeypatch.setattr("apps.notificacoes.transportes.enviar_email", enviar)
        monkeypatch.setattr(
            "apps.notificacoes.witness.testemunhar",
            lambda: (_ for _ in ()).throw(witness.WitnessIndisponivel()),
        )
        for indice, minutos in enumerate((0, 2, 8), start=1):
            relogio.return_value = agora + timedelta(minutes=minutos)
            enviar_email_entrega(entrega.pk)
            entrega.refresh_from_db()
            assert entrega.tentativas == indice
            assert entrega.estado == ("falhou" if indice == 3 else "pendente")
            assert entrega.resultado == "witness_indisponivel"
        enviar.assert_not_called()


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


@pytest.mark.django_db
def test_rnf07_witness_nao_pode_operar_dentro_de_transacao():
    with pytest.raises(RuntimeError, match="outside"):
        _testemunhar_real()


@pytest.mark.django_db(transaction=True)
def test_rnf07_witness_apos_commit_e_revogacao_antes_envio(contas_fixture, monkeypatch):
    from datetime import UTC, datetime, timedelta
    from unittest.mock import Mock, patch

    from django.db import connection
    from django.utils import timezone

    from apps.notificacoes import servicos
    from apps.notificacoes.entregas import enviar_email_entrega
    from apps.notificacoes.models import EntregaNotificacao

    agora = datetime(2026, 11, 16, 12, 0, tzinfo=UTC)
    with patch("django.utils.timezone.now", return_value=agora):
        test_contas.nova(
            contas_fixture.u["admin"],
            contas_fixture.grupo,
            pagador=contas_fixture.u["membro"].pk,
            vencimento=timezone.localdate() + timedelta(days=3),
        )
        servicos.varrer_lembretes()
        entrega = EntregaNotificacao.objects.filter(canal="email").first()
        assert entrega is not None
        enviar = Mock()

        def witness():
            assert not connection.in_atomic_block
            atual = EntregaNotificacao.objects.get(pk=entrega.pk)
            assert atual.estado == "iniciada" and atual.token is not None
            usuario = atual.notificacao.destinatario
            usuario.prefs_notificacao = {"email": False}
            usuario.save(update_fields=["prefs_notificacao"])

        monkeypatch.setattr("apps.notificacoes.witness.testemunhar", witness)
        monkeypatch.setattr("apps.notificacoes.transportes.enviar_email", enviar)
        enviar_email_entrega(entrega.pk)
        entrega.refresh_from_db()
        assert entrega.estado == "descartada"
        enviar.assert_not_called()


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


def test_rn30_restore_journal_cadeia_e_prepare_pendente(settings, monkeypatch, tmp_path):

    from apps.privacidade import restore
    from apps.privacidade.journal import JournalIndisponivel, canonico

    key = b"w" * 32
    keyfile = tmp_path / "key"
    keyfile.write_bytes(key)
    epoch, owner, operacao = (str(uuid.uuid4()) for _ in range(3))
    settings.JOURNAL_EPOCH = epoch
    settings.JOURNAL_CHECKPOINT_KEY_ID = "checkpoint-v1"
    settings.JOURNAL_CHECKPOINT_KEY_FILE = str(keyfile)
    settings.JOURNAL_CHAIN_KEY_ID = "chain-v1"
    settings.JOURNAL_CHAIN_KEY_FILE = str(keyfile)

    def mac(domain, value):
        return hmac.new(key, domain + b"\n" + canonico(value), hashlib.sha256).hexdigest()

    def checkpoint(seq, digest):
        item = {
            "version": 1,
            "epoch": epoch,
            "seq": seq,
            "mac": digest,
            "checkpoint_key_id": "checkpoint-v1",
        }
        item["checkpoint_mac"] = mac(b"varal-journal-checkpoint-v1", item)
        return item

    def registro(tipo, seq, anterior, prepare):
        item = {
            "version": 1,
            "epoch": epoch,
            "operation_id": operacao,
            "owner_id": owner,
            "kind": tipo,
            "fence": 1,
            "prepare_seq": prepare,
            "seq": seq,
            "recorded_at": "2026-11-16T00:00:00Z",
            "prev_mac": anterior,
            "chain_key_id": "chain-v1",
        }
        item["mac"] = mac(b"varal-journal-record-v1", item)
        return item

    primeiro = registro("PREPARE", 1, "0" * 64, None)
    segundo = registro("COMMIT", 2, primeiro["mac"], 1)
    ancora = checkpoint(0, "0" * 64)
    monkeypatch.setattr(
        restore,
        "ler_pagina",
        lambda seq: {"records": [primeiro, segundo], "checkpoint": checkpoint(2, segundo["mac"])},
    )
    assert restore.validar_journal(ancora) == {owner}
    monkeypatch.setattr(
        restore,
        "ler_pagina",
        lambda seq: {"records": [primeiro], "checkpoint": checkpoint(1, primeiro["mac"])},
    )
    with pytest.raises(JournalIndisponivel):
        restore.validar_journal(ancora)
    segundo["owner_id"] = str(uuid.uuid4())
    monkeypatch.setattr(
        restore,
        "ler_pagina",
        lambda seq: {"records": [primeiro, segundo], "checkpoint": checkpoint(2, segundo["mac"])},
    )
    with pytest.raises(JournalIndisponivel):
        restore.validar_journal(ancora)


def test_rn30_restore_sem_fence_permanece_fechado(settings, monkeypatch, tmp_path):
    from django.core.management import call_command
    from django.core.management.base import CommandError
    from django.test import Client

    settings.VARAL_RESTORE_MODE = True
    ancora = tmp_path / "checkpoint.json"
    ancora.write_bytes(b"{}")

    def indisponivel(nonce):
        raise JournalIndisponivel()

    monkeypatch.setattr(
        "apps.privacidade.management.commands.reconciliar_exclusoes_restore.ler_fence",
        indisponivel,
    )
    with pytest.raises(CommandError, match="sem validação completa"):
        call_command("reconciliar_exclusoes_restore", "--ancora", str(ancora), "--isolado")
    assert Client().get("/api/health/").status_code == 503


def test_rnf07_restore_bloqueia_witness_de_transporte(settings):
    from apps.notificacoes.witness import WitnessIndisponivel

    settings.VARAL_RESTORE_MODE = True
    with pytest.raises(WitnessIndisponivel):
        _testemunhar_real()


@pytest.mark.django_db(transaction=True)
def test_rn32_exclusao_bloqueia_antes_de_prepare_e_preserva_intencao(contas_fixture, monkeypatch):
    from apps.contas_usuario.models import Usuario
    from apps.privacidade.models import IntencaoExclusao

    user = contas_fixture.u["membro"]
    conta = test_contas.restrita(user, contas_fixture.grupo, descricao="segredo-restrito")
    monkeypatch.setattr("apps.privacidade.views.did_recently_reauthenticate", lambda request: True)
    chamadas = []
    monkeypatch.setattr(
        "apps.privacidade.exclusao.registrar", lambda *args: chamadas.append(args) or {"seq": 1}
    )
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
    assert chamadas == []
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
def test_rn32_remocao_vence_enquanto_exclusao_aguarda_prepare(contas_fixture, monkeypatch):
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
    aguardando, liberar = threading.Event(), threading.Event()
    kinds = []

    def registrar(operation_id, owner_id, kind, fence, prepare_seq=None):
        kinds.append(kind)
        if kind == "PREPARE":
            assert not connection.in_atomic_block
            aguardando.set()
            assert liberar.wait(10)
            return {"seq": 1}
        return {"seq": 2}

    monkeypatch.setattr(exclusao, "registrar", registrar)

    def apagar():
        try:
            return user.delete()
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(apagar)
        assert aguardando.wait(10)
        try:
            assert (
                grupos.remover_membro(contas_fixture.grupo, contas_fixture.m["membro"].pk) is None
            )
        finally:
            liberar.set()
        assert isinstance(future.result(timeout=10), tuple)
    assert not Usuario.objects.filter(pk=user_id).exists()
    conta.refresh_from_db()
    assert conta.criador_id is None and conta.status == "pendente"
    assert quem_ve(conta) == {observador_id}
    assert conta.historico.filter(acao=Historico.Acao.PAGADOR_REMOVIDO).count() == 1
    assert kinds == ["PREPARE", "COMMIT"]


def test_rn30_fence_selado_exige_recibo_e_desafio_autenticos(settings, tmp_path):
    import secrets

    from apps.privacidade.journal import JournalIndisponivel, _mac, canonico
    from apps.privacidade.restore import validar_fence

    key = b"a" * 32
    path = tmp_path / "receipt"
    path.write_bytes(key)
    settings.JOURNAL_RECEIPT_KEY_FILE = str(path)
    settings.JOURNAL_RECEIPT_KEY_ID = "receipt-v1"
    settings.JOURNAL_EPOCH = str(uuid.uuid4())
    nonce = secrets.token_hex(32)
    fence = {
        "version": 1,
        "epoch": settings.JOURNAL_EPOCH,
        "fence_id": str(uuid.uuid4()),
        "state": "sealed",
        "seq": 0,
        "record_mac": "0" * 64,
        "key_id": "receipt-v1",
    }
    fence["mac"] = _mac(key, b"varal-journal-fence-v1\n", canonico(fence))
    fresh = {**{k: v for k, v in fence.items() if k != "mac"}, "nonce": nonce}
    fresh["mac"] = _mac(key, b"varal-journal-fence-read-v1\n", canonico(fresh))
    envelope = {"fence": fence, "freshness": fresh}
    assert validar_fence(envelope, nonce) == fence
    with pytest.raises(JournalIndisponivel):
        validar_fence(envelope, secrets.token_hex(32))
    fence["seq"] = 1
    with pytest.raises(JournalIndisponivel):
        validar_fence(envelope, nonce)


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
def test_rn30_restore_guardas_conjunto_bloqueiam_dois_ultimos_admins(contas_fixture):
    from apps.espacos.servicos import UltimoAdmin
    from apps.privacidade.restore import guardas_conjunto
    from apps.solicitacoes.coordenacao import barreira

    f = contas_fixture
    f.m["membro"].papel = "admin"
    f.m["membro"].save(update_fields=["papel"])
    alvos = {f.u["admin"].pk, f.u["membro"].pk}
    with transaction.atomic():
        barreira()
        with pytest.raises(UltimoAdmin):
            guardas_conjunto(alvos)
    assert f.grupo.membros.filter(usuario_id__in=alvos).count() == 2


@pytest.mark.django_db(transaction=True)
def test_rn30_restore_reaplica_commit_autenticado_e_idempotente(settings, monkeypatch, tmp_path):
    import json

    from django.contrib.auth import get_user_model
    from django.core.management import call_command
    from django.db import connection

    from apps.privacidade.journal import _mac
    from apps.privacidade.models import ExecucaoRestauracao, MarcaRestauracao

    user = get_user_model().objects.create_user(
        username="restore-proof", email="restore@example.com"
    )
    owner_id = user.pk
    settings.VARAL_RESTORE_MODE = True
    operation = uuid.uuid4()
    MarcaRestauracao.objects.create(operation_id=operation)
    epoch, fence_id = str(uuid.uuid4()), str(uuid.uuid4())
    seal = {"epoch": epoch, "fence_id": fence_id, "seq": 2, "record_mac": "a" * 64}
    mod = "apps.privacidade.management.commands.reconciliar_exclusoes_restore"
    monkeypatch.setattr(f"{mod}.ler_fence", lambda nonce: seal)
    monkeypatch.setattr(f"{mod}.validar_fence", lambda envelope, nonce: envelope)
    monkeypatch.setattr(
        f"{mod}.validar_journal",
        lambda checkpoint, **kwargs: ({str(owner_id)}, {"seq": 2, "mac": "a" * 64}),
    )
    with connection.cursor() as cursor:
        cursor.execute("SELECT system_identifier::text FROM pg_control_system()")
        system_id = cursor.fetchone()[0]
    proof = {
        "version": 1,
        "operation_id": str(operation),
        "snapshot_id": str(uuid.uuid4()),
        "epoch": epoch,
        "fence_id": fence_id,
        "journal_seq": 2,
        "journal_record_mac": "a" * 64,
        "system_identifier": system_id,
        "timeline": "00000001",
        "target_lsn": "0/100",
        "replay_lsn": "0/100",
        "wal_checkpoint_seq": 1,
        "wal_chain_mac": "b" * 64,
        "base_cipher_sha256": "c" * 64,
        "objects_cipher_sha256": "d" * 64,
        "objects_manifest_sha256": "e" * 64,
        "pins_manifest_sha256": "f" * 64,
        "key_id": "restore-proof-v1",
    }
    key = b"p" * 32
    proof["mac"] = _mac(key, b"varal-restore-proof-v1\n", canonico(proof))
    path, keypath, anchor = tmp_path / "proof", tmp_path / "key", tmp_path / "anchor"
    path.write_bytes(canonico(proof))
    keypath.write_bytes(key)
    anchor.write_text(json.dumps({}))
    args = (
        "reconciliar_exclusoes_restore",
        "--isolado",
        "--ancora",
        str(anchor),
        "--prova",
        str(path),
        "--prova-chave",
        str(keypath),
        "--operacao",
        str(operation),
        "--fence",
        fence_id,
    )
    call_command(*args)
    assert not get_user_model().objects.filter(pk=owner_id).exists()
    assert ExecucaoRestauracao.objects.filter(operation_id=operation).count() == 1
    call_command(*args)
    assert ExecucaoRestauracao.objects.filter(operation_id=operation).count() == 1


@pytest.mark.django_db
def test_rn30_manifesto_restore_preserva_pin_sem_documento(settings):
    import io
    import json

    from django.core.management import call_command

    from apps.boletos.models import PinPDF
    from apps.privacidade.models import MarcaRestauracao

    settings.VARAL_RESTORE_MODE = True
    operation, reserva, documento = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    MarcaRestauracao.objects.create(operation_id=operation)
    PinPDF.objects.create(reserva_id=reserva, documento_id=documento, tamanho=123)
    saida = io.StringIO()
    call_command(
        "exportar_manifesto_restore", "--operacao", str(operation), "--isolado", stdout=saida
    )
    result = json.loads(saida.getvalue())
    key = f"boletos/{documento}.pdf"
    assert {"reserva_id": str(reserva), "key": key, "size": 123} in result["pins"]
    assert {"key": key, "size": 123, "sha256": None} in result["objects"]


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
