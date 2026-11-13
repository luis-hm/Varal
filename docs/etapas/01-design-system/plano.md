# Plano — Etapa 01 (Design system no código)

> **Contém:** o que cada agente faz na Etapa 01, arquivos e contratos (props e rotas), dependências novas e riscos.
> **Origem:** [spec.md](spec.md), [design/README.md](../../design/README.md) e o esqueleto `web/` da Etapa 00 ([relatório](../00-fundacao/relatorio.md)).

## Ponto de partida

`web/` tem Next.js 16.4 (App Router, `cacheComponents`), React 19.3, TanStack Query, Vitest 4 + Testing Library (jsdom) e ESLint do Next. Não há CSS global, `public/`, fontes nem componentes (`src/components/{ui,layout,bills}` vazios). Estilo: **CSS Modules** (nativo do Next) + `tokens.css` global.

## Agentes

| Agente | Faz |
| --- | --- |
| varal-boletos | Não se aplica. |
| varal-backend | Não se aplica (API não muda; sem `make types`). |
| varal-frontend | Lê o Doop, escreve tokens, fontes, logo, Icon, componentes, shell e vitrine; testes unitários junto. |
| varal-devops | `@playwright/test`, alvo `make e2e` e job `e2e` no `web.yml` (roda quando houver remoto). |
| varal-qa | Playwright da vitrine nas duas resoluções; confere CA01–CA17; preenche a matriz. |
| varal-seguranca | Não se aplica: não toca dados, permissões, arquivos nem auth. A vitrine não chama a API e dá 404 em produção. |
| varal-docs | Relatório, PROGRESSO, matriz e `design/README.md`. |

## Frontend — leitura do Doop

1. `get_guide(topic "doop-instructions")`, `agent_name "Claude Code"`; `get_canvas` e confirmar frames **pelo nome**.
2. `get_tokens(canvas_id "k0kB5dc-Vo", format "css")` → `tokens.css`; `get_guidelines("varal-ui")`.
3. Logo, Paleta e tipografia, Ícones: `get_frame` + `get_frame_screenshot(scale 2)`.
4. Cada componente da página 04: `get_component` (CSS, props, `code.path`) + `get_component_preview`.
5. Ícones: os 29 SVGs saem do HTML do componente `Icon` / frame Ícones (`get_component("Icon")`, `get_frame("FDDhQEf8T5")`), copiados como `<path>` no código. **Sem biblioteca de ícones.**

## Frontend — arquivos

| Arquivo | Conteúdo |
| --- | --- |
| `src/styles/tokens.css` | Saída literal de `get_tokens` + bloco separado `/* fora do Doop */` com as variáveis extras (medidas do CSS do Doop sem token, ex.: `--shadow-tabbar`, `--leading-tight`) |
| `src/styles/globals.css` | Importa tokens; reset mínimo; `--font-display`/`--font-sans` apontam para as variáveis do `next/font`; corpo em `--color-bg`; `@keyframes press`/`badge-pulse`; bloco `prefers-reduced-motion` |
| `src/app/layout.tsx` | Carrega fontes (`next/font/google`, `display: "swap"`, subset `latin`) e `globals.css` |
| `src/app/icon.svg` | Favicon do frame Logo |
| `src/components/ui/logo.tsx` | Logo horizontal e símbolo (`variant`), cores por `var(--…)` |
| `src/components/ui/icon.tsx` | `Icon` + tipo `IconName` (29 nomes) |
| `src/components/ui/{button,chip,field}.tsx` | Button, Chip, Field |
| `src/components/bills/status-badge.tsx` | StatusBadge |
| `src/components/layout/{top-bar,tab-bar,side-nav}.tsx` | TopBar; TabItem + TabBar; NavItem + SideNav |
| `src/components/layout/app-shell.tsx` | Client: lê `usePathname`, passa `active`, mostra TabBar ou SideNav por media query (1024px) |
| `src/app/(app)/layout.tsx` | Usa `AppShell`; as telas das próximas etapas entram neste grupo |
| `src/app/(app)/dev/componentes/page.tsx` | Vitrine: cada componente em todas as variantes; `notFound()` se `NODE_ENV === "production"` |
| `src/components/layout/em-breve.tsx` | TopBar com o título + "Em breve" (placeholder de seção) |
| `src/app/(app)/{page,contas/page,grupos/page,avisos/page,perfil/page}.tsx` | Uma linha cada: `<EmBreve title="…" />`. `/` (movida de `app/page.tsx`) mantém a linha do healthcheck até a Etapa 04 |

Cada componente com `*.module.css` ao lado e `*.test.tsx` (Vitest). Nenhum valor literal de cor, sombra, fonte ou altura de linha nos `*.module.css`: só `var(--…)`.

## Contratos (props = Doop)

| Componente | Props |
| --- | --- |
| Icon | `name: IconName`, `size?: "sm"\|"md"\|"lg"\|"xl"`, `label?` (sem `label` → `aria-hidden`) |
| Button | `tone: "primary"\|"secondary"\|"ghost"\|"success"\|"danger"`, `width?: "auto"\|"full"`, `label`, `icon?: IconName`, demais props de `<button>` |
| Chip | `state: "off"\|"on"`, `label`, `count?`, `onClick` |
| Field | `label`, `value`, `hint?`, `error?` (estado `error`), `trailing?: ReactNode`, `placeholder?`; `placeholder`/`filled` derivam do valor |
| StatusBadge | `status: "aguardando"\|"pendente"\|"vence"\|"vencida"\|"paga"\|"confirmada"\|"cancelada"` |
| TopBar | `title`, `action?: ReactNode` |
| TabItem / NavItem | `state: "off"\|"on"`, `label`, `icon: IconName`, `href`, `count?` (NavItem) |
| TabBar | `active?: "inicio"\|"contas"\|"grupos"\|"perfil"` |
| SideNav | `active?: "inicio"\|"contas"\|"grupos"\|"avisos"\|"perfil"`, `espaco?`, `usuario?` (texto do Doop na vitrine; dados reais nas Etapas 02–03) |

Rotas dos itens de navegação: `inicio` `/`, `contas` `/contas`, `grupos` `/grupos`, `avisos` `/avisos`, `perfil` `/perfil`. Até a etapa de cada tela, mostram a página "Em breve" (`/perfil` continua assim, sem tela no Doop). O botão + da TabBar e "Nova conta" do SideNav não fazem nada até a Etapa 04/06.

## Dependências novas

| Pacote | Por quê |
| --- | --- |
| `@playwright/test` (dev) | CA12–CA15 precisam de navegador real (jsdom não aplica media query); a Etapa 00 adiou o Playwright para cá. |

Fontes por `next/font/google`: já vem no Next, baixa no build e serve do próprio domínio. Nada mais (sem lib de ícones, CSS-in-JS, jest-dom ou axe).

## Devops

- `web/package.json`: script `e2e` (`playwright test`); `web/playwright.config.ts` com projetos 390×844 e 1440×900 e `webServer: npm run dev` (vitrine não precisa da API).
- `Makefile`: alvo `e2e` (`cd web && npx playwright install chromium && npm run e2e`). `make test` continua sem e2e.
- `.gitignore`: `web/test-results/`, `web/playwright-report/`.
- `.github/workflows/web.yml`: job `e2e` (Node 22, `npm ci`, `npx playwright install --with-deps chromium`, `npm run e2e`, relatório como artefato em falha). Roda quando houver remoto; localmente, `make e2e`.

## QA

- `web/e2e/design-system.spec.ts`: CA02, CA12, CA13, CA15, CA16 (este no `next build && next start`, ou checado por teste unitário da guarda).
- Screenshots em `web/e2e/__screens__/` (390×844 e 1440×900) para CA14, comparados com o Doop.
- Nomes com ID: `it("rnf09: status nunca só por cor …")`, `it("rnf08: alvos ≥ 44px …")`.

## Migrações

Nenhuma.

## Riscos

| Risco | Mitigação |
| --- | --- |
| `tokens.md` diverge do Doop atual (ex.: `--spacing-1…8` lista 7 valores) | Vale `get_tokens`; divergência vira nota no relatório e correção em `tokens.md`. Token **faltando**: parar e perguntar. |
| Valores sem token no Doop (sombra da TabBar, alturas de linha) | Decidido pelo dono: valor do CSS do Doop vira variável extra no bloco "fora do Doop" de `tokens.css`, listada no relatório; nunca literal no componente. 64px = token `--text-4xl` (reler `get_tokens`). Sem `--spacing-7` é intencional. Cor sem token: parar e perguntar. |
| Ids de frame mudarem | Procurar pelo nome; atualizar `design/README.md`. |
| `next/font/google` precisa de rede no build (Docker/CI) | Se falhar, trocar por `next/font/local` com os arquivos no repo (OFL) e registrar no relatório. |
| Bricolage Grotesque é variável (eixos `opsz`, `wdth`) | Carregar só os pesos usados (700, 800) e conferir com o screenshot do Doop. |
| Playwright precisa de dependências de sistema no WSL | `npx playwright install --with-deps chromium`; se bloquear, reportar como pendência. |
| SVG do Doop com cor fixa em vez de `currentColor` | Trocar por `currentColor` ao copiar; ícones de status recebem cor do selo. |
