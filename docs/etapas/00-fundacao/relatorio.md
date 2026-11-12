# Relatório — Etapa 00 (Fundação)

> **Contém:** o que a Etapa 00 entregou, como foi verificada, decisões, desvios do plano e pendências.
> **Origem:** escrito ao fim da Etapa 00 (12/11/2026), na branch `etapa/00-fundacao`.

## O que foi feito

**Fontes.** `docs/especificacao-varal.md` já existia (13 seções conferidas); o conector Claude Docs não foi necessário. Doop funcionando: `get_guide`, `get_canvas`, guia `varal-ui`, tokens e 16 componentes lidos.

**Repositório.** Git com `main` (só a especificação) e branch `etapa/00-fundacao`. Monorepo: `api/`, `web/`, `infra/`, `docs/`, `.github/workflows/`, `.claude/agents/` (7 agentes), `.claude/commands/` (`/etapa`, `/status`), `CLAUDE.md`, `Makefile`.

**Docs.** Especificação quebrada em `produto/`, `requisitos/`, `casos-de-uso/` (12 CUs), `regras-de-negocio/`, `dados/`, `arquitetura/`, `design/` por cópia literal via script (faixas de linha). Três diagramas recriados em Mermaid (status, arquitetura, atores × CUs) e diagrama ER derivado do modelo. Matriz de rastreabilidade inicial, ADR 0001 e `docs/api/README.md`.

**API.** Django 6.1 + DRF 3.18 + drf-spectacular 0.30: `GET /api/health/` (testa o banco), `/api/schema/`, `/api/docs/`. Celery 5.7 com tarefa `ping`. Sete apps de domínio vazios registrados. Usuário próprio `contas_usuario.Usuario` (UUID, e-mail único) com migração `0001`. Comando `seed` (usuário dev, só com `DEBUG`).

**Web.** Next.js 16.4 + React 19.3 + TanStack Query: a página `/` chama `/api/health/` pelo proxy same-origin do Next (rewrites para `http://api:8000`). Tipos gerados: `api/openapi.yaml` → `web/src/types/api.ts`.

**Infra.** Compose com postgres 17, redis 7, api (roda `migrate` ao subir), worker, beat e web; MinIO atrás do profile `storage`. CI: `api.yml` (ruff, pytest com postgres, job `types` que falha se houver diff) e `web.yml` (lint, typecheck, vitest).

## Verificação

Feita em 12/11/2026, localmente.

| Verificação | Resultado |
| --- | --- |
| `make dev` | sobem api, worker, beat, postgres, redis, web |
| `GET :8000/api/health/` e `GET :3000/api/health/` | `{"status":"ok"}` |
| `GET :3000/` | 200 |
| tarefa `ping` no worker | `'pong'` |
| `make test` | pytest 3 passed; vitest 2 passed |
| `make lint` | verde (ruff check/format, eslint, tsc) |
| `make types` | ok |
| `make seed` | usuário dev criado |
| CI no GitHub | **não executado** (sem remoto/push) |

Testes: `api/tests/test_fundacao.py` (`test_health_ok`, `test_schema_documents_health`, `test_celery_ping_task`) e `web/src/app/page.test.tsx` (2 testes).

## Decisões

- Usuário próprio desde a Etapa 00: trocar `AUTH_USER_MODEL` depois é caro.
- DRF autenticado por padrão.
- Proxy `/api` same-origin no Next: cookies first-party para o allauth headless.
- nginx adiado para a Etapa 11 (deploy).
- Dependências de etapas futuras (allauth, pdfplumber, S3, web push, Playwright) não instaladas ainda.

## Desvios do plano

1. **MinIO.** As imagens oficiais (`minio/minio` no Docker Hub e `quay.io/minio/minio`) não estão mais acessíveis. O compose aponta provisoriamente para `pgsty/minio`, atrás do profile `storage`. Essa imagem **não foi executada** (bloqueada pela checagem de segurança por ser de terceiros). Ver D4.
2. **nginx** não criado (adiado para a Etapa 11).
3. **Apps vazios** ganharam `apps.py` (necessário para registrá-los) em vez de README.
4. **Agente `varal-docs`** não pôde ser chamado pelo nome nesta sessão (agentes de `.claude/agents` só carregam em sessão nova); este relatório foi escrito por um agente genérico seguindo as instruções do `varal-docs`.

## Pendências

- Decisões D1–D6 em [PROGRESSO](../../PROGRESSO.md#decisões): altura do botão (52 × 48 px); `StatusBadge` sem `cancelada`; desktop/SideNav/D02 fora da especificação; imagem do MinIO; RNF04 (LGPD) sem etapa; merge da `etapa/00-fundacao` na `main` antes do `/etapa 01`.
- Rodar o CI no GitHub quando houver remoto.
- Playwright entra na Etapa 01.

## Ajustes aplicados

Do documento "Varal — Ajustes" (Claude Docs `ce521944-15d6-44a5-b70c-f0790e03de41`), em 12/11/2026, commits `fix(ajustes): …`:

| Item | Onde ficou |
| --- | --- |
| Documento de ajustes como fonte | `CLAUDE.md`, `docs/README.md` |
| Comando /etapa (ler ajustes, revisão de ajustes, merge da etapa anterior) | `.claude/commands/etapa.md` |
| Especificação reexportada (seção 12 com telas desktop) | `docs/especificacao-varal.md`, `docs/design/README.md` |
| Páginas do Doop e frames desktop | `docs/design/README.md` |
| Regra responsiva | `docs/design/README.md`, `CLAUDE.md` |
| NavItem, SideNav e shell responsivo na Etapa 01 | `docs/design/README.md`, `docs/etapas/README.md`, `PROGRESSO.md` |
| Animações modal-pop, slide-in, scan | `docs/design/movimento.md` (conferido com `varal-ui`) |
| Agentes de frontend e QA em 390×844 e 1440×900 | `.claude/agents/varal-frontend.md`, `varal-qa.md` |
| Matriz com frame mobile ↔ desktop | `docs/matriz-rastreabilidade.md` |
| D1–D6 | `PROGRESSO.md` (resolvidas), ADR 0002 (D4), ADR 0003 / RN30 (D5), merge local (D6) |

## Ajustes pendentes

- Nenhum item do documento ficou pendente. Pendência operacional: P1 em `PROGRESSO.md` (rodar uma vez o serviço `minio` com `pgsty/silo`; a execução foi bloqueada pela checagem de segurança do agente).
