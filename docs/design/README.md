# Design — canvas do Doop

> **Contém:** onde está cada tela e componente no Doop, como lê-los, a regra responsiva e as telas e ícones da especificação.
> **Origem:** canvas Doop `k0kB5dc-Vo` (autenticação relida em 13/11/2026), guia `varal-ui`, especificação seções 11–12, código das Etapas 01–06 e decisões/revisões delegadas das etapas.

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

Tamanhos: telas mobile 390×844 (06: 390×1090; 07: 390×1220; 10: 390×944); telas desktop 1440×900; gaveta D06 440×900; modais no tamanho da janela (M01 560×590, M02 1040×660, M03 520×450, M04 480×520, M05 560×480, M06 560×530).

### Componentes (página 04)

| Componente | Props (do Doop) | Caminho no código | Etapa |
| --- | --- | --- | --- |
| Icon | `name` (29 nomes), `size: sm\|md\|lg\|xl` | `web/src/components/ui/icon.tsx` | 01 (feito) |
| StatusBadge | `status: aguardando\|pendente\|vence\|vencida\|paga\|confirmada\|cancelada` | `web/src/components/bills/status-badge.tsx` | 01 (feito) |
| Button | `tone: primary\|secondary\|ghost\|success\|danger`, `width: auto\|full`, `label`, slot `icon` (52px) | `web/src/components/ui/button.tsx` | 01 (feito) |
| Chip | `state: off\|on`, `label`, `count`; extensão local `wrap` para espaço/casa (Q04-39) | `web/src/components/ui/chip.tsx` | 01 (feito), revisão 04 |
| Field | `state: default\|placeholder\|filled\|error`, `label`, `value`, `hint`, slot `trailing` | `web/src/components/ui/field.tsx` | 01 (feito) |
| TopBar | `title`, slot `action` | `web/src/components/layout/top-bar.tsx` | 01 (feito) |
| TabItem | `state: off\|on`, `label`, slot `icon` | `web/src/components/layout/tab-bar.tsx` | 01 (feito) |
| TabBar | `active: inicio\|contas\|grupos\|perfil` (< 1024px) | `web/src/components/layout/tab-bar.tsx` | 01 (feito) |
| NavItem | `state: off\|on`, `label`, `count`, slot `icon` | `web/src/components/layout/side-nav.tsx` | 01 (feito) |
| SideNav | `active: inicio\|contas\|grupos\|avisos\|perfil` (≥ 1024px) | `web/src/components/layout/side-nav.tsx` | 01 (feito) |
| BillCard | `title`, `meta`, `value`, slots `icon`, `status` | `web/src/components/bills/bill-card.tsx` | 04 (feito) |
| RadioCard | `state: off\|on`, `title`, `text` | `web/src/components/ui/radio-card.tsx` | 03 (feito) |
| MemberRow | `role: admin\|membro\|pagador\|observador`, `initials`, `name`, `detail` | `web/src/components/groups/member-row.tsx` | 03 (feito) |
| HouseCard | `house-link`, `label`, `caption`, `caption-2` | `web/src/components/groups/house-card.tsx` | 03 (feito) |
| RecurringRow | `text`, `caption`, `vl` | `web/src/components/recurrences/recurring-row.tsx` | 08 |
| NoticeRow | `tone: info\|vence\|vencida\|aguardando\|pago`, `unread: no\|yes`, `title`, `text`, `time`, slot `icon` | `web/src/components/notifications/notice-row.tsx` | 09 |

Fora da página 04, também da Etapa 01: logo (`web/src/components/ui/logo.tsx`), shell responsivo (`web/src/components/layout/app-shell.tsx`) e "Em breve" (`web/src/components/layout/em-breve.tsx`).
**Vitrine** `/dev/componentes` (`web/src/app/dev/componentes/`): todos os componentes feitos e seus estados, para teste e comparação com o Doop; só em desenvolvimento, com sessão autenticada desde a Etapa 02. A checagem de produção ocorre antes do `ProtectedShell` para devolver HTTP 404 real, sem iniciar o streaming da sessão.

### Autenticação implementada (Etapa 02)

`web/src/components/auth/auth-frame.tsx` e `auth-form.tsx` atendem 01 · Entrar ↔ D01: folha branca abaixo da marca no mobile e duas metades com formulário de 400px no desktop. Rotas `/entrar`, `/criar-conta`, `/recuperar-senha`, `/recuperar-senha/[key]` e `/entrar/retorno` compartilham layout e lógica.

O dono aprovou no chat (13/11/2026) cadastro/recuperação como estados desse layout e a animação mobile do guia (`100%`, `0,5s`). Os frames foram lidos em HTML e screenshots e continuam `draft`; aprovação no chat não alterou o canvas. Comparação nas duas resoluções: composição, cores, fontes e curva do varal correspondem. Diferença deliberada: senha começa vazia com placeholder cinza; os bullets preenchidos do exemplo do Doop não são uma senha fictícia no formulário.

O shell recebe usuário/espaço próprios da API. Perfil continua “Em breve”, com a ação “Sair da conta”; a tela Perfil/LGPD permanece para a Etapa 11.

### Grupos implementados (Etapa 03)

- **Folha/modal** `web/src/components/ui/folha.tsx`: `<dialog>` nativo, `sheet-up` < 1024px e `modal-pop` ≥ 1024px; base de 11 ↔ M05 e das telas sem frame (criar grupo, gestão de membro, casa).
- **Convite** `web/src/components/groups/convite-folha.tsx` (11 ↔ M05): RadioCard de papel, link encurtado em JetBrains Mono, `shine` 2×.
- **Página do grupo** `grupo-pagina.tsx` (10 ↔ D04), **lista** `grupos-lista.tsx`, **aceite** `aceite-convite.tsx` (layout de 01 ↔ D01), **sair** `sair-do-grupo.tsx`; seletor de espaço no SideNav (`side-nav.tsx`, menu sem frame).
- Diferenças em relação aos frames: [relatório da Etapa 03](../etapas/03-espacos-grupos/relatorio.md#diferenças-visuais-ca18). 10 e 11 seguem draft; D04 e M05 `ready_for_dev`. Canvas não alterado.

### Contas implementadas (Etapa 04)

Mesmas rotas nas duas larguras: `/` (02 ↔ D02), `/contas` (03 ↔ D03), `/contas/[id]` (07 sozinho < 1024px; lista 540px + painel `slide-in` ≥ 1024px). Componentes em `web/src/components/bills/`:

- **Início** `inicio.tsx`: "Total de <mês>" com `count-up`, varal `swing` (sem a conta "pagas" e sem barra até a 07), "Precisa de atenção" com `rise`; D02 com "Por casa". O hero do D02 tem a altura do conteúdo, sem reservar a barra ausente (decisão 27).
- **Contas e Detalhe** `contas-pagina.tsx`, `conta-detalhe.tsx`: chips com contagem, "Casa" e "Quem paga" no desktop, folha "Filtros" no mobile; histórico com ações automáticas sem autor.
- **Detalhe mobile é tela empilhada** (decisão 28): `/contas/[id]` abaixo de 1024px não tem TabBar; tem TopBar com voltar, também nos estados de carregando, erro e "Conta não encontrada" (`app-shell.tsx`).
- **Formulário** `conta-folha.tsx` (partes de 05/06 ↔ M01/M02, sobre `ui/folha.tsx`): só a conta manual; aviso "Quem paga também vê esta conta" em `aria-live`. "Onde fica" começa pelo espaço atual, já selecionado (Pessoal se a pessoa está no pessoal, o grupo se está num grupo); se o atual não aceita conta (observador), mantém a ordem e seleciona o primeiro; na edição fica o espaço da conta (decisão 30, `espacosParaCriar`).
- **Nomes de pessoas em uma linha** (decisão 29): nomes e e-mails usam `<Nome>` (`web/src/components/ui/nome.tsx`): uma linha, reticências, valor inteiro no `title` e no nome acessível. Usado em BillCard, detalhe e MemberRow; saudação e identificação do usuário no shell seguem o corte pelo CSS.
- **Quem vê completo** (Q04-38/D04-14): detalhe restrito usa `quem_ve` (audiência efetiva da RN06/RN07, considerando criador, pagador, escolhidos e papéis atuais, sem duplicatas), não só `acesso`. Cada pessoa tem seu próprio `<Nome>` em uma linha; a lista quebra entre pessoas e cresce sem cortar participantes. É exceção de composição motivada pela visibilidade; o canvas não foi alterado nem sua aprovação alegada.
- **Identificação de espaço/casa** (Q04-39): seletor fechado e Chips `wrap` mostram até duas linhas. Ao abrir o menu, nomes de espaços ficam completos; no formulário, foco de teclado ou seleção por toque expande o nome inteiro antes de salvar. Assim grupos com prefixos iguais podem ser distinguidos sem depender de hover ou pedir confirmação extra no caso comum. Nomes de pessoas continuam em uma linha.
- **Prazo e selo** (Q04-35/ADR 0009): o filtro Vencidas também inclui aguardando vencida; o card conserva o selo Aguardando. A distinção temporal não altera a paleta ou o componente StatusBadge.
- **Grupo:** HouseCard com total e "N contas"; "Configurações" (janela 1–7) só para admin; folha de saída barrada pela RN32 em `sair-do-grupo.tsx`; lista do pagador `contas-pagador.tsx` em `/grupos/[id]/simples`.
- **Espaço atual:** cookie `espaco` (`web/src/lib/espaco.ts`); seletor no SideNav e no cabeçalho do Início mobile.
- Diferenças em relação aos frames: [relatório da Etapa 04](../etapas/04-contas/relatorio.md#comparação-com-o-doop-ca29). Canvas não alterado.

### Boleto e Pix implementados (Etapa 05)

`conta-folha.tsx` estende o formulário existente, referenciado em 05/M01 e 06/M02, sem criar outra rota. "Como cadastrar" oferece Digitar conta, Colar código e Chave Pix; o espaço atual continua primeiro. Código inválido permanece no campo; preview preenche dados e mostra avisos. Valor codificado é somente leitura; fator bancário ambíguo oferece as duas datas em escolha explícita. Pix sem valor/data exige preenchimento, sem reaproveitar valor de entrada anterior. Resposta atrasada do preview não sobrescreve uma mudança posterior para manual; refetch remoto não substitui entrada/conferência da sessão local (CA16). Durante gravação, campos, modo, leitura, fechamento e reenvio ficam protegidos, inclusive antes do próximo render (CA15).

`conta-detalhe.tsx` acrescenta bloco de linha digitável/Pix/chave, beneficiário quando disponível e `copiar-codigo.tsx` (07/D03). Copia dígitos normalizados do boleto, BR Code integral ou chave normalizada, anuncia sucesso e oferece textarea selecionada/focada se o clipboard falhar. Manual não exibe cópia fictícia. A ação copia dados: não inicia pagamento nem consulta URL Pix/DICT. O grupo de pagador recebe somente detalhes já autorizados; o modo simples completo continua na 10.

Estilos em `instrumento.module.css`, com tokens existentes, textarea para código longo e rótulos acessíveis. PDF/prévia, emissão e pagamento permanecem ausentes até suas etapas. Leitura atual do Doop e comparação final em 390×844/1440×900 registradas no [relatório da 05](../etapas/05-boleto-pix/relatorio.md), com fixtures sintéticas e inspeção visual sem pixel a pixel. Avisos exibem datas em dd/mm/aaaa; datas estruturadas da API continuam ISO. O canvas permanece preservado.

### PDF do boleto implementado e validado (Etapa 06)

Formulário existente em `conta-folha.tsx` e `pdf-arquivo.tsx` referencia 05/M01 e06/M02: escolher/arrastar PDF, trocar/remover, acompanhar leitura e conferir candidatos/metadados. A seleção do arquivo não salva conta nem substitui o PDF ativo antes da confirmação. Sem código, permite conferência manual; várias linhas válidas exigem escolha e avisam que o arquivo inteiro fica disponível a quem vê a conta.

`PdfArquivo` pede assinatura atual e aceita prévia HTTP(S) de outra origem, servida diretamente pelo S3 privado; não injeta PDF como HTML da aplicação nem usa URL do próprio app como documento. Há prévia em iframe e abertura em outra aba com `noopener noreferrer`. Detalhe07/D03 acrescenta arquivo, emissão/beneficiário e download autorizado. Emissão é data civil formatada sem conversão para o fuso de um instante, para não deslocar o dia.

Inspeção em navegador headed confirmou PDF real e fallback em mobile/desktop. Resultado integral verde e capturas finais ficam no [relatório 06](../etapas/06-pdf-boleto/relatorio.md). Canvas somente leitura e preservado; pagamento/comprovante/recorrência permanecem para etapas seguintes.

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
