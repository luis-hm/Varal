# Tarefas — Etapa 04 (Contas, núcleo)

> **Contém:** checklist ordenada, responsáveis e critérios de aceite da Etapa 04.
> **Origem:** [spec.md](spec.md) (Q1–Q23 resolvidas em 15/11/2026) e [plano.md](plano.md).

Não se aplica `varal-boletos` (sem código de barras, Pix nem PDF nesta etapa).

| # | Tarefa | Responsável | CA |
| --- | --- | --- | --- |
| 1 | [x] Apresentar escopo e Q1–Q16; ok do dono; reexportar a especificação (rev 47, RF11 sem categoria); ADR 0005 e 0006 (RN32); reler `varal-ui`; ajustar docs com as respostas | orquestrador, varal-docs | todos |
| 2 | [x] Levar Q17–Q23 ao dono; spec, plano, ADR 0006 (dois caminhos), ADR 0007 (exceção RN05), ADR 0008 (RN06 sobre RN07), regras e matriz ajustados antes do código | orquestrador, varal-docs | CA09, CA16, CA19–CA25 |
| 3 | [ ] `Lancamento` (restrições RN11/RN12, índice, `acesso`), `Historico` (com as ações automáticas), `on_delete` da RN30, restrição da janela 1–7; migrações `lancamentos.0001` e `espacos.0006`; admin só leitura; sem categoria | varal-backend | CA02, CA04, CA10, CA11, CA26 |
| 4 | [ ] `acesso.py`: `lancamentos_visiveis` (pagador + acesso explícito, ADR 0008), `lancamento_ou_404` (404, nunca 403 para invisível), `quem_ve`; `com_status` com hoje em Fortaleza; testes por papel e visibilidade | varal-backend | CA05–CA10 |
| 5 | [ ] Serviços criar, editar (histórico só do que mudou; 400 da Q19b), cancelar; validação de casa (só quando muda), pagador (admin/membro/pagador) e escolhidos novos (admin/membro/observador) | varal-backend | CA01–CA04, CA12, CA13, CA25 |
| 6 | [ ] `_desligar` em dois modos (sair: 409 + `resolucoes` do ADR 0007; admin: cancela órfãs sem sinal); RN21; `alterar_papel` preserva acesso (ADR 0008); travas admins → membro → contas por `pk`; guarda RN32 `pre_delete` em `Usuario` e mensagem no admin do Django; `test_rn32_*`, `test_rn05_rn32_*`, `test_rn06_rn07_*` com concorrência | varal-backend | CA18–CA24 |
| 7 | [ ] Endpoints do plano (lista com filtros e contagens, resumo sem dados de pagamento, detalhe, PATCH, cancelar, `PATCH /api/grupos/{id}/` janela, `sair` com `resolucoes` e 409 `conta_restrita_orfa`; remover e alterar papel sem mudança de resposta); agregados e opções de filtro só sobre o visível; seed | varal-backend | CA01–CA26 |
| 8 | [ ] Rodar `make types`; versionar OpenAPI e tipos; regenerar sem diff | orquestrador | CA33 |
| 9 | [ ] Reler 02, D02, 03, D03, 07, 05, M01, 06, M02, 10, D04 e BillCard (HTML + screenshot); sem escrever no Doop | varal-frontend | CA29 |
| 10 | [ ] BillCard, formato R$/datas/mês em Fortaleza, `lib/contas`; espaço atual por cookie no seletor (SideNav e cabeçalho do Início); vitrine; Vitest | varal-frontend | CA14, CA27, CA32 |
| 11 | [ ] Início (02/D02): "Total de <mês>" com `count-up`, varal `swing` sem a conta "pagas", sem barra, "Precisa de atenção" com `rise`, "Por casa"; remover linha do healthcheck | varal-frontend | CA14, CA16, CA17, CA29, CA32 |
| 12 | [ ] Contas (03/D03) com "Total de <mês>", chips, filtros na URL, grupos por prazo; `/contas/[id]` com 07 no mobile e painel `slide-in` no desktop; 404 neutro; histórico com ações automáticas sem autor | varal-frontend | CA14, CA15, CA17, CA26, CA29, CA30 |
| 13 | [ ] Formulário criar/editar/cancelar (folha/modal), "Eu" pré-selecionado, aviso "Quem paga também vê esta conta", 400 da Q19b junto de "Quem vê", FAB e "Nova conta" do SideNav | varal-frontend | CA01, CA03, CA12, CA13, CA25, CA28, CA31 |
| 14 | [ ] Grupo: HouseCard com total e "N contas" (sem barra), "Configurações" só admin (janela 1–7); folha de saída barrada pela RN32 (escolher quem vê ou cancelar, depois sair); remoção sem mensagem nova; `/grupos/[id]/simples` com as contas do pagador | varal-frontend | CA09, CA11, CA16, CA22, CA23, CA27 |
| 15 | [ ] P5: taxa de cadastro do allauth por variável só no E2E/CI (`make e2e` e job `e2e`) | varal-devops | CA34 |
| 16 | [ ] E2E com papéis e API real (inclui admin não escolhido, pagador fora dos escolhidos, aviso de visibilidade, saída barrada e resolvida, remoção sem sinal ao admin); comparação visual 390×844 e 1440×900; `make test`, `make lint`, E2E | varal-qa | CA01–CA34 |
| 17 | [ ] Revisar visibilidade em lista/detalhe/agregados/filtros, 404 × 403, IDOR, validações, cookie do espaço, RN21, RN32 (dois modos), sinal ao admin, exceção da RN05 presa à saída, acesso preservado e concorrência; corrigir bloqueantes | varal-seguranca; correções pelo agente da área | CA04–CA09, CA18–CA25, CA34 |
| 18 | [ ] Reler "Varal — Ajustes" ao vivo; marcar só o concluído | orquestrador | CA34 |
| 19 | [ ] Relatório (decisões, Q17–Q23, confirmar que o aviso ao removido fica na 09, diferenças visuais); PROGRESSO, matriz, `dados/modelo.md`, `api/README.md`, `design/README.md`, `movimento.md` | varal-docs | CA34 |
| 20 | [ ] Commits locais pt-BR, apresentar relatório e parar; sem push | orquestrador | CA34 |
