# ADR 0001 — Monorepo com Django e Next.js

> **Contém:** a decisão de estrutura do repositório e da stack principal.
> **Origem:** `docs/especificacao-varal.md`, seção 9, e as decisões do prompt de fundação.

- **Status:** aceita (12/11/2026)

## Contexto

O Varal precisa ler PDFs e códigos de boleto, rodar tarefas agendadas (recorrências, lembretes) e, na v3, gerar relatórios financeiros. O front é um PWA mobile-first. Uma pessoa mantém o projeto com ajuda de agentes, então contrato de API e tipos precisam ficar sincronizados sem esforço manual.

## Decisão

- Um repositório: `api/` (Django + DRF + Celery), `web/` (Next.js App Router + TypeScript), `infra/`, `docs/`, `Makefile`, `.github/workflows/`.
- Sem Turborepo nem Nx: só o `web/` é JavaScript; o `Makefile` orquestra.
- CI separado por pasta (`api.yml` para `api/**`, `web.yml` para `web/**`).
- Contrato único em OpenAPI (drf-spectacular), com tipos do front gerados (`make types`) e checados no CI.
- Docker Compose para desenvolvimento e para a VPS.

## Consequências

- Uma mudança de API e a tela que a usa entram no mesmo commit.
- O ecossistema Python cobre PDF (pdfplumber), filas (Celery) e relatórios.
- Dois toolchains (uv e npm), mas cada um isolado na sua pasta.
