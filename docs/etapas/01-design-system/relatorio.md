# Relatório — Etapa 01 (Design system no código)

> **Contém:** o que a Etapa 01 entregou, como foi verificada, decisões, desvios e pendências.
> **Origem:** escrito ao fim da Etapa 01 (12/11/2026), na branch `etapa/01-design-system` (commits `cc73bc1`, `5760613`, `ff6b761`, `1f084f6`).

## O que foi feito

**Tokens.** `web/src/styles/tokens.css` = saída de `get_tokens(format "css")` do canvas `k0kB5dc-Vo` (inclui `--text-4xl: 64px`; sem `--spacing-7`, de propósito), mais um bloco comentado **"fora do Doop"** (tabela abaixo). `globals.css`: reset, fundo, keyframe `press` e `prefers-reduced-motion`.

**Fontes.** Bricolage Grotesque e Inter via `next/font/google`, ligadas a `--font-display` e `--font-sans`, servidas pelo próprio app (o plano B, arquivos locais, não precisou).

**Marca.** Logo horizontal e símbolo (`components/ui/logo.tsx`) e favicon `app/icon.svg`, do frame Logo.

**Componentes** (props do Doop, um teste cada):

| Componente | Arquivo | Nota |
| --- | --- | --- |
| Icon (29 ícones, `sm\|md\|lg\|xl`) | `components/ui/icon.tsx` | |
| Button | `components/ui/button.tsx` | 52px em todos os tons (D1) |
| Chip | `components/ui/chip.tsx` | |
| Field | `components/ui/field.tsx` | |
| StatusBadge | `components/bills/status-badge.tsx` | com `cancelada` (D2); `badge-pulse` no Vencida |
| TopBar | `components/layout/top-bar.tsx` | |
| TabItem, TabBar | `components/layout/tab-bar.tsx` | |
| NavItem, SideNav | `components/layout/side-nav.tsx` | |
| AppShell | `components/layout/app-shell.tsx`, `app/(app)/layout.tsx` | TabBar < 1024px, SideNav fixo de 264px ≥ 1024px (D3) |

**Vitrine** `/dev/componentes`: todos os componentes e estados; 404 em produção (confirmado com `next build` + `next start`).

**Páginas "Em breve"** em `/`, `/contas`, `/grupos`, `/avisos`, `/perfil` (`components/layout/em-breve.tsx`); a `/` mantém a linha do healthcheck até a Etapa 04.

**Movimento.** `press` (botões) e `badge-pulse` (selo Vencida), ambos parados com `prefers-reduced-motion: reduce`.

**E2E.** Playwright 1.65.0, `playwright.config.ts`, alvo `make e2e`, `.gitignore` e job `e2e` em `.github/workflows/web.yml` (roda quando houver remoto). Testes em `web/e2e/design-system.spec.ts`; screenshots em `web/e2e/__screens__/`.

## Variáveis "fora do Doop"

Medidas que o CSS do Doop usa sem token. Nenhuma cor nova: as sombras usam `color-mix` sobre os tokens de cor.

| Nome | Valor | Origem no Doop |
| --- | --- | --- |
| `--text-2xs` | `11.5px` | TabItem, `.tab` font-size |
| `--text-logo` | `30px` | SideNav, `.logo b` |
| `--leading-none` | `1` | SideNav, `.logo b` |
| `--leading-body` | `22px` | estilo "Corpo" 15/22, frame Paleta e tipografia (EmBreve) |
| `--shadow-tabbar` | `0 -10px 30px color-mix(in srgb, var(--color-ink) 7%, transparent)` | TabBar `.tb`, `rgba(28,37,65,.07)` |
| `--shadow-fab` | `0 10px 24px color-mix(in srgb, var(--color-amber) 45%, transparent)` | TabBar `.fab` |
| `--shadow-cta` | `0 8px 20px color-mix(in srgb, var(--color-amber) 35%, transparent)` | SideNav `.new` |
| `--shadow-navitem` | `0 1px 0 var(--color-line), 0 0 0 1px var(--color-line)` | NavItem `on` |
| `--shadow-focus` | `0 0 0 4px var(--color-neutral-soft)` | Field `:focus-within` |

Medidas de espaço e tamanho que não são cor, sombra, fonte nem altura de linha (gaps de 6/10px, 52px, 264px) ficaram literais no CSS, usando `--spacing-*` quando o valor coincide.

## Critérios de aceite

| CA | Teste | Status |
| --- | --- | --- |
| CA01 | `tokens.test.ts`: `ca01: no hex colour…`, `ca01: CSS modules take colour…`, `ca01: the Doop block holds the get_tokens values…` | OK |
| CA02 | e2e `ca02: Bricolage Grotesque e Inter servidas pelo app…` | OK |
| CA03, CA04 | `icon.test.tsx`: `ca03`, `ca04` | OK |
| CA05 | `button.test.tsx` (`ca05`, `ca05/d1`); e2e `ca05/d1: Button renderizado com 52px…` | OK |
| CA06 | `chip.test.tsx`: `ca06` (2) | OK |
| CA07 | `field.test.tsx`: `ca07` (2) | OK |
| CA08 | `status-badge.test.tsx`: `ca08/rnf09` | OK |
| CA09 | `tokens.test.ts`: `ca09/rnf09` | OK |
| CA10 | `top-bar.test.tsx`: `ca10` | OK |
| CA11 | `nav.test.tsx`: `ca11` (TabBar e SideNav) | OK |
| CA12 | e2e `ca12` | OK |
| CA13 | e2e `rnf08 ca13` (vitrine e 5 páginas, 360px) | OK |
| CA14 | e2e `ca14` (screenshots) + comparação com o Doop | OK, com diferenças listadas abaixo |
| CA15 | e2e `ca15` + `ca15 (controle)` | OK |
| CA16 | `dev/componentes/page.test.tsx`: `ca16`; `next build` + `next start` → 404 | OK |
| CA17 | `make test`, `make lint` | OK (revalidação em 13/11/2026, abaixo) |
| CA18 | e2e `ca18` | OK |

Resultados iniciais (12/11/2026): Vitest 29/29; ESLint e `tsc` limpos; Playwright 26/26 (duas rodadas). **CA17:** `make test` e `make lint` não rodaram, porque a integração WSL do Docker Desktop estava desligada (`docker` não existia no WSL). A API não mudou; `ruff` local passou; `pytest` local deu 1 ok e 2 erros por falta de Postgres. Foi registrada a pendência P2.

**Revalidação em 13/11/2026:** Docker disponível. A primeira execução de `make test` falhou por credenciais do `.env` local incompatíveis com o volume PostgreSQL já inicializado. Após validar as credenciais de desenvolvimento documentadas, foram corrigidas apenas `POSTGRES_USER` e `POSTGRES_PASSWORD` no `.env` não versionado, sem alterar usuários ou dados do banco. `make test` passou (API 3/3; web 29/29) e `make lint` passou (ruff, ESLint e TypeScript). P2 resolvida e CA17 completo; merge desbloqueado. Sem mudança de código, o próprio `make test` serviu de verificação da correção de ambiente.

## Bugs corrigidos pelo QA

- Reduced motion não parava o pulso do selo Vencida (especificidade de seletor).
- ESLint lintava `playwright-report/`: adicionado ao `globalIgnores`.

## Comparação com o Doop (CA14)

Bate em cor, tipografia, raio, ícones, selos, botões, TabBar e SideNav. Diferenças restantes:

1. "Em breve" no desktop usa a TopBar centralizada (decisão do dono); os frames desktop têm h1 à esquerda, que entra com cada tela.
2. SideNav do shell sem seletor de espaço e rodapé de usuário (Etapas 02–03); por isso "Nova conta" fica mais alto que no D02.
3. Screenshot `fullPage` do desktop corta a borda do SideNav em 900px (sticky `100dvh`); efeito da captura.
4. Os previews de componente do Doop renderizam o Button com fonte de sistema e a TabBar em 228px (limite do preview); o frame 02 · Início bate.
5. Logo só na versão para fundo claro.
6. Contador de Avisos branco sobre `--color-red` tem ~3,9:1 (igual ao Doop; fora do CA09). Observação de acessibilidade para a auditoria da Etapa 11.

## Desvios deliberados (pedir confirmação ao dono)

1. **Chip**: pílula de 40px dentro de um `<button>` de 44px (RNF08), com `press`.
2. **Field**: prop `filled?: boolean` em vez de derivar do valor (`filled` = valor lido pelo sistema, fundo verde).
3. **TopBar**: `backHref?` opcional.
4. **SideNav**: `espaco` e `usuario` opcionais (dados reais nas Etapas 02–03).
5. **FAB "+" e "Nova conta"**: `<button>` sem ação (a tela Nova conta ainda não existe).
6. **`badge-pulse`**: keyframes no módulo do StatusBadge (CSS Modules renomeia animações); reduced-motion declarado por módulo.
7. **`/avisos` no mobile**: nenhuma aba fica ativa (a TabBar do Doop não tem Avisos).

## Segurança

`varal-seguranca` não se aplica: sem dados, permissões, arquivos nem auth; a vitrine não chama a API e é 404 em produção.

## Ambiente

- Node local v20.20.0 (o `CLAUDE.md` pede 22+); tudo passou mesmo assim.
- `next dev` 16 gera `web/AGENTS.md`; agora no `.gitignore`.
- O hook RTK quebra `npx next start`; usar `./node_modules/.bin/next`.

## Pendências

- **P2 resolvida em 13/11/2026**, conforme revalidação acima.
- Confirmar os desvios deliberados acima.
- CI no GitHub (inclui o job `e2e`) quando houver remoto.

## Ajustes aplicados

Nenhum item novo nesta revisão. Implementados no código nesta etapa (já marcados no documento na Etapa 00): D1, D2, D3, "Componentes novos" e "Animações" (só `press` e `badge-pulse`; `modal-pop`, `slide-in` e `scan` entram com as telas que os usam).

## Ajustes pendentes

- **"Variáveis do Google (Etapa 02)"**: `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` no `.env` da API (e no `.env.example` sem valores), via `SOCIALACCOUNT_PROVIDERS` do allauth; callback `http://localhost:8000/accounts/google/login/callback/`, origem `http://localhost:3000`; avisar no resumo se a URL mudar. Entra na spec da Etapa 02.
