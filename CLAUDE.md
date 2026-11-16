# Varal

App web mobile-first (PWA) para cadastrar e acompanhar contas (boletos e Pix) no espaço pessoal e em grupos familiares.
Objetivo: nenhuma conta vence sem que alguém saiba. Lê o código do boleto, do Pix e o PDF, gera recorrências e avisa por push e e-mail.
Monorepo: `api/` (Django + DRF + Celery), `web/` (Next.js), `infra/` (Docker Compose), `docs/`.

## Antes de qualquer tarefa

1. Leia `docs/PROGRESSO.md` (etapa atual, decisões, log).
2. Leia a spec da etapa atual: `docs/etapas/NN-slug/spec.md`.
3. Não trabalhe fora da etapa atual sem o dono do projeto pedir.
4. Se as fontes da verdade se contradizem (ajustes, especificação, canvas do Doop, guia `varal-ui`), **pare e pergunte**.

## Fontes da verdade (da mais forte para a mais fraca)

1. **"Varal — Ajustes"** (Claude Docs, doc `ce521944-15d6-44a5-b70c-f0790e03de41`): lido **sempre ao vivo** pelo conector claude.ai Claude Docs, no início e no fim de cada etapa. Vale mais que a especificação; um item escrito lá já conta como aprovação do dono do projeto. O Claude Code só **marca** itens como feitos (" — feito na etapa NN"), nunca apaga nem reescreve. Item ambíguo ou que exige mudar o Doop: perguntar no chat.
2. `docs/especificacao-varal.md`: cópia local da especificação (doc `c3529f9b-eb78-41e6-aa80-2a31957e189e`). Atualizar só reexportando a aba principal, nunca editando.
3. Canvas do Doop `k0kB5dc-Vo` e o guia `varal-ui`: toda a interface.

## Mapa da documentação

| Pasta / arquivo | Responde |
| --- | --- |
| `docs/README.md` | Índice: qual arquivo responde a qual pergunta |
| `docs/PROGRESSO.md` | Estado das etapas, decisões (pendentes e resolvidas), log |
| `docs/etapas/` | Tabela das etapas; `NN-slug/{spec,plano,tarefas,relatorio}.md` |
| `docs/matriz-rastreabilidade.md` | RF → CU → RN → tela → etapa → testes |
| `docs/produto/` | Visão, escopo do MVP, roadmap, atores e personas |
| `docs/requisitos/` | RF01–RF25, RNF01–RNF12 |
| `docs/casos-de-uso/` | CU01–CU12 (um arquivo cada) e diagrama de atores |
| `docs/regras-de-negocio/` | RN01–RN29 e ciclo de status |
| `docs/dados/modelo.md` | Entidades, campos, diagrama ER |
| `docs/arquitetura/` | Visão geral, stack, versões, ADRs |
| `docs/design/` | Doop (frames, componentes), tokens, movimento |
| `docs/api/README.md` | OpenAPI e geração de tipos |
| `docs/especificacao-varal.md` | Origem de tudo. **Nunca editar.** |

## Subagentes (`.claude/agents/`)

| Agente | Quando delegar |
| --- | --- |
| `varal-docs` | Início da etapa (spec, plano, tarefas) e fim (relatório, PROGRESSO, matriz) |
| `varal-boletos` | Linha digitável, Pix BR Code, leitura de PDF (`api/apps/boletos`) |
| `varal-backend` | Qualquer coisa em `api/`: modelos, permissões, endpoints, Celery |
| `varal-frontend` | Qualquer coisa em `web/`: telas e componentes (sempre lendo o Doop) |
| `varal-devops` | `infra/`, `Makefile`, `.github/`, variáveis de ambiente, deploy |
| `varal-qa` | Testes e critérios de aceite, ao fim de cada etapa e quando algo quebra |
| `varal-seguranca` | Revisão (somente leitura) antes de fechar etapa que toca dados, permissões, arquivos ou auth |
| `varal-decisor` | Triagem das decisões depois da spec, dúvida que trava um agente, auditoria antes do relatório |

**Política de decisões (vale para todo agente):** o teste é "quanto custa desfazer?". O que se desfaz só no código, sem mudar
o que alguém vê, o agente decide e registra em `docs/etapas/NN-slug/decisoes.md` (decisão, motivo, como desfazer).
Regra de negócio, privacidade/visibilidade, segurança, dados gravados, tela (inclusive número, ordem ou texto que muda) e
conflito entre fontes são sempre do dono: vão ao `varal-decisor` como pergunta. Detalhes em `.claude/agents/varal-decisor.md`.

Codex (GPT) usa as mesmas fontes via `AGENTS.md`: `.codex/agents/` e `.agents/skills/` são gerados destes arquivos
por `make codex-sync`. Mudou um agente ou comando aqui, rode `make codex-sync`.

Fluxo do `/etapa`: ler ajustes → merge local (`--no-ff`) da etapa anterior concluída → branch nova → docs (spec/plano/tarefas)
→ resumo e **parar até o ok** → boletos → backend → `make types` → frontend → devops → qa → segurança → revisão de ajustes
→ docs → commits locais → relatório e **parar**. `/status` mostra o estado sem alterar nada.

## Regra do Doop

- Nenhuma tela ou componente é construído sem antes ler o canvas **`k0kB5dc-Vo`** (conector claude.ai Doop, `agent_name "Claude Code"`, `get_guide` uma vez por sessão).
- O canvas é **somente leitura**: não criar, editar nem apagar frames, componentes ou tokens sem pedido explícito.
- Ache frames pelo **nome** (ids podem mudar). Tabela em `docs/design/README.md`.
- Toda tela cita os frames no topo: `// Doop: k0kB5dc-Vo / JJvrRugL0_ (02 · Início) + SMDsrD8FGT (D02 · Início)`.

## Regra responsiva

É **um só app**: mesmas rotas, componentes e dados; só o layout muda. Abaixo de 1024px: TabBar e folhas que sobem de baixo.
A partir de 1024px: SideNav fixo de 264px, folhas viram modais centralizados (M01–M06), Contas e Detalhe lado a lado (D03),
Avisos em gaveta lateral (D06). **Cada tela é entregue nas duas versões** (390×844 e 1440×900). Equivalências em `docs/design/README.md`.

## Rodar o projeto

Requisitos: Docker (com Compose), Node 22+ (para `make test-web`/`lint`/`types`), `npm ci` em `web/` na primeira vez.

| Comando | Faz |
| --- | --- |
| `make dev` | Cria `infra/.env` se faltar e sobe api, worker, beat, postgres, redis e web (http://localhost:3000) |
| `make down` | Para tudo |
| `make test` | pytest (api, no Compose) + Vitest (web) |
| `make e2e` | Sobe API/worker e dependências; Playwright inicia o Next e testa em 390×844 e 1440×900 |
| `make lint` | ruff (check + format) + ESLint + `tsc` |
| `make types` | Exporta/valida schema composto DRF + allauth (`export_schema`) e gera `web/src/types/api.ts` |
| `make migrate` | `makemigrations` + `migrate` |
| `make seed` | Dados de desenvolvimento (usuário `dev`) |

O S3 local (`pgsty/silo`, ADR 0002) fica no profile `storage`: `docker compose -f infra/docker-compose.yml --profile storage up -d minio`.

## Convenções

- Nomes de domínio em **português sem acento**, iguais ao modelo de dados (`lancamento`, `espaco`, `membro`, `subgrupo`, `instrumento`, `recorrencia`, `pagamento`, `historico`, `notificacao`). O resto do código e os comentários técnicos em inglês.
- Dinheiro em **centavos** (`int`); **UUID** como chave; datas em **UTC** no banco, exibidas em America/Fortaleza.
- Status gravados: `aguardando`, `pendente`, `paga`, `confirmada`, `cancelada`. "Vence em breve" e "vencida" são calculados (RN12).
- Permissão sempre no backend, por espaço, papel e visibilidade (RN01–RN07, RNF01).
- Testes de regra com o ID no nome: `test_rn14_data_pagamento_nao_pode_ser_futura`.
- Docs mudam no mesmo commit que o código. Mudar regra da especificação exige ADR + aprovação.
- Commits em **Conventional Commits, pt-BR** (`feat(api): ...`; ajustes: `fix(ajustes): ...`). **Sem push** sem pedido explícito; o único merge automático é o do `/etapa` (etapa anterior concluída → `main`, `--no-ff`).
- Segredos só em `infra/.env` (não versionado); `infra/.env.example` só com valores de desenvolvimento.
