# ADR 0005 — RF11 sem categoria

> **Contém:** a retirada da categoria do RF11 e o que isso significa para o modelo de dados e as etapas.
> **Origem:** resposta do dono à Q2 da Etapa 04 (chat, 15/11/2026) e a especificação reexportada na rev 47 (Claude Docs `c3529f9b-eb78-41e6-aa80-2a31957e189e`), onde o RF11 passou a ser "Definir espaço, subgrupo, pagador e visibilidade".

- **Status:** aceita (15/11/2026)

## Contexto

O RF11 pedia categoria, mas nenhum frame do Doop tem o campo e não havia lista de categorias (Q2 da Etapa 04). O dono tirou a categoria do RF11 na origem.

## Decisão

- Categoria é conceito da **v3** (orçamento por categoria), não do MVP.
- **Nenhum** campo, tabela, modelo, migração ou contrato de API de categoria agora, nem "para depois". Quando a v3 chegar, ela decide o desenho.

## Consequências

- `requisitos/funcionais.md` (RF11) segue a origem rev 47.
- A origem ainda cita categoria no passo 3 do CU05 e no modelo de dados (seção 8: entidade `categoria` e `lancamento.categoria_id?`). Os derivados seguem este ADR: [CU05](../../casos-de-uso/CU05-cadastrar-conta.md) sem categoria e [modelo](../../dados/modelo.md) com nota. O dono limpou a origem na rev 50 (Q22 da Etapa 04); a cópia local é reexportada na abertura da Etapa 05.
- A Etapa 04 não cria `categoria` nem `categoria_id`.
