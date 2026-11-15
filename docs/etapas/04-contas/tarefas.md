# Tarefas — Etapa 04 (Contas, núcleo)

> **Contém:** checklist ordenada, responsáveis e critérios de aceite da Etapa 04.
> **Origem:** [spec.md](spec.md) (decisões resolvidas em 15/11/2026; Q17–Q23 abertas) e [plano.md](plano.md).

Não se aplica `varal-boletos` (sem código de barras, Pix nem PDF nesta etapa).

| # | Tarefa | Responsável | CA |
| --- | --- | --- | --- |
| 1 | [x] Apresentar escopo e Q1–Q16; ok do dono; reexportar a especificação (rev 47, RF11 sem categoria); ADR 0005 e 0006 (RN32); reler `varal-ui`; ajustar docs com as respostas | orquestrador, varal-docs | todos |
| 2 | [ ] Levar Q17–Q23 ao dono; ajustar spec/plano com as respostas antes do código que depende delas | orquestrador | CA16, CA19, CA20 |
| 3 | [ ] `Lancamento` (restrições RN11/RN12, índice, `acesso`), `Historico`, `on_delete` da RN30, restrição da janela 1–7; migrações `lancamentos.0001` e `espacos.0006`; admin só leitura; sem categoria | varal-backend | CA02, CA04, CA10, CA11, CA21 |
| 4 | [ ] `acesso.py`: `lancamentos_visiveis`, `lancamento_ou_404` (404, nunca 403 para invisível), `quem_ve`; `com_status` com hoje em Fortaleza; testes por papel e visibilidade | varal-backend | CA05–CA10 |
| 5 | [ ] Serviços criar, editar (histórico só do que mudou), cancelar; validação de casa, pagador (admin/membro/pagador) e escolhidos (admin/membro/observador) | varal-backend | CA01–CA04, CA12, CA13 |
| 6 | [ ] RN21 + RN32 em `_desligar` (travas: admins → membro → contas por `pk`); guarda RN32 `pre_delete` em `Usuario` e mensagem no admin do Django; `test_rn32_*` com concorrência | varal-backend | CA18, CA19 |
| 7 | [ ] Endpoints do plano (lista com filtros e contagens, resumo sem dados de pagamento, detalhe, PATCH, cancelar, `PATCH /api/grupos/{id}/` janela, 409 `conta_restrita_orfa`); agregados e opções de filtro só sobre o visível; seed | varal-backend | CA01–CA19, CA21 |
| 8 | [ ] Rodar `make types`; versionar OpenAPI e tipos; regenerar sem diff | orquestrador | CA28 |
| 9 | [ ] Reler 02, D02, 03, D03, 07, 05, M01, 06, M02, 10, D04 e BillCard (HTML + screenshot); sem escrever no Doop | varal-frontend | CA24 |
| 10 | [ ] BillCard, formato R$/datas/mês em Fortaleza, `lib/contas`; espaço atual por cookie no seletor (SideNav e cabeçalho do Início); vitrine; Vitest | varal-frontend | CA14, CA22, CA27 |
| 11 | [ ] Início (02/D02): "Total de <mês>" com `count-up`, varal `swing`, sem barra, "Precisa de atenção" com `rise`, "Por casa"; remover linha do healthcheck | varal-frontend | CA14, CA16, CA17, CA24, CA27 |
| 12 | [ ] Contas (03/D03) com "Total de <mês>", chips, filtros na URL, grupos por prazo; `/contas/[id]` com 07 no mobile e painel `slide-in` no desktop; 404 neutro | varal-frontend | CA14, CA15, CA17, CA24, CA25 |
| 13 | [ ] Formulário criar/editar/cancelar (folha/modal), "Eu" pré-selecionado, aviso "Quem paga também vê esta conta", FAB e "Nova conta" do SideNav | varal-frontend | CA01, CA03, CA12, CA13, CA23, CA26 |
| 14 | [ ] Grupo: HouseCard com total e "N contas" (sem barra), "Configurações" só admin (janela 1–7); mensagem do 409 RN32 em sair/remover; `/grupos/[id]/simples` com as contas do pagador | varal-frontend | CA09, CA11, CA16, CA20, CA22 |
| 15 | [ ] P5: taxa de cadastro do allauth por variável só no E2E/CI (`make e2e` e job `e2e`) | varal-devops | CA29 |
| 16 | [ ] E2E com papéis e API real (inclui admin não escolhido, pagador fora dos escolhidos, aviso de visibilidade, bloqueio RN32); comparação visual 390×844 e 1440×900; `make test`, `make lint`, E2E | varal-qa | CA01–CA29 |
| 17 | [ ] Revisar visibilidade em lista/detalhe/agregados/filtros, 404 × 403, IDOR, validações, cookie do espaço, RN21, RN32 e concorrência; corrigir bloqueantes | varal-seguranca; correções pelo agente da área | CA04–CA09, CA18, CA19, CA29 |
| 18 | [ ] Reler "Varal — Ajustes" ao vivo; marcar só o concluído | orquestrador | CA29 |
| 19 | [ ] Relatório (decisões, Q17–Q23 e diferenças visuais); PROGRESSO, matriz, `dados/modelo.md`, `api/README.md`, `design/README.md`, `movimento.md` | varal-docs | CA29 |
| 20 | [ ] Commits locais pt-BR, apresentar relatório e parar; sem push | orquestrador | CA29 |
