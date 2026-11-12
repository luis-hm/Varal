# Varal

App web mobile-first (PWA) para cadastrar e acompanhar contas (boletos e Pix) no espaço pessoal e em grupos familiares.
Objetivo: nenhuma conta vence sem que alguém saiba. Lê o código do boleto, do Pix e o PDF, gera recorrências e avisa por push e e-mail.
Monorepo: `api/` (Django + DRF + Celery), `web/` (Next.js), `infra/` (Docker Compose), `docs/`.

## Antes de qualquer tarefa

1. Leia `docs/PROGRESSO.md` (etapa atual, decisões pendentes, log).
2. Leia a spec da etapa atual: `docs/etapas/NN-slug/spec.md`.
3. Não trabalhe fora da etapa atual sem o dono do projeto pedir.
4. Se as fontes da verdade se contradizem (especificação, canvas do Doop, guia `varal-ui`), **pare e pergunte**.

## Mapa da documentação

| Pasta / arquivo | Responde |
| --- | --- |
| `docs/README.md` | Índice: qual arquivo responde a qual pergunta |
| `docs/PROGRESSO.md` | Estado das etapas, decisões pendentes, log |
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

Fluxo do `/etapa`: docs (spec/plano/tarefas) → resumo e **parar até o ok** → boletos → backend → `make types` → frontend →
devops → qa → segurança → docs → commits locais → relatório e **parar**. `/status` mostra o estado sem alterar nada.

## Regra do Doop

- Nenhuma tela ou componente é construído sem antes ler o canvas **`k0kB5dc-Vo`** (conector claude.ai Doop, `agent_name "Claude Code"`, `get_guide` uma vez por sessão).
- O canvas é **somente leitura**: não criar, editar nem apagar frames, componentes ou tokens sem pedido explícito.
- Ache frames pelo **nome** (ids podem mudar). Tabela em `docs/design/README.md`.
- Toda tela cita o frame no topo: `// Doop: k0kB5dc-Vo / JJvrRugL0_ (02 · Início)`.

## Rodar o projeto

Requisitos: Docker (com Compose), Node 22+ (para `make test-web`/`lint`/`types`), `npm ci` em `web/` na primeira vez.

| Comando | Faz |
| --- | --- |
| `make dev` | Cria `infra/.env` se faltar e sobe api, worker, beat, postgres, redis e web (http://localhost:3000) |
| `make down` | Para tudo |
| `make test` | pytest (api, no Compose) + Vitest (web) |
| `make lint` | ruff (check + format) + ESLint + `tsc` |
| `make types` | Gera `api/openapi.yaml` e `web/src/types/api.ts` |
| `make migrate` | `makemigrations` + `migrate` |
| `make seed` | Dados de desenvolvimento (usuário `dev`) |

MinIO fica atrás do profile `storage` até a decisão D4 (ver `docs/PROGRESSO.md`).

## Convenções

- Nomes de domínio em **português sem acento**, iguais ao modelo de dados (`lancamento`, `espaco`, `membro`, `subgrupo`, `instrumento`, `recorrencia`, `pagamento`, `historico`, `notificacao`). O resto do código e os comentários técnicos em inglês.
- Dinheiro em **centavos** (`int`); **UUID** como chave; datas em **UTC** no banco, exibidas em America/Fortaleza.
- Status gravados: `aguardando`, `pendente`, `paga`, `confirmada`, `cancelada`. "Vence em breve" e "vencida" são calculados (RN12).
- Permissão sempre no backend, por espaço, papel e visibilidade (RN01–RN07, RNF01).
- Testes de regra com o ID no nome: `test_rn14_data_pagamento_nao_pode_ser_futura`.
- Docs mudam no mesmo commit que o código. Mudar regra da especificação exige ADR + aprovação.
- Commits em **Conventional Commits, pt-BR** (`feat(api): ...`). **Sem push nem merge** sem pedido explícito.
- Segredos só em `infra/.env` (não versionado); `infra/.env.example` só com valores de desenvolvimento.
