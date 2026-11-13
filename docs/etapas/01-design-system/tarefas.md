# Tarefas — Etapa 01 (Design system no código)

> **Contém:** a checklist ordenada da Etapa 01, com o agente responsável e o critério de aceite de cada item.
> **Origem:** [spec.md](spec.md) e [plano.md](plano.md).

Não se aplica nesta etapa: **varal-boletos**, **varal-backend** e `make types` (API não muda), **varal-seguranca** (sem dados, permissões, arquivos nem auth).

| # | Tarefa | Agente | CA |
| --- | --- | --- | --- |
| 1 | [x] Ler o Doop: guia, `get_canvas`, frames da página 01 pelo nome, tokens, `varal-ui`, componentes da página 04; anotar divergências com `tokens.md` | varal-frontend | — |
| 2 | [x] `tokens.css` (saída de `get_tokens`) e `globals.css` (reset, fontes, fundo, keyframes `press`/`badge-pulse`, reduced-motion) | varal-frontend | CA01, CA15 |
| 3 | [x] Fontes com `next/font/google` no `layout.tsx` | varal-frontend | CA02 |
| 4 | [x] Logo (horizontal e símbolo) e favicon `app/icon.svg` | varal-frontend | CA14 |
| 5 | [x] `Icon` com os 29 SVGs do Doop + teste | varal-frontend | CA03, CA04 |
| 6 | [x] Button (52px, D1) + teste | varal-frontend | CA05 |
| 7 | [x] Chip + teste | varal-frontend | CA06 |
| 8 | [x] Field + teste | varal-frontend | CA07 |
| 9 | [x] StatusBadge com `cancelada` (D2) + teste de ícone/texto e de contraste | varal-frontend | CA08, CA09 |
| 10 | [x] TopBar + teste | varal-frontend | CA10 |
| 11 | [x] TabItem/TabBar e NavItem/SideNav + teste | varal-frontend | CA11 |
| 12 | [x] `AppShell` e `(app)/layout.tsx` com troca em 1024px (D3) | varal-frontend | CA12 |
| 13 | [x] Vitrine `/dev/componentes` (404 em produção) | varal-frontend | CA16 |
| 13b | [x] Páginas "Em breve" (`/`, `/contas`, `/grupos`, `/avisos`, `/perfil`) no grupo `(app)`; `/` mantém o healthcheck | varal-frontend | CA18 |
| 14 | [x] Comparar a vitrine com o Doop em 390×844 e 1440×900; listar diferenças | varal-frontend | CA14 |
| 15 | [x] `@playwright/test`, `playwright.config.ts`, script `e2e`, alvo `make e2e`, `.gitignore`, job `e2e` em `.github/workflows/web.yml` | varal-devops | — |
| 16 | [x] E2E da vitrine e da navegação "Em breve" nas duas resoluções; screenshots em `web/e2e/__screens__/` | varal-qa | CA02, CA12–CA16, CA18 |
| 17 | [x] `make test`, `make lint`, `make e2e`; conferir CA01–CA17 (parcial: `make test` e `make lint` não rodaram, ver P2) | varal-qa | CA17 |
| 18 | [x] Revisão do documento "Varal — Ajustes" (ao vivo): marcar itens feitos, sem apagar | orquestrador | — |
| 19 | [x] `relatorio.md`; PROGRESSO (etapa concluída, log); matriz (RNF08, RNF09: testes); `design/README.md` (componentes feitos, vitrine) e `tokens.md` se divergiu | varal-docs | — |
