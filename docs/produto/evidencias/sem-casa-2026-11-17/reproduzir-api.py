import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
import json
import uuid
from datetime import datetime, UTC
from unittest.mock import patch
from django.db import transaction
from django.test import override_settings
from rest_framework.test import APIClient
from apps.contas_usuario.models import Usuario
from apps.espacos.models import Espaco
from apps.espacos.servicos import criar_grupo
from apps.lancamentos.models import Lancamento

resultados = {}
with override_settings(ALLOWED_HOSTS=['testserver'], SECURE_SSL_REDIRECT=False, DEBUG=True), patch('django.utils.timezone.now', return_value=datetime(2026,11,16,15,tzinfo=UTC)):
    with transaction.atomic():
        identificador = 'diag-' + uuid.uuid4().hex
        u = Usuario.objects.create_user(username=identificador, email=identificador+'@example.invalid')
        g = criar_grupo(u, 'Grupo sintético de diagnóstico', ['Casa sintética'])
        casa = g.subgrupos.get()
        c = APIClient()
        c.force_authenticate(user=u)
        base = f'/api/espacos/{g.pk}/lancamentos/'
        ids = {}
        for nome, subgrupo, vencimento in [('sem_casa',None,'2026-11-25'),('com_casa',str(casa.pk),'2026-11-25'),('outro_mes',None,'2026-12-25')]:
            resposta = c.post(base, {'descricao':nome,'valor_centavos':10000,'vencimento':vencimento,'subgrupo':subgrupo,'pagador':str(u.pk),'visibilidade':'grupo'}, format='json')
            assert resposta.status_code == 201, (resposta.status_code, resposta.data)
            ids[nome] = str(resposta.data['id'])
        def lista(**params):
            r = c.get(base, params)
            assert r.status_code == 200, (r.status_code,r.data)
            return r.data
        def nomes(data):
            return sorted(k for k,v in ids.items() if v in [str(i['id']) for i in data['itens']])
        resultados['cadastro'] = {'status':201,'sem_casa_persistida_no_grupo': Lancamento.objects.filter(pk=ids['sem_casa'], espaco=g, subgrupo__isnull=True).exists()}
        resultados['lista_padrao'] = nomes(lista())
        resultados['filtro_meu_pagador_a_pagar'] = nomes(lista(pagador=str(u.pk),status='a_pagar'))
        resultados['filtro_casa'] = nomes(lista(subgrupo=str(casa.pk)))
        resultados['limpar_filtro_casa'] = nomes(lista())
        resultados['mes_seguinte'] = nomes(lista(mes='2026-12'))
        vazio = lista(mes='2027-01', subgrupo=str(casa.pk))
        resultados['mes_vazio_com_filtro_antigo'] = {'itens_qtd':len(vazio['itens']), 'opcoes':vazio['opcoes']}
        r = c.get(f'/api/espacos/{g.pk}/lancamentos/simples/')
        assert r.status_code == 200, r.data
        resultados['modo_simples_abertas'] = nomes(r.data)
        pessoal = Espaco.objects.get(dono=u)
        r = c.get(f'/api/espacos/{pessoal.pk}/lancamentos/')
        assert r.status_code == 200
        resultados['lista_pessoal'] = nomes(r.data)
        r = c.get(f'/api/espacos/{g.pk}/resumo/')
        assert r.status_code == 200, r.data
        resultados['resumo'] = {'qtd':r.data['qtd'],'total_centavos':r.data['total_centavos'],'por_casa_qtd':[x['qtd'] for x in r.data['por_casa']]}
        resultados['opcoes_filtros'] = {'chaves':list(lista()['opcoes']), 'casas_qtd':len(lista()['opcoes']['casas'])}
        r = c.get(base, {'subgrupo':'nenhum'})
        resultados['filtro_sem_casa_explicito'] = {'status':r.status_code,'resposta':r.data}
        assert resultados['lista_padrao'] == ['com_casa','sem_casa']
        assert resultados['filtro_meu_pagador_a_pagar'] == ['com_casa','sem_casa']
        assert resultados['mes_seguinte'] == ['outro_mes']
        assert resultados['resumo']['qtd'] == 2
        assert resultados['resumo']['por_casa_qtd'] == [1]
        transaction.set_rollback(True)
    assert not Usuario.objects.filter(pk=u.pk).exists()
resultados['rollback_confirmado'] = True
print(json.dumps(resultados,ensure_ascii=False,indent=2))
