# Spec — Etapa 01 (Design system no código)

> **Contém:** escopo, requisitos e telas cobertos, ajustes incluídos, critérios de aceite e o que fica fora da Etapa 01.
> **Origem:** [etapas/README.md](../README.md) (linha 01), [design/](../../design/README.md), decisões D1–D3 em [PROGRESSO](../../PROGRESSO.md) e documento "Varal — Ajustes" (rev 21, lido em 12/11/2026).

## Escopo

Levar o design system do Doop para `web/`, sem telas de produto:

1. **Tokens → CSS**: `web/src/styles/tokens.css` = saída de `get_tokens` (mesmos nomes, [tokens.md](../../design/tokens.md)). Medidas que o Doop usa sem token (ex.: sombra da TabBar, alturas de linha) viram variáveis extras (`--shadow-tabbar`, `--leading-tight`…) num bloco separado comentado **"fora do Doop"**, nunca valores soltos nos componentes. Os 64px do número-herói são o token `--text-4xl`. Não existir `--spacing-7` é intencional.
2. **Fontes**: Bricolage Grotesque e Inter via `next/font`, ligadas a `--font-display` e `--font-sans`.
3. **Logo** (horizontal e símbolo) e favicon, do frame Logo.
4. **Icon** com os 29 ícones (24 da seção 11 + `chevron`, `fechar`, `pdf`, `baixar`, `enviar`), tamanhos `sm|md|lg|xl`.
5. **Componentes base** com as props do Doop: Button (52px), Chip, Field, StatusBadge (com `cancelada`), TopBar, TabItem, TabBar, NavItem, SideNav.
6. **Shell responsivo**: TabBar abaixo de 1024px; SideNav fixo de 264px a partir de 1024px.
7. **Vitrine** `/dev/componentes`: rota só de desenvolvimento, para teste e comparação visual com o Doop.
8. **Páginas "Em breve"** em `/`, `/contas`, `/grupos`, `/avisos` e `/perfil`, dentro do shell, cada uma com TopBar e uma linha "Em breve", para navegar pela estrutura e ver o item ativo. Cada página é substituída na etapa da sua tela; `/perfil` continua "Em breve" (sem tela no Doop). Em `/`, a linha do healthcheck da Etapa 00 continua até a Etapa 04.
9. **Movimento** usado por estes componentes: `press` e `badge-pulse`, com `prefers-reduced-motion`.

## Requisitos cobertos

Nenhum RF, CU ou RN de negócio. Requisitos não funcionais:

| ID | Como esta etapa atende |
| --- | --- |
| RNF08 | Mobile-first a partir de 360px; alvos ≥ 44px; botões 52px |
| RNF09 | Contraste ≥ 4,5:1 nos pares de texto dos selos; status sempre com ícone e texto |

## Telas do Doop (canvas `k0kB5dc-Vo`)

| Página | Frames |
| --- | --- |
| 01 · Marca e ícones | Logo `t4pHch9UDR`, Paleta e tipografia `O5JpUML_Uw`, Ícones `FDDhQEf8T5` |
| 04 · Componentes (`page-mwdwblpn`) | Icon, StatusBadge, Button, Chip, Field, TopBar, TabItem, TabBar, NavItem, SideNav |
| Referência do shell (só a navegação) | 02 · Início `JJvrRugL0_` (TabBar) ↔ D02 · Início `SMDsrD8FGT` (SideNav) |

Ids podem mudar: o frontend confirma pelo **nome** com `get_canvas`.

## Ajustes incluídos

Do documento "Varal — Ajustes" (todos já marcados como feitos na Etapa 00; aqui entram no código):

| Item | Nesta etapa |
| --- | --- |
| D1 — botão 52px | Button com 52px de altura em todos os tons |
| D2 — StatusBadge `cancelada` | Ícone `fechar`, texto "Cancelada", fundo `--color-surface`, borda `--color-line`, texto `--color-ink-muted` |
| D3 — desktop no MVP | NavItem, SideNav e shell com troca em 1024px |
| Componentes novos | NavItem e SideNav |
| Animações (`modal-pop`, `slide-in`, `scan`) | Só documentadas; os keyframes entram com a primeira tela que os usa (modais na 03, D03 na 04, M02 na 06) |

## Critérios de aceite

Unitários: Vitest + Testing Library. Visuais e de layout: Playwright em 390×844 e 1440×900 na vitrine.

### Tokens e fontes

- CA01 — **Dado** `tokens.css`, **quando** comparado com `get_tokens(format "css")`, **então** nomes e valores são iguais, e `web/src/` não tem cor em hex fora de `tokens.css` e do favicon (`app/icon.svg`, arquivo isolado que não lê variáveis CSS). Os `*.module.css` não têm cor, sombra, tamanho de fonte nem altura de linha literais: tudo vem de `var(--…)`; as variáveis extras ficam no bloco "fora do Doop" de `tokens.css` e são listadas no relatório.
- CA02 — **Dado** a vitrine aberta, **quando** leio o estilo calculado de um título e de um texto, **então** usam Bricolage Grotesque e Inter servidas pelo próprio app (sem requisição ao Google no navegador).

### Icon

- CA03 — **Dado** cada um dos 29 nomes, **quando** renderizo `<Icon name>`, **então** sai um `<svg>` 24×24 com `stroke="currentColor"` e `aria-hidden="true"`.
- CA04 — **Dado** `size` `sm|md|lg|xl`, **quando** renderizo, **então** o tamanho é o do componente no Doop.

### Componentes

- CA05 — **Dado** um Button de qualquer `tone`, **quando** renderizado, **então** é um `<button>` com 52px de altura; com `width="full"` ocupa a largura do pai; só com ícone exige `aria-label` (D1).
- CA06 — **Dado** um Chip, **quando** clico, **então** `onClick` é chamado e `aria-pressed` reflete `state` (`on` = `true`); `count` aparece no texto.
- CA07 — **Dado** um Field com `label` e `hint`, **quando** renderizado, **então** o input tem nome acessível igual ao `label` e a dica em `aria-describedby`; no estado `error`, `aria-invalid="true"`.
- CA08 — **Dado** cada `status` (`aguardando`, `pendente`, `vence`, `vencida`, `paga`, `confirmada`, `cancelada`), **quando** renderizo o StatusBadge, **então** aparecem o ícone e o texto do Doop (RNF09); `cancelada` mostra `fechar` e "Cancelada" (D2).
- CA09 — **Dado** os pares texto/fundo dos selos e do texto principal em `tokens.css`, **quando** calculo o contraste, **então** todos são ≥ 4,5:1 (RNF09).
- CA10 — **Dado** a TopBar com `title` e `action`, **quando** renderizada, **então** o título é um cabeçalho e a ação aparece no slot.
- CA11 — **Dado** TabBar com `active` ou SideNav com `active`, **quando** renderizados, **então** o item ativo é o único com `aria-current="page"`, e cada item é um link com rótulo visível.

### Shell e vitrine

- CA12 — **Dado** a vitrine em 390×844, **quando** abro, **então** a TabBar aparece e o SideNav não; **dado** 1440×900, **então** o SideNav (264px, fixo) aparece e a TabBar não.
- CA13 — **Dado** a vitrine em 360px de largura, **quando** abro, **então** não há rolagem horizontal e todo botão ou link mede ≥ 44×44px (RNF08).
- CA14 — **Dado** a vitrine nas duas resoluções, **quando** comparo os screenshots com `get_frame_screenshot` / `get_component_preview` do Doop, **então** não há diferença visível de cor, tipografia, raio, espaçamento ou ícone; diferenças restantes ficam listadas no relatório com o motivo.
- CA15 — **Dado** `prefers-reduced-motion: reduce`, **quando** abro a vitrine, **então** o selo Vencida não pulsa e os botões não encolhem ao pressionar.
- CA16 — **Dado** o build de produção, **quando** acesso `/dev/componentes`, **então** recebo 404.
- CA17 — `make test` e `make lint` verdes.
- CA18 — **Dado** o app em 390×844 e em 1440×900, **quando** navego pela TabBar e pelo SideNav entre `/`, `/contas`, `/grupos`, `/avisos` (SideNav) e `/perfil`, **então** cada página mostra a TopBar com o título da seção e "Em breve", e o item da rota atual é o único com `aria-current="page"`.

## Fora de escopo

- Telas de produto (Início, Contas, Entrar…) e dados reais no shell (espaço, usuário): Etapas 02–04.
- Componentes das etapas seguintes: BillCard, RadioCard, MemberRow, HouseCard, RecurringRow, NoticeRow.
- Folhas, modais e gaveta, e as animações `swing`, `rise`, `grow`, `count-up`, `sheet-up`, `modal-pop`, `slide-in`, `scan`, `pop + draw`.
- Ícone de app e manifesto PWA (Etapa 11). (O job do Playwright entra no workflow `web.yml` agora, mas só roda quando houver remoto; localmente, `make e2e`.)
- API: nenhuma mudança; `make types` não roda.
