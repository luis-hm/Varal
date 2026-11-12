# Design — canvas do Doop

> **Contém:** onde está cada tela e componente no Doop, como lê-los, a regra responsiva e as telas e ícones da especificação.
> **Origem:** canvas Doop `k0kB5dc-Vo` (lido em 12/11/2026), guia `varal-ui` e `docs/especificacao-varal.md`, seções 11 e 12.

## Regras

- **Nenhuma tela ou componente é construído sem antes ser lido no canvas.** O canvas é **somente leitura**.
- Conector **claude.ai Doop** (ferramentas `mcp__claude_ai_Doop__*`). Uma vez por sessão: `get_guide(topic: "doop-instructions")`. Sempre `agent_name: "Claude Code"`.
- Ids de frame podem mudar se alguém recriar um frame: confirme com `get_canvas` e **procure pelo nome**.
- Por tela: ler **os dois frames** (mobile e desktop) com `get_frame` (HTML) + `get_frame_screenshot(scale 2)`; para cada `<doop-use component="X">`, `get_component("X")` → `code.path`.
- Guia fixado: `varal-ui` ("Varal · regras de interface"), via `get_guidelines`. Tokens: [tokens.md](tokens.md). Animações: [movimento.md](movimento.md).

## Regra responsiva

É **um só app**. Mesmas rotas, componentes e dados; só o layout muda. Cada tela é entregue nas duas versões, na mesma etapa.

| | Mobile (< 1024px) | Desktop (≥ 1024px) |
| --- | --- | --- |
| Referência | 390×844 | 1440×900 |
| Navegação | TabBar inferior com botão + âmbar central | SideNav fixo de 264px à esquerda (logo, seletor de espaço, Nova conta, NavItems, usuário) |
| Ações (nova conta, pagar, convidar…) | Folhas que sobem de baixo (`sheet-up`) | Modais centralizados M01–M06 (`modal-pop`), no tamanho da própria janela |
| Contas e Detalhe | Telas separadas (03 e 07) | Lado a lado (D03): lista 540px + painel de detalhe (`slide-in`) |
| Avisos | Tela própria (04) | Gaveta lateral de 440px (D06) aberta pelo sino |
| Conferir conta | Tela (06) | Modal largo com prévia do PDF e campos lidos destacados (M02, `scan`) |
| Margens | Lateral 20px (cards 12px) | Conteúdo com padding 28px 40px |

Em qualquer tamanho: alvo mínimo 44px, botões 52px. Número-herói 48px no mobile e 64px no desktop.

## Canvas

[Varal no Doop](https://doop.design/c/k0kB5dc-Vo)

| Página | Id |
| --- | --- |
| 01 · Marca e ícones | `k0kB5dc-Vo:page1` |
| 02 · Telas mobile | `-eLoZ0SLb1` |
| 03 · Telas desktop | `YGk9_iqJ-Y` |
| 04 · Componentes | `page-mwdwblpn` |

### Marca (página 01)

| Frame | Nome | Tamanho | Etapa |
| --- | --- | --- | --- |
| `t4pHch9UDR` | Logo | 1200×720 | 01 |
| `O5JpUML_Uw` | Paleta e tipografia | 1200×900 | 01 |
| `FDDhQEf8T5` | Ícones | 1200×684 | 01 |

### Telas: mobile (página 02) ↔ desktop (página 03)

| Mobile | Frame mobile | Desktop | Frame desktop | Etapa |
| --- | --- | --- | --- | --- |
| 01 · Entrar | `GJDSPaQbio` | D01 · Entrar | `7JTmWMAJup` | 02 |
| 02 · Início | `JJvrRugL0_` | D02 · Início | `SMDsrD8FGT` | 04 |
| 03 · Contas | `bdiED7Q0I-` | D03 · Contas + Detalhe | `cWdVUX2y8H` | 04 |
| 04 · Avisos | `fcR9RDu79a` | D06 · Avisos (gaveta lateral) | `aYT5zpG8_w` | 09 |
| 05 · Nova conta | `0PfC8pBVwF` | M01 · Nova conta (modal) | `oOhe6pYOzx` | 06 |
| 06 · Conferir conta | `tKY4nFTZ3-` | M02 · Conferir conta (modal) | `Sre1zOcaE-` | 06 |
| 07 · Detalhe da conta | `efJzW9e5vx` | D03 · Contas + Detalhe | `cWdVUX2y8H` | 04 e 06 |
| 08 · Marcar como paga | `-RwBuRqs8G` | M03 · Marcar como paga (modal) | `feyLdQSk81` | 07 |
| 09 · Conta paga | `y1NUSjOnMM` | M04 · Conta paga (modal) | `CB5AeHekwg` | 07 |
| 10 · Grupo | `SfhuKVOQIF` | D04 · Grupo | `5UzCB5yNaI` | 03 |
| 11 · Convidar membro | `bkv_O9ohNO` | M05 · Convidar membro (modal) | `8XSFrkwy2d` | 03 |
| 12 · Pedir para alguém pagar | `MFZW3LUORq` | M06 · Pedir para alguém pagar (modal) | `3OQOmTm6BG` | 10 |
| 13 · Modo simples (pagador) | `mIvLheR2TS` | D05 · Modo simples (pagador) | `YTtAtGSyCI` | 10 |

Tamanhos: telas mobile 390×844 (06: 390×1090; 07: 390×1220; 10: 390×944); telas desktop 1440×900; gaveta D06 440×900; modais no tamanho da janela (M01 560×590, M02 1040×660, M03 520×450, M04 480×520, M05 560×560, M06 560×530).

### Componentes (página 04)

| Componente | Props (do Doop) | Caminho no código | Etapa |
| --- | --- | --- | --- |
| Icon | `name` (29 nomes), `size: sm\|md\|lg\|xl` | `web/src/components/ui/icon.tsx` | 01 |
| StatusBadge | `status: aguardando\|pendente\|vence\|vencida\|paga\|confirmada\|cancelada` | `web/src/components/bills/status-badge.tsx` | 01 |
| Button | `tone: primary\|secondary\|ghost\|success\|danger`, `width: auto\|full`, `label`, slot `icon` (52px) | `web/src/components/ui/button.tsx` | 01 |
| Chip | `state: off\|on`, `label`, `count` | `web/src/components/ui/chip.tsx` | 01 |
| Field | `state: default\|placeholder\|filled\|error`, `label`, `value`, `hint`, slot `trailing` | `web/src/components/ui/field.tsx` | 01 |
| TopBar | `title`, slot `action` | `web/src/components/layout/top-bar.tsx` | 01 |
| TabItem | `state: off\|on`, `label`, slot `icon` | `web/src/components/layout/tab-bar.tsx` | 01 |
| TabBar | `active: inicio\|contas\|grupos\|perfil` (< 1024px) | `web/src/components/layout/tab-bar.tsx` | 01 |
| NavItem | `state: off\|on`, `label`, `count`, slot `icon` | `web/src/components/layout/side-nav.tsx` | 01 |
| SideNav | `active: inicio\|contas\|grupos\|avisos\|perfil` (≥ 1024px) | `web/src/components/layout/side-nav.tsx` | 01 |
| BillCard | `title`, `meta`, `value`, slots `icon`, `status` | `web/src/components/bills/bill-card.tsx` | 04 |
| RadioCard | `state: off\|on`, `title`, `text` | `web/src/components/ui/radio-card.tsx` | 03 |
| MemberRow | `role: admin\|membro\|pagador\|observador`, `initials`, `name`, `detail` | `web/src/components/groups/member-row.tsx` | 03 |
| HouseCard | `house-link`, `label`, `caption`, `caption-2` | `web/src/components/groups/house-card.tsx` | 03 |
| RecurringRow | `text`, `caption`, `vl` | `web/src/components/recurrences/recurring-row.tsx` | 08 |
| NoticeRow | `tone: info\|vence\|vencida\|aguardando\|pago`, `unread: no\|yes`, `title`, `text`, `time`, slot `icon` | `web/src/components/notifications/notice-row.tsx` | 09 |

### Conta cancelada (D2)

`StatusBadge status="cancelada"`: ícone `fechar`, texto "Cancelada", fundo branco com borda `--color-line`, texto `--color-ink-muted`.
A conta cancelada sai do Início, das listas padrão, dos totais e dos lembretes; aparece só no filtro "Canceladas" da tela Contas e no histórico. No card: valor riscado e opacidade reduzida. Selo na Etapa 01; filtro e regras na Etapa 04.

## Da especificação

## 12. Telas

As 13 telas do MVP estão no canvas [Varal no Doop](https://doop.design/c/k0kB5dc-Vo), em 390 × 844 px, montadas com componentes e tokens; é dali que o código deve ser gerado.

**Organização do canvas**

- [01 · Marca e ícones](https://doop.design/c/k0kB5dc-Vo?page=k0kB5dc-Vo:page1): logo, paleta, tipografia e ícones.
- [02 · Telas mobile](https://doop.design/c/k0kB5dc-Vo?page=-eLoZ0SLb1): as 13 telas em 390×844, em três linhas por fluxo.
- [03 · Telas desktop](https://doop.design/c/k0kB5dc-Vo?page=YGk9_iqJ-Y): 5 telas em 1440×900, 6 janelas (modais) e a gaveta de avisos.
- [04 · Componentes](https://doop.design/c/k0kB5dc-Vo?page=page-mwdwblpn): os 16 componentes, cada um com o caminho no código (`web/src/components/...`).
- Guia **Varal · regras de interface** fixado no canvas: tokens, status e especificação das animações.

| Nº | Tela | Casos de uso | Destaque |
| --- | --- | --- | --- |
| 01 | Entrar | CU01 | Contas caem no varal ao abrir; folha de login sobe |
| 02 | Início | CU06 | Total do mês com contagem, barra de pagas e o resumo como contas balançando no varal |
| 03 | Contas | CU06 | Filtros por status, mês e grupos por prazo |
| 04 | Avisos | CU12 | Avisos por tipo, com ponto de não lido |
| 05 | Nova conta | CU05, CU09 | Área "Enviar PDF do boleto" com borda animada; colar código, digitar e recorrente |
| 06 | Conferir conta | CU05, RN25 a RN28 | PDF lido: código, valor, emissão, vencimento e beneficiário preenchidos e marcados com a origem |
| 07 | Detalhe da conta | CU07, CU08 | A conta pendurada balança; copiar o código ou baixar o PDF; data de emissão; histórico |
| 08 | Marcar como paga | CU08 | Data e comprovante opcional |
| 09 | Conta paga | CU08 | A conta sai do varal e o check é desenhado |
| 10 | Grupo | CU02, CU03, CU04, CU09 | Casas com progresso, membros e papéis, recorrentes |
| 11 | Convidar membro | CU03, RN24 | Escolha do papel e link de uso único |
| 12 | Pedir para alguém pagar | CU10, RN20 | Do pessoal para o grupo, só esta conta |
| 13 | Modo simples | CU11 | Ações grandes por conta: Copiar, Já paguei e Baixar boleto em PDF |

**Telas desktop**

A partir de 1024px, a barra inferior dá lugar a um menu lateral fixo (SideNav, 264px) com logo, seletor de espaço, botão Nova conta e usuário. As folhas inferiores viram janelas centralizadas, e Contas e Detalhe ficam lado a lado.

| Nº | Tela | Equivale a | Destaque |
| --- | --- | --- | --- |
| D01 | Entrar | 01 | Bloco azul com as contas no varal à esquerda, login à direita |
| D02 | Início | 02, 04 | Total do mês com o varal grande, contas que pedem atenção, progresso por casa e avisos recentes |
| D03 | Contas + Detalhe | 03, 07 | Lista com filtros à esquerda e a conta aberta à direita, com Copiar, Baixar PDF e histórico |
| D04 | Grupo | 10 | Casas, membros e papéis, recorrentes em colunas |
| D05 | Modo simples | 13 | Contas do pagador em cards grandes, com Copiar, Já paguei e Baixar PDF |
| D06 | Avisos | 04 | Gaveta lateral de 440px aberta pelo sino |
| M01 | Nova conta | 05 | Janela com a área de enviar PDF e as outras formas |
| M02 | Conferir conta | 06 | Prévia do PDF ao lado dos campos, com os dados lidos destacados |
| M03 | Marcar como paga | 08 | Data e comprovante opcional |
| M04 | Conta paga | 09 | Check desenhado e a conta saindo do varal |
| M05 | Convidar membro | 11 | Papel e link de uso único |
| M06 | Pedir para alguém pagar | 12 | Escolha do grupo e de quem paga |

As telas ainda não estão ligadas como protótipo clicável; os botões indicam a navegação prevista.

## 11. Iconografia

Os ícones são próprios e seguem o traço do logo: grade de 24 × 24 px, linha de 2 px com pontas e cantos arredondados, em `ink-900`. Cor só aparece nos ícones de status, sempre acompanhados de texto. Os desenhos estão no canvas do Doop (seção 12), na prancheta "Ícones", como o componente `Icon` (prop `name`). Além dos 24 da tabela, há `chevron` e `fechar` para navegação, além de pdf, baixar e enviar, usados no boleto em PDF.

| Nome no código | Desenho | Onde aparece |
| --- | --- | --- |
| `varal` | Fio com uma conta pendurada | Aba Início |
| `contas` | Lista de contas | Aba Contas |
| `grupo` | Duas pessoas | Aba Grupos |
| `perfil` | Uma pessoa | Aba Perfil |
| `boleto` | Documento com código de barras | Tipo de conta e colar código |
| `pix` | QR code estilizado | Tipo de conta Pix (não reproduz a marca Pix) |
| `manual` | Lápis | Tipo de conta manual |
| `casa` | Casa | Subgrupo |
| `calendario` | Calendário | Vencimento |
| `repetir` | Duas setas em círculo | Conta recorrente |
| `cadeado` | Cadeado | Visibilidade restrita |
| `sino` | Sino | Notificações |
| `prendedor` | Prendedor de roupa | Aguardando boleto |
| `pendente` | Círculo vazio | Status Pendente |
| `relogio` | Relógio, em âmbar | Status Vence em breve |
| `alerta` | Círculo com exclamação, em vermelho | Status Vencida |
| `pago` | Círculo com check, em verde | Status Paga |
| `comprovante` | Canhoto com check, em verde | Status Confirmada e anexo |
| `copiar` | Duas folhas | Copiar código |
| `camera` | Câmera | Foto do comprovante |
| `pedir` | Seta saindo de uma caixa | Solicitar pagamento |
| `mais` | Sinal de mais | Nova conta |
| `filtro` | Funil | Filtros da lista |
| `voltar` | Seta para a esquerda | Navegação |

No código, os ícones devem virar componentes SVG com `stroke="currentColor"`, para herdar a cor do texto, e `aria-hidden="true"` quando acompanham um texto.
