"""Synthetic benchmark fixture; invoked only by guarded seed.mjs inside the isolated lab API."""

import json
import os
import re
import uuid
from datetime import timedelta

from apps.contas_usuario.models import Usuario
from apps.espacos.acesso import lancamentos_visiveis
from apps.espacos.models import Espaco, Membro, Papel
from apps.lancamentos.models import Acao, Historico, Lancamento, Status, Visibilidade
from apps.lancamentos.servicos import criar
from apps.notificacoes.acesso import autorizadas
from apps.notificacoes.models import EventoNotificacao, TipoEvento
from apps.notificacoes.servicos import consumir_pagamento, criar_notificacao
from apps.pagamentos.servicos import marcar
from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone

if (
    os.environ.get("VARAL_QA11_LAB") != "1"
    or settings.DEBUG
    or connection.settings_dict["NAME"] != "varal_lab"
    or connection.settings_dict["HOST"] != "postgres"
):
    raise RuntimeError("Fixture refuses non-laboratory database")

suffix = uuid.uuid4().hex
email = f"e2e-benchmark11-{suffix}@varal.invalid"
assert re.fullmatch(r"e2e-benchmark11-[a-f0-9]{32}@varal\.invalid", email)
password = "Varal-e2e!93-Linha"  # public synthetic test credential only
hoje = timezone.localdate()
with transaction.atomic():
    dono = Usuario.objects.create_user(
        username=email,
        email=email,
        password=password,
        nome="Pessoa benchmark",
        prefs_notificacao={"email": False, "push": False},
    )
    outro_email = f"e2e-benchmark11-outro-{suffix}@varal.invalid"
    outro = Usuario.objects.create_user(
        username=outro_email,
        email=outro_email,
        password=password,
        nome="Outro benchmark",
        prefs_notificacao={"email": False, "push": False},
    )
    pessoal = Espaco.objects.get(tipo=Espaco.Tipo.PESSOAL, dono=dono)
    avisaveis = []
    grupos = []
    ocultas = []

    def conta(espaco, autor, pagador, n, prefixo, esperando=False):
        dias = 0 if prefixo == "Pessoal benchmark" and 2 <= n < 22 else n % 3
        dados = {
            "descricao": f"{prefixo} {n:03}",
            "vencimento": hoje + timedelta(days=dias),
            "valor_centavos": 1000 + n,
            "pagador": pagador.id,
        }
        if esperando:
            # Valid legacy awaiting occurrence, NULL is a supported persisted state (D08-1).
            item = Lancamento.objects.create(
                espaco=espaco,
                criador=autor,
                pagador=pagador,
                descricao=dados["descricao"],
                vencimento=dados["vencimento"],
                valor_centavos=None,
                status=Status.AGUARDANDO,
            )
            Historico.objects.create(lancamento=item, usuario=autor, acao=Acao.CRIADA)
        else:
            item = criar(autor, espaco, dados)
        return item

    for i in range(100):
        item = conta(pessoal, dono, dono, i, "Pessoal benchmark", esperando=i == 0)
        if i == 1:
            _, pagamento = marcar(
                dono,
                item.id,
                {"pago_em": hoje, "valor_centavos_esperado": item.valor_centavos},
            )
            consumir_pagamento(pagamento.evento.id)
        elif 2 <= i < 21:
            avisaveis.append(item)

    for g in range(20):
        grupo = Espaco.objects.create(
            tipo=Espaco.Tipo.GRUPO, nome=f"Grupo benchmark {g:02}"
        )
        Membro.objects.create(espaco=grupo, usuario=outro, papel=Papel.ADMIN)
        Membro.objects.create(espaco=grupo, usuario=dono, papel=Papel.MEMBRO)
        grupos.append(str(grupo.id))
        for i in range(10):
            item = conta(grupo, outro, dono, i, f"Grupo {g:02}", esperando=i == 0)
            if i == 1:
                marcar(
                    dono,
                    item.id,
                    {"pago_em": hoje, "valor_centavos_esperado": item.valor_centavos},
                )
        oculta = criar(
            outro,
            grupo,
            {
                "descricao": f"Restrita invisível {g:02}",
                "vencimento": hoje,
                "valor_centavos": 2000,
                "pagador": outro.id,
                "visibilidade": Visibilidade.RESTRITA,
                "acesso": [],
            },
        )
        ocultas.append(str(oculta.id))
        assert lancamentos_visiveis(dono, grupo).count() == 10
        assert not lancamentos_visiveis(dono, grupo).filter(pk=oculta.id).exists()

    for item in avisaveis:
        evento = EventoNotificacao.objects.create(
            chave=f"benchmark11:{suffix}:{item.id}",
            tipo=TipoEvento.VENCE_HOJE,
            lancamento=item,
            alvo=hoje,
            canais_permitidos=False,
            materializado_em=timezone.now(),
        )
        criar_notificacao(evento, dono)
    assert Lancamento.objects.filter(espaco=pessoal).count() == 100
    assert len(grupos) == 20 and autorizadas(dono).count() == 20
    assert Lancamento.objects.filter(
        espaco=pessoal, valor_centavos=None, status=Status.AGUARDANDO
    ).exists()
    assert Lancamento.objects.filter(espaco=pessoal, status=Status.PAGA).exists()
    print(
        json.dumps(
            {
                "owner": str(dono.id),
                "email": email,
                "pessoal": str(pessoal.id),
                "grupos": grupos,
                "ocultas": ocultas,
                "avisos": 20,
            }
        )
    )
