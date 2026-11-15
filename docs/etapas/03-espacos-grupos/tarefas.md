# Tarefas — Etapa 03 (Espaços e grupos)

> **Contém:** checklist ordenada, responsáveis e critérios de aceite da Etapa 03.
> **Origem:** [spec.md](spec.md) e [plano.md](plano.md), com as decisões resolvidas em 14/11/2026.

Não se aplica `varal-boletos`. Perguntas Q1–Q5 da spec seguem o padrão indicado e vão para o relatório.

| # | Tarefa | Responsável | CA |
| --- | --- | --- | --- |
| 1 | [x] Apresentar escopo e decisões 1–8; ok do dono com correções (14/11/2026); docs, ADR 0004 e RN31 atualizados antes do código | orquestrador, varal-docs | todos |
| 2 | [x] Restrição grupo sem dono, `Membro`, `Convite` (`token_hash`, `revogado_em`), `Subgrupo`, migrações (com a de dados) e admin só leitura; testar RN03 e restrições | varal-backend | CA01–CA02 |
| 3 | [x] `acesso.py`: `espacos_do_usuario`, `papel`, `PERMISSOES` (com `ver_grupo`, pagador sem ele), `espaco_ou_404`; teste parametrizado papel × ação | varal-backend | CA10, CA15 |
| 4 | [x] Serviços com transação e `select_for_update`: grupo, convite (hash, 7 dias), revogação, aceite, papel, remoção, saída, casas; concorrência RN04/RN24 | varal-backend | CA01, CA03, CA05–CA07, CA12, CA14, CA16 |
| 5 | [x] Guarda RN04 na exclusão de `Usuario` (`pre_delete`, queryset e admin do Django com mensagem); `test_rn04_exclusao_usuario_ultimo_admin_*` | varal-backend | CA13 |
| 6 | [x] Endpoints do plano, `/api/me/` com `grupos`, 403 do pagador no detalhe, 404 para não membro, rotas aninhadas filtradas pelo espaço, throttle `convite_aceite` 10/h por usuário; seed com os quatro papéis | varal-backend | CA03–CA17 |
| 7 | [x] Rodar `make types`; versionar OpenAPI e tipos; regenerar sem diff | orquestrador | CA21 |
| 8 | [x] Reler 10, D04, 11, M05 e RadioCard/MemberRow/HouseCard (HTML + screenshot); sem escrever no Doop | varal-frontend | CA18–CA19 |
| 9 | [x] RadioCard, MemberRow, HouseCard e folha/modal `<dialog>` (`sheet-up`/`modal-pop`), `shine` 2× e reduced motion; vitrine; Vitest | varal-frontend | CA19–CA20 |
| 10 | [x] `/grupos/[id]` em três níveis (10/D04 com as diferenças do CA18), convite (11/M05, link encurtado, revogar ao trocar papel ou fechar sem usar), convites pendentes, gestão de membro e casa, sair | varal-frontend | CA07, CA09, CA11–CA12, CA14, CA16, CA18–CA20 |
| 11 | [x] `/grupos` (lista + criar), `/grupos/[id]/simples` ("Em breve" + sair), `/c/[token]`, `proximo` local, seletor do SideNav | varal-frontend | CA01, CA04–CA06, CA11, CA17 |
| 12 | [x] ~~Ajustar ambiente de E2E só se o fluxo com vários usuários exigir~~ (não foi necessário: o fixture do E2E espera e tenta de novo em 429; ver P5) | varal-devops | CA22 |
| 13 | [x] E2E com os quatro papéis e API real; comparação visual 390×844 e 1440×900 com as diferenças esperadas; `make test`, `make lint`, E2E | varal-qa | CA01–CA22 |
| 14 | [x] Revisar permissões por papel, IDOR, token (hash, entropia, uso único, revogação, ausência em logs/admin), throttle, `proximo`, concorrência, guarda de exclusão, vazamento de e-mail; corrigir bloqueantes | varal-seguranca; correções pelo agente da área | CA02–CA15, CA22 |
| 15 | [x] Reler "Varal — Ajustes" ao vivo; marcar só o concluído | orquestrador | CA22 |
| 16 | [x] Relatório (com Q1–Q5, rota do pagador e limite por usuário a confirmar); PROGRESSO, matriz, `dados/modelo.md`, `api/README.md`, `design/README.md`, `movimento.md` | varal-docs | CA22 |
| 17 | [x] Commits locais pt-BR, apresentar relatório e parar; sem push | orquestrador | CA22 |
