# Tokens de design

> **Contém:** os tokens do Doop, o nome equivalente na especificação e como viram variáveis CSS no web.
> **Origem:** `get_tokens` do canvas Doop `k0kB5dc-Vo` (12/11/2026) e `docs/especificacao-varal.md`, seção 10.

## Regra

`web/src/styles/tokens.css` é a saída de `get_tokens(canvas_id "k0kB5dc-Vo", format "css")`, **com os mesmos nomes**.
No código só se usa `var(--token)`; nunca hex solto. Se faltar um token, pergunte (o canvas é somente leitura).

## Doop → especificação

| Token CSS (Doop) | Valor | Nome na especificação | Uso |
| --- | --- | --- | --- |
| `--color-ink` | `#1C2541` | `ink-900` | Marca, texto principal, botão primário |
| `--color-ink-soft` | `#2B3657` | — | (só no Doop) |
| `--color-ink-muted` | `#4A5372` | `ink-600` | Texto secundário, ícones inativos |
| `--color-ink-subtle` | `#8A91A8` | `ink-400` | Placeholder e desabilitado |
| `--color-line` | `#E3E6EC` | `line` | Bordas e divisores |
| `--color-bg` | `#F6F7F9` | `bg` | Fundo do app |
| `--color-surface` | `#FFFFFF` | `surface` | Cards, folhas, campos |
| `--color-neutral-soft` | `#EEF0F4` | `neutral-50` | Selos Pendente e Aguardando |
| `--color-amber` | `#F5A524` | `amber-500` | Prendedor, FAB, ícone "vence em breve" |
| `--color-amber-text` / `--color-amber-soft` | `#9A5B00` / `#FEF4E2` | `amber-text` / `amber-50` | Selo "Vence em breve" |
| `--color-red` | `#E5484D` | `red-500` | Ícone de vencida, ações destrutivas |
| `--color-red-text` / `--color-red-soft` | `#B42318` / `#FDECEC` | `red-text` / `red-50` | Selo "Vencida" |
| `--color-green` | `#1F9D6B` | `green-600` | Paga, confirmada, sucesso |
| `--color-green-text` / `--color-green-soft` | `#12704B` / `#E6F4EE` | `green-text` / `green-50` | Selos "Paga" e "Confirmada" |
| `--radius-sm` / `md` / `lg` / `xl` / `2xl` / `full` | 8 / 12 / 20 / 22 / 28 / 999 px | selos / campos / cards / — / hero e folhas / pílula | |
| `--spacing-1…8` | 4, 8, 12, 16, 20, 24, 32 px | múltiplos de 4 | margem lateral 20 px |
| `--font-display` | Bricolage Grotesque | Display, títulos, valores | |
| `--font-sans` | Inter | Interface e texto | |
| `--text-xs` … `--text-3xl` | 12, 13, 15, 16, 18, 24, 32, 48 px | Rótulo, Pequeno, Corpo, Título de card, Título 2, Título 1, Display, número-herói | |

Número-herói: 48px (`--text-3xl`) no mobile e 64px no desktop (guia `varal-ui`; sem token próprio no Doop), centavos na metade do tamanho com opacidade .55.

## Da especificação

## 10. Identidade visual

O logo aprovado é a opção 1, "Contas no varal": três contas penduradas nas cores dos status, com o nome em Bricolage Grotesque. As cores das contas no logo são as mesmas dos status no app, então a marca já ensina a ler a interface.

### Logo

- **Versões:** horizontal (símbolo + nome), símbolo sozinho, fundo claro e fundo escuro (fio e prendedores em branco).
- **Ícone de app:** símbolo branco sobre azul-marinho `#1C2541`, cantos de 22% do lado.
- **Favicon:** versão simplificada, sem prendedores e com o fio mais grosso.
- **Respiro mínimo:** a altura de uma conta do símbolo em todos os lados. **Tamanho mínimo:** símbolo com 24 px de largura.
- **Não fazer:** trocar a ordem ou as cores das contas, girar o fio, aplicar sombra ou degradê.

### Paleta

| Token | Hex | Uso |
| --- | --- | --- |
| `ink-900` | `#1C2541` | Marca, texto principal, botão primário, fundo do ícone de app |
| `ink-600` | `#4A5372` | Texto secundário e ícones inativos |
| `ink-400` | `#8A91A8` | Placeholder e desabilitado (nunca em texto que precisa ser lido) |
| `line` | `#E3E6EC` | Bordas e divisores |
| `bg` | `#F6F7F9` | Fundo do app |
| `surface` | `#FFFFFF` | Cards, folhas e campos |
| `amber-500` | `#F5A524` | Prendedor, destaques e ícone de "vence em breve" |
| `amber-text` / `amber-50` | `#9A5B00` / `#FEF4E2` | Texto e fundo do selo "Vence em breve" |
| `red-500` | `#E5484D` | Ícone de vencida e ações destrutivas |
| `red-text` / `red-50` | `#B42318` / `#FDECEC` | Texto e fundo do selo "Vencida" |
| `green-600` | `#1F9D6B` | Paga, confirmada e sucesso |
| `green-text` / `green-50` | `#12704B` / `#E6F4EE` | Texto e fundo dos selos "Paga" e "Confirmada" |
| `neutral-50` | `#EEF0F4` | Fundo dos selos "Pendente" e "Aguardando boleto" |

Status nunca é indicado só por cor: todo selo tem ícone e texto (RNF09).

### Tipografia

Duas famílias do Google Fonts: **Bricolage Grotesque**, a mesma do logo, para títulos e valores em destaque, e **Inter** para a interface e o texto corrido.

| Estilo | Família | Peso | Tamanho / linha | Uso |
| --- | --- | --- | --- | --- |
| Display | Bricolage Grotesque | 800 | 32 / 38 px, espaçamento -2% | Títulos de destaque e mensagens de sucesso |
| Título 1 | Bricolage Grotesque | 700 | 24 / 30 px | Título de tela |
| Título 2 | Bricolage Grotesque | 700 | 18 / 24 px | Título de seção |
| Título de card | Inter | 600 | 16 / 22 px | Descrição da conta |
| Corpo | Inter | 400 | 15 / 22 px | Texto geral |
| Corpo forte | Inter | 600 | 15 / 22 px | Botões e ênfase |
| Valor em lista | Inter | 600 | 16 / 22 px, números tabulares | Valores em listas e cards |
| Pequeno | Inter | 500 | 13 / 18 px | Vencimento, casa, pagador |
| Rótulo | Inter | 600 | 12 / 16 px, maiúsculas, +4% | Selos de status e rótulos de seção |

### Espaços e formas

- **Espaçamento:** múltiplos de 4 (4, 8, 12, 16, 24, 32 px); margem lateral das telas de 20 px.
- **Raios:** 8 px em selos, 12 px em campos, 20 px em cards, 28 px no bloco de destaque e nas folhas inferiores; botões e filtros em pílula.
- **Toque:** botões com 52 px de altura; nenhum alvo menor que 44 px.
- **Sombra:** só na barra inferior e em folhas que sobem; cards usam borda `line`.
