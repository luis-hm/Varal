"""Acceptance gaps for recurrence; synthetic data and the real PostgreSQL constraints."""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from django.db import IntegrityError, transaction

from apps.boletos.models import DocumentoBoleto
from apps.lancamentos.models import Lancamento
from apps.recorrencias.models import Recorrencia
from tests import test_contas
from tests.test_grupos import cliente
from tests.test_recorrencias import criar

pytestmark = pytest.mark.django_db
contas_fixture = test_contas.f


@pytest.fixture
def f(contas_fixture):
    return contas_fixture


@pytest.mark.parametrize("estado", ["aguardando", "pendente", "paga", "confirmada", "cancelada"])
@pytest.mark.parametrize("valor", [0, -1])
def test_d08_1_constraint_sql_rejeita_valor_nao_positivo_em_todo_estado(f, estado, valor):
    from tests.test_contas import nova

    conta = nova(f.u["membro"], f.grupo)
    with pytest.raises(IntegrityError), transaction.atomic():
        Lancamento.objects.filter(pk=conta.pk).update(status=estado, valor_centavos=valor)


def test_q08_9_nonce_reutilizado_com_payload_divergente_nao_cria_ou_altera(f):
    with patch("django.utils.timezone.now", return_value=datetime(2026, 11, 16, 15, tzinfo=UTC)):
        response, corpo = criar(f)
        assert response.status_code == 201
        response = cliente(f.u["membro"]).post(
            f"/api/espacos/{f.grupo.pk}/recorrencias/",
            {**corpo, "descricao": "Outro compromisso"},
            content_type="application/json",
        )
        assert response.status_code == 409
        assert Recorrencia.objects.count() == Lancamento.objects.count() == 1
        assert Recorrencia.objects.get().descricao == "Energia"


def test_q08_9_mes_errado_preserva_draft_pdf_e_nao_cria_modelo(f):
    pdf = DocumentoBoleto.objects.create(
        espaco=f.grupo,
        criado_por=f.u["membro"],
        estado="conferencia_manual",
        nome="sintetico.pdf",
        tamanho=20,
        resultado={},
    )
    with patch("django.utils.timezone.now", return_value=datetime(2026, 11, 16, 15, tzinfo=UTC)):
        response, _ = criar(
            f,
            ocorrencia_inicial={
                "valor_centavos": 765,
                "vencimento": "2026-12-01",
                "documento_pdf": str(pdf.pk),
            },
        )
    assert response.status_code == 400
    assert not Recorrencia.objects.exists() and not Lancamento.objects.exists()
    pdf.refresh_from_db()
    assert pdf.estado == "conferencia_manual"
    assert pdf.lancamento_id is None and pdf.vinculado_em is None
