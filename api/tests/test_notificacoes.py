import base64
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.espacos import servicos as grupos
from apps.lancamentos import servicos as contas
from apps.lancamentos.models import Acao, Historico, Lancamento
from apps.notificacoes import push, servicos
from apps.notificacoes.models import EventoNotificacao, InscricaoPush, Notificacao, TipoEvento
from apps.pagamentos import servicos as pagamentos
from tests import test_contas
from tests.test_grupos import cliente

contas_fixture = test_contas.f
pytestmark = pytest.mark.django_db


@pytest.fixture
def f(contas_fixture):
    return contas_fixture


@pytest.fixture
def horario():
    with patch("django.utils.timezone.now", return_value=datetime(2026, 11, 16, 12, 0, tzinfo=UTC)):
        yield


def chave_b64(data):
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def dados_push():
    chave = (
        ec.generate_private_key(ec.SECP256R1())
        .public_key()
        .public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    )
    return {
        "endpoint": "https://fcm.googleapis.com/token-aleatorio",
        "keys": {"p256dh": chave_b64(chave), "auth": chave_b64(b"abcdefghijklmnop")},
        "instalacao": str(uuid.uuid4()),
    }


def conta(f, **dados):
    return test_contas.nova(f.u["admin"], f.grupo, **dados)


def test_rn19_fases_e_audiencia_so_contas_visiveis(f, horario):
    a = conta(f, pagador=f.u["membro"].pk, vencimento=timezone.localdate() + timedelta(days=3))
    oculta = conta(
        f,
        pagador=f.u["membro"].pk,
        visibilidade="restrita",
        vencimento=timezone.localdate() + timedelta(days=1),
    )
    servicos.varrer_lembretes()
    servicos.varrer_lembretes()
    eventos = EventoNotificacao.objects.filter(lancamento=a)
    assert eventos.count() == 1 and eventos.get().tipo == TipoEvento.VENCE_3
    assert Notificacao.objects.filter(evento=eventos.get(), destinatario=f.u["membro"]).count() == 1
    assert not EventoNotificacao.objects.filter(lancamento=oculta).exists()
    resumo = cliente(f.u["membro"]).get("/api/notificacoes/resumo/")
    assert resumo.status_code == 200, resumo.content
    assert resumo.json()["nao_lidas"] == 1


def test_q09_2_revogacao_terminal_em_edicao_de_acesso(f, horario):
    a = conta(f, pagador=f.u["membro"].pk, vencimento=timezone.localdate() + timedelta(days=3))
    servicos.varrer_lembretes()
    n = Notificacao.objects.get(destinatario=f.u["membro"])
    contas.editar(
        f.u["admin"], a.pk, {"pagador": f.u["admin"].pk, "visibilidade": "restrita", "acesso": []}
    )
    contas.editar(f.u["admin"], a.pk, {"pagador": f.u["membro"].pk, "visibilidade": "grupo"})
    n.refresh_from_db()
    assert n.revogado_em
    assert cliente(f.u["membro"]).get("/api/notificacoes/resumo/").json()["nao_lidas"] == 0
    assert cliente(f.u["membro"]).post(f"/api/notificacoes/{n.pk}/ler/").status_code == 404


def test_q09_3_pagamento_pendente07_e_undo(f, horario):
    a = conta(f, pagador=f.u["membro"].pk)
    _, p = pagamentos.marcar(
        f.u["membro"], a.pk, {"pago_em": timezone.localdate(), "valor_centavos_esperado": 1000}
    )
    servicos.consumir_fontes()
    n = Notificacao.objects.get(destinatario=f.u["admin"], evento__tipo=TipoEvento.PAGAMENTO)
    assert cliente(f.u["admin"]).get("/api/notificacoes/resumo/").json()["nao_lidas"] == 1
    pagamentos.desfazer(f.u["membro"], a.pk, p.pk)
    n.refresh_from_db()
    assert (
        n.revogado_em
        and cliente(f.u["admin"]).get("/api/notificacoes/resumo/").json()["nao_lidas"] == 0
    )


def test_p7_novo_privado_snapshot_e_legado_sem_enriquecer(f, horario):
    from apps.notificacoes.models import ControleNotificacoes

    ControleNotificacoes.objects.filter(pk="ativacao_09").update(
        ativado_em=timezone.now() - timedelta(days=1)
    )
    atual = test_contas.restrita(f.u["membro"], f.grupo, descricao="Conta privada")
    grupos.remover_membro(f.grupo, f.m["membro"].pk)
    servicos.consumir_fontes()
    c = cliente(f.u["membro"])
    lista = c.get("/api/notificacoes/").json()["resultados"]
    assert len(lista) == 1 and "Conta privada" in lista[0]["texto"] and lista[0]["destino"] is None
    assert cliente(f.u["admin"]).get("/api/notificacoes/").json()["resultados"] == []
    assert c.get(f"/api/lancamentos/{atual.pk}/").status_code == 404


def test_q09_9_marcar_todas_sem_tocar_outro_destinatario(f, horario):
    for n in range(4):
        conta(
            f,
            pagador=f.u["membro"].pk,
            vencimento=timezone.localdate() + timedelta(days=3),
            descricao=f"Conta {n}",
        )
    servicos.varrer_lembretes()
    c = cliente(f.u["membro"])
    primeira = c.get("/api/notificacoes/", {"limite": 1}).json()
    assert primeira["nao_lidas"] == 4 and primeira["proximo"]
    assert c.post("/api/notificacoes/ler-todas/").json()["nao_lidas"] == 0
    tempos = list(
        Notificacao.objects.filter(destinatario=f.u["membro"]).values_list("lido_em", flat=True)
    )
    assert all(tempos)
    assert c.post("/api/notificacoes/ler-todas/").json()["nao_lidas"] == 0
    assert (
        list(
            Notificacao.objects.filter(destinatario=f.u["membro"]).values_list("lido_em", flat=True)
        )
        == tempos
    )


def test_q09_7_alias_host_fingerprint_e_pontos_validos(settings):
    settings.WEBPUSH_ALLOWED_HOSTS = {"fcm.googleapis.com"}
    assert push.fingerprint("https://fcm.googleapis.com/token") == push.fingerprint(
        "https://FCM.GOOGLEAPIS.COM:443/%74oken"
    )
    assert push.fingerprint("https://fcm.googleapis.com/a%2Fb") != push.fingerprint(
        "https://fcm.googleapis.com/a/b"
    )
    chaves = dados_push()["keys"]
    push.validar_chaves(**chaves)
    with pytest.raises(ValidationError):
        push.validar_chaves(p256dh=chave_b64(b"\x04" + b"\x00" * 64), auth=chaves["auth"])


def test_q09_6_tombstone_e_logout_nativo(f, settings):
    settings.WEBPUSH_ENABLED = True
    settings.WEBPUSH_PUBLIC_KEY = "publica-sintetica"
    settings.WEBPUSH_ALLOWED_HOSTS = {"fcm.googleapis.com"}
    dados = dados_push()
    c = cliente(f.u["membro"])

    def post():
        return c.post("/api/notificacoes/push/inscricoes/", dados, content_type="application/json")

    resposta = post()
    assert resposta.status_code == 201, resposta.content
    pk = resposta.json()["id"]
    assert post().status_code == 200
    c.logout()
    assert not InscricaoPush.objects.get(pk=pk).ativa
    c = cliente(f.u["membro"])
    assert post().status_code == 409
    dados["instalacao"] = str(uuid.uuid4())
    assert post().status_code == 200


def test_q09_8_p7_legado_sem_descricao_atual(f, horario):
    from apps.notificacoes.models import ControleNotificacoes, EntregaNotificacao

    a = test_contas.restrita(f.u["membro"], f.grupo, descricao="Descrição antiga")
    Lancamento.objects.filter(pk=a.pk).update(status="cancelada", descricao="Descrição alterada")
    registro = Historico.objects.create(
        lancamento=a,
        acao=Acao.CANCELADA_AUTOMATICAMENTE,
        dados={"motivo": "sem_quem_veja", "removido": str(f.u["membro"].pk)},
    )
    corte = ControleNotificacoes.objects.get(pk="ativacao_09").ativado_em
    Historico.objects.filter(pk=registro.pk).update(criado_em=corte - timedelta(days=1))
    f.m["membro"].delete()
    servicos.consumir_fontes()
    usuario = cliente(f.u["membro"])
    avisos = usuario.get("/api/notificacoes/").json()["resultados"]
    assert len(avisos) == 1
    assert str(registro.pk) in avisos[0]["texto"]
    assert (
        "Descrição antiga" not in avisos[0]["texto"]
        and "Descrição alterada" not in avisos[0]["texto"]
    )
    evento = EventoNotificacao.objects.get(historico=registro)
    assert evento.canais_permitidos is False
    assert set(
        EntregaNotificacao.objects.filter(notificacao__evento=evento).values_list(
            "estado", flat=True
        )
    ) == {"descartada"}


def test_d09_1_rotina_gera_primeiro_e_avisa_variavel_nova(f):
    from apps.notificacoes.tasks import rotina_diaria
    from apps.recorrencias import servicos as recorrencias

    with patch("django.utils.timezone.now", return_value=datetime(2026, 11, 16, 12, 0, tzinfo=UTC)):
        dados = {
            "chave_idempotencia": uuid.uuid4(),
            "descricao": "Recorrente",
            "dia_vencimento": 6,
            "valor_tipo": "variavel",
            "valor_centavos": None,
            "pagador": f.u["membro"].pk,
        }
        modelo, _, _ = recorrencias.criar(f.u["membro"], f.grupo, dados)
    with patch("django.utils.timezone.now", return_value=datetime(2026, 12, 1, 10, 0, tzinfo=UTC)):
        rotina_diaria()
        rotina_diaria()
    conta_nova = Lancamento.objects.get(recorrencia=modelo, competencia="2026-12-01")
    assert conta_nova.status == "aguardando"
    assert (
        EventoNotificacao.objects.filter(
            lancamento=conta_nova, tipo=TipoEvento.BOLETO_AUSENTE
        ).count()
        == 1
    )
    assert (
        Notificacao.objects.filter(
            evento__lancamento=conta_nova, destinatario=f.u["membro"]
        ).count()
        == 1
    )


def test_q09_4_retry_tres_totais_e_timeout_incerto(f, horario):
    from apps.notificacoes.entregas import enviar_email_entrega
    from apps.notificacoes.models import EntregaNotificacao
    from apps.notificacoes.transportes import Resultado

    a = conta(f, pagador=f.u["membro"].pk, vencimento=timezone.localdate() + timedelta(days=3))
    servicos.varrer_lembretes()
    entrega = EntregaNotificacao.objects.get(notificacao__evento__lancamento=a, canal="email")
    momentos = [
        datetime(2026, 11, 16, 12, 0, tzinfo=UTC),
        datetime(2026, 11, 16, 12, 2, tzinfo=UTC),
        datetime(2026, 11, 16, 12, 8, tzinfo=UTC),
        datetime(2026, 11, 16, 12, 15, tzinfo=UTC),
    ]
    with patch(
        "apps.notificacoes.transportes.enviar_email",
        return_value=Resultado("transiente", "smtp_recusou"),
    ) as enviar:
        for momento in momentos:
            with patch("django.utils.timezone.now", return_value=momento):
                enviar_email_entrega(entrega.pk)
    entrega.refresh_from_db()
    assert enviar.call_count == 3 and entrega.tentativas == 3 and entrega.estado == "falhou"
    entrega.estado, entrega.tentativas = "iniciada", 1
    entrega.lease_ate = timezone.now() - timedelta(seconds=1)
    entrega.save()
    with patch("apps.notificacoes.transportes.enviar_email") as enviar:
        enviar_email_entrega(entrega.pk)
        entrega.refresh_from_db()
        assert entrega.estado == "incerta" and enviar.call_count == 0


def test_q09_6_delete_antes_do_post_e_alias_de_outro_usuario(f, settings):
    settings.WEBPUSH_ENABLED, settings.WEBPUSH_PUBLIC_KEY = True, "chave-publica"
    settings.WEBPUSH_ALLOWED_HOSTS = {"fcm.googleapis.com"}
    dados = dados_push()
    primeiro = cliente(f.u["membro"])
    caminho = f"/api/notificacoes/push/instalacoes/{dados['instalacao']}/"
    assert primeiro.delete(caminho).status_code == 204
    assert (
        primeiro.post(
            "/api/notificacoes/push/inscricoes/", dados, content_type="application/json"
        ).status_code
        == 409
    )
    dados["instalacao"] = str(uuid.uuid4())
    assert (
        primeiro.post(
            "/api/notificacoes/push/inscricoes/", dados, content_type="application/json"
        ).status_code
        == 201
    )
    outro = cliente(f.u["observador"])
    dados["instalacao"] = str(uuid.uuid4())
    dados["endpoint"] = "https://FCM.GOOGLEAPIS.COM:443/%74oken-aleatorio"
    assert (
        outro.post(
            "/api/notificacoes/push/inscricoes/", dados, content_type="application/json"
        ).status_code
        == 409
    )


@pytest.mark.parametrize("mesma_sessao", [True, False])
def test_q09_6_delete_antigo_nao_revoga_geracao_de_outra_sessao(f, settings, mesma_sessao):
    settings.WEBPUSH_ENABLED, settings.WEBPUSH_PUBLIC_KEY = True, "chave-publica"
    settings.WEBPUSH_ALLOWED_HOSTS = {"fcm.googleapis.com"}
    dados = dados_push()
    a = cliente(f.u["membro"])
    b = a if mesma_sessao else cliente(f.u["membro"])
    antiga = dados["instalacao"]
    primeira = a.post("/api/notificacoes/push/inscricoes/", dados, content_type="application/json")
    assert primeira.status_code == 201
    pk = primeira.json()["id"]
    assert a.delete(f"/api/notificacoes/push/instalacoes/{dados['instalacao']}/").status_code == 204
    dados["instalacao"] = str(uuid.uuid4())
    assert (
        b.post(
            "/api/notificacoes/push/inscricoes/", dados, content_type="application/json"
        ).status_code
        == 200
    )
    assert a.delete(f"/api/notificacoes/push/instalacoes/{antiga}/").status_code == 204
    assert InscricaoPush.objects.get(pk=pk).ativa


def test_q09_7_dns_bloqueia_resultado_misto_e_mapeado():
    import socket

    publico = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443))
    privado = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))
    mapeado = (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("::ffff:8.8.8.8", 443, 0, 0))
    with (
        patch("apps.notificacoes.push.socket.getaddrinfo", return_value=[publico, privado]),
        pytest.raises(ValueError),
    ):
        push.resolver_publico("fcm.googleapis.com")
    with (
        patch("apps.notificacoes.push.socket.getaddrinfo", return_value=[mapeado]),
        pytest.raises(ValueError),
    ):
        push.resolver_publico("fcm.googleapis.com")


@pytest.mark.django_db(transaction=True)
def test_q09_6_logout_e_post_concorrentes_nao_reativam(f, settings):
    from tests.test_grupos import rodar_em_paralelo

    settings.WEBPUSH_ENABLED, settings.WEBPUSH_PUBLIC_KEY = True, "chave-publica"
    settings.WEBPUSH_ALLOWED_HOSTS = {"fcm.googleapis.com"}
    dados = dados_push()
    a, b = cliente(f.u["membro"]), cliente(f.u["membro"])
    primeira = a.post("/api/notificacoes/push/inscricoes/", dados, content_type="application/json")
    assert primeira.status_code == 201
    resultados = rodar_em_paralelo(
        lambda: a.logout(),
        lambda: b.post(
            "/api/notificacoes/push/inscricoes/", dados, content_type="application/json"
        ),
    )
    assert resultados[0] is None and resultados[1].status_code == 409
    assert not InscricaoPush.objects.get(pk=primeira.json()["id"]).ativa


def test_q09_6_logout_allauth_revoga_sessao_nativa(f, settings):
    settings.WEBPUSH_ENABLED, settings.WEBPUSH_PUBLIC_KEY = True, "chave-publica"
    settings.WEBPUSH_ALLOWED_HOSTS = {"fcm.googleapis.com"}
    dados = dados_push()
    c = cliente(f.u["membro"])
    criada = c.post("/api/notificacoes/push/inscricoes/", dados, content_type="application/json")
    assert criada.status_code == 201
    resposta = c.delete("/api/auth/browser/v1/auth/session")
    assert resposta.status_code == 401
    assert not InscricaoPush.objects.get(pk=criada.json()["id"]).ativa
    c = cliente(f.u["membro"])
    assert (
        c.post(
            "/api/notificacoes/push/inscricoes/", dados, content_type="application/json"
        ).status_code
        == 409
    )


def test_q09_2_troca_papel_e_retorno_nao_ressuscitam(f, horario):
    a = conta(f, pagador=f.u["membro"].pk, vencimento=timezone.localdate() + timedelta(days=1))
    # D+1 to creator/admin; make member admin initially so removal of role loses that eligibility.
    grupos.alterar_papel(f.grupo, f.m["membro"].pk, "admin")
    Lancamento.objects.filter(pk=a.pk).update(
        vencimento=timezone.localdate() - timedelta(days=1), pagador=None
    )
    servicos.varrer_lembretes()
    n = Notificacao.objects.get(destinatario=f.u["membro"], evento__lancamento=a)
    grupos.alterar_papel(f.grupo, f.m["membro"].pk, "membro")
    grupos.alterar_papel(f.grupo, f.m["membro"].pk, "admin")
    n.refresh_from_db()
    assert (
        n.revogado_em
        and cliente(f.u["membro"]).get("/api/notificacoes/resumo/").json()["nao_lidas"] == 0
    )


def test_rn21_exclusao_de_usuario_registra_evento_sem_pagar(f, horario):
    a = conta(f, pagador=f.u["membro"].pk)
    f.u["membro"].delete()
    a.refresh_from_db()
    assert a.pagador_id is None
    h = Historico.objects.get(lancamento=a, acao=Acao.PAGADOR_REMOVIDO)
    servicos.consumir_fontes()
    assert Notificacao.objects.filter(evento__historico=h, destinatario=f.u["admin"]).exists()


def test_q09_4_dispositivos_independentes_e_novo_nao_recebe_passado(f, settings, horario):
    from apps.notificacoes.entregas import enviar_push_dispositivo
    from apps.notificacoes.models import EntregaPushDispositivo
    from apps.notificacoes.transportes import Resultado

    settings.WEBPUSH_ENABLED, settings.WEBPUSH_PUBLIC_KEY = True, "chave-publica"
    settings.WEBPUSH_ALLOWED_HOSTS = {"fcm.googleapis.com"}
    for indice in range(2):
        inscricao = dados_push()
        inscricao["endpoint"] += str(indice)
        assert (
            cliente(f.u["membro"])
            .post("/api/notificacoes/push/inscricoes/", inscricao, content_type="application/json")
            .status_code
            == 201
        )
    a = conta(f, pagador=f.u["membro"].pk, vencimento=timezone.localdate() + timedelta(days=3))
    servicos.varrer_lembretes()
    entregas = list(
        EntregaPushDispositivo.objects.filter(entrega__notificacao__evento__lancamento=a).order_by(
            "pk"
        )
    )
    assert len(entregas) == 2
    nova = dados_push()
    nova["endpoint"] += "terceiro"
    assert (
        cliente(f.u["membro"])
        .post("/api/notificacoes/push/inscricoes/", nova, content_type="application/json")
        .status_code
        == 201
    )
    assert EntregaPushDispositivo.objects.filter(entrega=entregas[0].entrega).count() == 2
    with patch(
        "apps.notificacoes.transportes.enviar_push",
        side_effect=[Resultado("aceita"), Resultado("descartada", "inscricao_expirada")],
    ) as enviar:
        enviar_push_dispositivo(entregas[0].pk)
        enviar_push_dispositivo(entregas[1].pk)
        enviar_push_dispositivo(entregas[0].pk)
    assert enviar.call_count == 2
    for item in entregas:
        item.refresh_from_db()
    assert {i.estado for i in entregas} == {"aceita", "descartada"}
    expirada = next(i for i in entregas if i.estado == "descartada")
    assert not InscricaoPush.objects.get(pk=expirada.inscricao_id).ativa
    entregas[0].entrega.refresh_from_db()
    assert entregas[0].entrega.estado == "aceita"


def test_q09_6_optout_descarta_sem_reativar_envio(f, horario):
    from apps.notificacoes.entregas import enviar_email_entrega
    from apps.notificacoes.models import EntregaNotificacao

    a = conta(f, pagador=f.u["membro"].pk, vencimento=timezone.localdate() + timedelta(days=3))
    servicos.varrer_lembretes()
    entrega = EntregaNotificacao.objects.get(notificacao__evento__lancamento=a, canal="email")
    c = cliente(f.u["membro"])
    assert (
        c.patch(
            "/api/notificacoes/preferencias/", {"email": False}, content_type="application/json"
        ).status_code
        == 200
    )
    assert (
        c.patch(
            "/api/notificacoes/preferencias/", {"email": True}, content_type="application/json"
        ).status_code
        == 200
    )
    with patch("apps.notificacoes.transportes.enviar_email") as enviar:
        enviar_email_entrega(entrega.pk)
    entrega.refresh_from_db()
    assert entrega.estado == "descartada" and not enviar.called


@pytest.mark.django_db(transaction=True)
def test_rnf07_duas_varreduras_concorrentes_criam_um_evento(f, horario):
    from tests.test_grupos import rodar_em_paralelo

    a = conta(f, pagador=f.u["membro"].pk, vencimento=timezone.localdate() + timedelta(days=3))
    resultados = rodar_em_paralelo(servicos.varrer_lembretes, servicos.varrer_lembretes)
    assert resultados == [None, None]
    assert EventoNotificacao.objects.filter(lancamento=a, tipo=TipoEvento.VENCE_3).count() == 1
    assert Notificacao.objects.filter(evento__lancamento=a, destinatario=f.u["membro"]).count() == 1


def test_d09_1_falha_geracao_nao_calcula_avisos(horario):
    from apps.notificacoes.models import RodadaDiaria
    from apps.notificacoes.tasks import rotina_diaria

    with (
        patch("apps.notificacoes.tasks.gerar_recorrencias", side_effect=RuntimeError),
        patch("apps.notificacoes.tasks.varrer_lembretes") as varrer,
    ):
        with pytest.raises(RuntimeError):
            rotina_diaria()
    assert not varrer.called
    rodada = RodadaDiaria.objects.get(dia=timezone.localdate())
    assert not rodada.geracao_concluida and not rodada.avisos_concluidos and rodada.token is None


def test_q09_4_erro_no_quit_nao_desfaz_aceite_email(settings):
    from apps.notificacoes.transportes import enviar_email

    class Conexao:
        def open(self):
            return True

        def send_messages(self, mensagens):
            return 1

        def close(self):
            raise OSError("simulado")

    with patch("apps.notificacoes.transportes.get_connection", return_value=Conexao()):
        resultado = enviar_email("pessoa@example.invalid")
    assert resultado.estado == "aceita"


@pytest.mark.django_db(transaction=True)
def test_q09_6_ordem_logout_e_post_mesma_instalacao_sem_deadlock(f, settings):
    import threading
    from concurrent.futures import ThreadPoolExecutor

    from django.db import connection

    from apps.notificacoes import sessoes

    settings.WEBPUSH_ENABLED, settings.WEBPUSH_PUBLIC_KEY = True, "chave-publica"
    settings.WEBPUSH_ALLOWED_HOSTS = {"fcm.googleapis.com"}
    dados = dados_push()
    a, b = cliente(f.u["membro"]), cliente(f.u["membro"])
    primeira = a.post("/api/notificacoes/push/inscricoes/", dados, content_type="application/json")
    assert primeira.status_code == 201
    b_travou = threading.Event()
    a_tentou = threading.Event()
    a_iniciou = threading.Event()
    liberar = threading.Event()
    original = sessoes.travar_instalacao

    def trava_b(usuario, identificador):
        valor = original(usuario, identificador)
        b_travou.set()
        assert liberar.wait(15)
        return valor

    def trava_a(usuario, identificador):
        a_tentou.set()
        return original(usuario, identificador)

    def sair_a():
        try:
            a_iniciou.set()
            a.logout()
        finally:
            connection.close()

    def postar_b():
        try:
            return b.post(
                "/api/notificacoes/push/inscricoes/", dados, content_type="application/json"
            )
        finally:
            connection.close()

    with (
        patch("apps.notificacoes.views.travar_instalacao", side_effect=trava_b),
        patch("apps.notificacoes.signals.travar_instalacao", side_effect=trava_a),
    ):
        with ThreadPoolExecutor(max_workers=2) as executor:
            futuro_b = executor.submit(postar_b)
            assert b_travou.wait(15)
            futuro_a = executor.submit(sair_a)
            assert a_iniciou.wait(15)
            try:
                # A waits at the global barrier while B owns it; no lock inversion.
                assert not a_tentou.wait(0.2)
            finally:
                liberar.set()
            assert futuro_b.result(timeout=20).status_code == 409
            assert futuro_a.result(timeout=20) is None
    assert not InscricaoPush.objects.get(pk=primeira.json()["id"]).ativa


def test_q09_4_erro_de_autenticacao_smtp_nao_e_repetido():
    import smtplib

    from apps.notificacoes.transportes import enviar_email

    class Conexao:
        def open(self):
            raise smtplib.SMTPAuthenticationError(535, b"erro sintetico")

    with patch("apps.notificacoes.transportes.get_connection", return_value=Conexao()):
        resultado = enviar_email("pessoa@example.invalid")
    assert resultado.estado == "falhou" and resultado.codigo == "configuracao"


def test_q09_6_preferencias_aceitam_apenas_booleans_conhecidos(f):
    c = cliente(f.u["membro"])
    url = "/api/notificacoes/preferencias/"
    assert c.patch(url, {"email": "false"}, content_type="application/json").status_code == 400
    assert c.patch(url, {"outro": True}, content_type="application/json").status_code == 400
    assert c.get(url).json() == {"versao": 1, "email": True, "push": True}


@pytest.mark.django_db(transaction=True)
def test_q09_6_inicio_push_serializa_com_revogacao_da_inscricao(f, settings, horario):
    import threading

    from apps.notificacoes import entregas
    from apps.notificacoes.models import EntregaPushDispositivo
    from apps.notificacoes.transportes import Resultado
    from tests.test_grupos import rodar_em_paralelo

    settings.WEBPUSH_ENABLED, settings.WEBPUSH_PUBLIC_KEY = True, "chave-publica"
    settings.WEBPUSH_ALLOWED_HOSTS = {"fcm.googleapis.com"}
    dados = dados_push()
    c = cliente(f.u["membro"])
    assert (
        c.post(
            "/api/notificacoes/push/inscricoes/", dados, content_type="application/json"
        ).status_code
        == 201
    )
    a = conta(f, pagador=f.u["membro"].pk, vencimento=timezone.localdate() + timedelta(days=3))
    servicos.varrer_lembretes()
    item = EntregaPushDispositivo.objects.get(entrega__notificacao__evento__lancamento=a)
    iniciou = threading.Event()
    revogacao_acabou = threading.Event()
    original = entregas._iniciar

    def pausar(*args):
        iniciou.set()
        assert not revogacao_acabou.wait(0.5)
        return original(*args)

    def revogar():
        assert iniciou.wait(5)
        resposta = c.delete(f"/api/notificacoes/push/instalacoes/{dados['instalacao']}/")
        revogacao_acabou.set()
        return resposta.status_code

    with (
        patch("apps.notificacoes.entregas._iniciar", side_effect=pausar),
        patch("apps.notificacoes.transportes.enviar_push", return_value=Resultado("aceita")),
    ):
        resultados = rodar_em_paralelo(lambda: entregas.enviar_push_dispositivo(item.pk), revogar)
    assert resultados == [None, 204]
    assert revogacao_acabou.is_set()


def test_q09_6_troca_de_sessao_allauth_revoga_inscricao(f, settings):
    from django.test import RequestFactory

    from apps.contas_usuario.adapters import AccountAdapter

    settings.WEBPUSH_ENABLED, settings.WEBPUSH_PUBLIC_KEY = True, "chave-publica"
    settings.WEBPUSH_ALLOWED_HOSTS = {"fcm.googleapis.com"}
    dados = dados_push()
    c = cliente(f.u["membro"])
    criada = c.post("/api/notificacoes/push/inscricoes/", dados, content_type="application/json")
    assert criada.status_code == 201
    request = RequestFactory().post("/")
    request.session = c.session
    request.user = f.u["membro"]
    AccountAdapter().login(request, f.u["observador"])
    assert not InscricaoPush.objects.get(pk=criada.json()["id"]).ativa


@pytest.mark.parametrize(
    "metodo,caminho",
    [
        ("post", "/api/notificacoes/00000000-0000-0000-0000-000000000001/ler/"),
        ("post", "/api/notificacoes/ler-todas/"),
        ("patch", "/api/notificacoes/preferencias/"),
        ("post", "/api/notificacoes/push/inscricoes/"),
        ("delete", "/api/notificacoes/push/instalacoes/00000000-0000-0000-0000-000000000001/"),
    ],
)
def test_escritas_exigem_sessao_e_csrf_real(f, metodo, caminho):
    from rest_framework.test import APIClient

    c = APIClient(enforce_csrf_checks=True)
    assert getattr(c, metodo)(caminho, {}, format="json").status_code == 403
    c.force_login(f.u["membro"])
    assert getattr(c, metodo)(caminho, {}, format="json").status_code == 403
    c.cookies["csrftoken"] = "a" * 32
    assert (
        getattr(c, metodo)(caminho, {}, format="json", HTTP_X_CSRFTOKEN="b" * 32).status_code == 403
    )


def test_instalacao_nao_pode_mudar_endpoint_no_mesmo_ciclo(f, settings):
    settings.WEBPUSH_ENABLED = True
    settings.WEBPUSH_PUBLIC_KEY = "publica-sintetica"
    settings.WEBPUSH_ALLOWED_HOSTS = {"fcm.googleapis.com"}
    c = cliente(f.u["membro"])
    dados = dados_push()
    assert (
        c.post(
            "/api/notificacoes/push/inscricoes/", dados, content_type="application/json"
        ).status_code
        == 201
    )
    dados["endpoint"] += "-outro"
    assert (
        c.post(
            "/api/notificacoes/push/inscricoes/", dados, content_type="application/json"
        ).status_code
        == 409
    )
    assert InscricaoPush.objects.count() == 1


def test_reagendar_pendencia_mantem_janela_e_identidade(f, horario):
    from apps.notificacoes.entregas import enviar_email_entrega
    from apps.notificacoes.models import EntregaNotificacao

    a = conta(f, pagador=f.u["membro"].pk, vencimento=timezone.localdate() + timedelta(days=3))
    servicos.varrer_lembretes()
    entrega = EntregaNotificacao.objects.get(notificacao__evento__lancamento=a, canal="email")
    contas.editar(f.u["admin"], a.pk, {"vencimento": timezone.localdate() + timedelta(days=5)})
    with patch("apps.notificacoes.transportes.enviar_email") as envio:
        enviar_email_entrega(entrega.pk)
        envio.assert_not_called()
    entrega.refresh_from_db()
    assert entrega.estado == "pendente" and timezone.localtime(
        entrega.proxima_em
    ).date() == timezone.localdate() + timedelta(days=2)
    with patch("django.utils.timezone.now", return_value=datetime(2026, 11, 18, 12, 0, tzinfo=UTC)):
        servicos.varrer_lembretes()
        assert EventoNotificacao.objects.filter(lancamento=a, tipo=TipoEvento.VENCE_3).count() == 1
