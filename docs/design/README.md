# Design — canvas do Doop

> **Contém:** onde está cada tela e componente no Doop, como lê-los, e as telas e ícones da especificação.
> **Origem:** canvas Doop `k0kB5dc-Vo` (lido em 12/11/2026) e `docs/especificacao-varal.md`, seções 11 e 12.

## Regras

- **Nenhuma tela ou componente é construído sem antes ser lido no canvas.** O canvas é **somente leitura**.
- Conector **claude.ai Doop** (ferramentas `mcp__claude_ai_Doop__*`). Uma vez por sessão: `get_guide(topic: "doop-instructions")`. Sempre `agent_name: "Claude Code"`.
- Ids de frame podem mudar se alguém recriar um frame: confirme com `get_canvas` e **procure pelo nome**.
- Por tela: `get_frame` (HTML) + `get_frame_screenshot(scale 2)`; para cada `<doop-use component="X">`, `get_component("X")` → `code.path`.
- Guia fixado: `varal-ui` ("Varal · regras de interface"), via `get_guidelines`. Tokens: [tokens.md](tokens.md). Animações: [movimento.md](movimento.md).

## Canvas

[Varal no Doop](https://doop.design/c/k0kB5dc-Vo) · páginas `k0kB5dc-Vo:page1` (Marca e ícones), `-eLoZ0SLb1` (Telas do MVP), `page-mwdwblpn` (Componentes).

### Frames de marca e telas

| Frame | Nome | Tamanho | Etapa |
| --- | --- | --- | --- |
| `t4pHch9UDR` | Logo | 1200×720 | 01 |
| `O5JpUML_Uw` | Paleta e tipografia | 1200×900 | 01 |
| `FDDhQEf8T5` | Ícones | 1200×684 | 01 |
| `GJDSPaQbio` | 01 · Entrar | 390×844 | 02 |
| `JJvrRugL0_` | 02 · Início | 390×844 | 04 |
| `bdiED7Q0I-` | 03 · Contas | 390×844 | 04 |
| `fcR9RDu79a` | 04 · Avisos | 390×844 | 09 |
| `0PfC8pBVwF` | 05 · Nova conta | 390×844 | 06 |
| `tKY4nFTZ3-` | 06 · Conferir conta | 390×1090 | 06 |
| `efJzW9e5vx` | 07 · Detalhe da conta | 390×1220 | 04 e 06 |
| `-RwBuRqs8G` | 08 · Marcar como paga | 390×844 | 07 |
| `y1NUSjOnMM` | 09 · Conta paga | 390×844 | 07 |
| `SfhuKVOQIF` | 10 · Grupo | 390×944 | 03 |
| `bkv_O9ohNO` | 11 · Convidar membro | 390×844 | 03 |
| `MFZW3LUORq` | 12 · Pedir para alguém pagar | 390×844 | 10 |
| `mIvLheR2TS` | 13 · Modo simples (pagador) | 390×844 | 10 |
| `SMDsrD8FGT` | D02 · Início (desktop) | 1440×900 | a definir (ver [PROGRESSO](../PROGRESSO.md)) |

### Componentes

| Componente | Props (do Doop) | Caminho no código | Frame |
| --- | --- | --- | --- |
| Icon | `name` (29 nomes), `size: sm\|md\|lg\|xl` | `web/src/components/ui/icon.tsx` | `gat61o1SXm` |
| StatusBadge | `status: aguardando\|pendente\|vence\|vencida\|paga\|confirmada` | `web/src/components/bills/status-badge.tsx` | `g156vs4htG` |
| Button | `tone: primary\|secondary\|ghost\|success\|danger`, `width: auto\|full`, `label`, slot `icon` | `web/src/components/ui/button.tsx` | `Qb8v_nTo0d` |
| Chip | `state: off\|on`, `label`, `count` | `web/src/components/ui/chip.tsx` | `Shcn3WFv8A` |
| Field | `state: default\|placeholder\|filled\|error`, `label`, `value`, `hint`, slot `trailing` | `web/src/components/ui/field.tsx` | `JAB1jjNtoh` |
| BillCard | `title`, `meta`, `value`, slots `icon`, `status` | `web/src/components/bills/bill-card.tsx` | `Mwqabjlc2s` |
| NoticeRow | `tone: info\|vence\|vencida\|aguardando\|pago`, `unread: no\|yes`, `title`, `text`, `time`, slot `icon` | `web/src/components/notifications/notice-row.tsx` | `q13NH-_3GL` |
| TopBar | `title`, slot `action` | `web/src/components/layout/top-bar.tsx` | `_7s7yWcVpV` |
| TabItem | `state: off\|on`, `label`, slot `icon` | `web/src/components/layout/tab-bar.tsx` | `uk7KOSHIo1` |
| TabBar | `active: inicio\|contas\|grupos\|perfil` | `web/src/components/layout/tab-bar.tsx` | `TEqEQt5DFw` |
| MemberRow | `role: admin\|membro\|pagador\|observador`, `initials`, `name`, `detail` | `web/src/components/groups/member-row.tsx` | `ZCWYoEHowC` |
| HouseCard | `house-link`, `label`, `caption`, `caption-2` | `web/src/components/groups/house-card.tsx` | — |
| RecurringRow | `text`, `caption`, `vl` | `web/src/components/recurrences/recurring-row.tsx` | — |
| RadioCard | `state: off\|on`, `title`, `text` | `web/src/components/ui/radio-card.tsx` | `rdtPCSRu6B` |
| NavItem | `state: off\|on`, `label`, `count`, slot `icon` (desktop) | `web/src/components/layout/side-nav.tsx` | `Q1iDJMH8KC` |
| SideNav | `active: inicio\|contas\|grupos\|avisos\|perfil` (desktop ≥ 1024px) | `web/src/components/layout/side-nav.tsx` | `dQTe9DYY67` |

NavItem, SideNav e "D02 · Início" existem no canvas mas não na especificação (que fala em 13 telas e 14 componentes).

## Divergências conhecidas

Registradas em [PROGRESSO.md](../PROGRESSO.md), "Decisões pendentes". Não escolha sozinho: pergunte.

## Da especificação

## 12. Telas

As 13 telas do MVP estão no canvas [Varal no Doop](https://doop.design/c/k0kB5dc-Vo), em 390 × 844 px, montadas com componentes e tokens; é dali que o código deve ser gerado.

**Organização do canvas**

- [01 · Marca e ícones](https://doop.design/c/k0kB5dc-Vo?page=k0kB5dc-Vo:page1): logo, paleta, tipografia e ícones.
- [02 · Telas do MVP](https://doop.design/c/k0kB5dc-Vo?page=-eLoZ0SLb1): as 13 telas, em três linhas por fluxo.
- [03 · Componentes](https://doop.design/c/k0kB5dc-Vo?page=page-mwdwblpn): os 14 componentes, cada um com o caminho no código (`web/src/components/...`).
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
