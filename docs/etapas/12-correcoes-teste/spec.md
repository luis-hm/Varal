# Spec — Etapa 12: correções do teste inicial

> **Contém:** escopo, critérios de aceite e fora de escopo da etapa que corrige o que o dono achou no teste inicial.
> **Origem:** [correções do teste inicial](../../produto/correcoes-teste-inicial-2026-11-16.md) (COR-01 a COR-12, escrito pelo dono) e o pedido no chat de 18/11/2026 (categorias com ícone, espaçamento das telas, auditoria do escopo inicial).

Branch `etapa/12-correcoes-teste`, aberta sobre a 11 (HMG publicado). Não fecha a 11: CA13/18 e produção continuam lá.

## Escopo

| Item | O que entrega |
| --- | --- |
| COR-01 | Voltar para a aba não pede login nem prende em "carregando"; só mascara quando a identidade muda ou o servidor diz 401/403. |
| COR-02/03 | Contas lista todos os meses; mês é filtro opcional e combina com status, categoria e pagador. |
| COR-04 | "Casa" vira **categoria** com ícone ([ADR 0016](../../arquitetura/adr/0016-categorias-com-icone.md)). |
| COR-05 | Contas abre no pessoal; `?espaco=` mostra um grupo; limpar volta ao pessoal. |
| COR-06 | Nova conta nasce no destino da tela (grupo/categoria/Contas filtrado), sempre visível e trocável. |
| COR-07 | "Sem categoria" aparece no resumo, no filtro e tem tela própria; filtro ativo nunca some. |
| COR-08 | Telas acompanham as mudanças; espaçamento de 24px entre seções nas duas larguras. |
| COR-09 | Perfil redesenhado, mesmos fluxos e proteções. |
| COR-10 | Permissões por categoria ([ADR 0017](../../arquitetura/adr/0017-permissoes-por-categoria.md), aprovado em 18/11/2026). |
| COR-11 | Grupos → grupo → categoria → contas → detalhe. |
| COR-12 | Login Google sem 403 CSRF (referrer `strict-origin` em `/entrar` e `/criar-conta`, Next e edge). URI de retorno no Google Console é ação do dono. |
| Auditoria | Itens da auditoria do escopo inicial listados no [handoff](handoff-codex.md#3-auditoria-do-escopo-inicial). |

## Critérios de aceite (Dado / Quando / Então)

- CA01 (COR-01): dado um usuário logado, quando troca de aba e volta (ou volta pelo BFCache), então a tela continua sem pedir login; com logout em outra aba, mostra "Sua sessão terminou".
- CA02 (COR-02/03): dado contas em três meses, quando abre Contas sem mês, então vê todas; com `mes=AAAA-MM&status=a_pagar`, só as abertas daquele vencimento.
- CA03 (COR-04): dado um admin, quando cria ou edita categoria, então escolhe nome e um dos 14 ícones; o ícone aparece no grupo, no Início, na Nova conta e no card da conta.
- CA04 (COR-05): dado pessoal e grupo com contas, quando abre `/contas`, então só vê as pessoais; com `?espaco=G`, só as do grupo.
- CA05 (COR-06): dado a tela de uma categoria, quando toca "+", então o formulário já vem com o grupo e a categoria, e dá para trocar.
- CA06 (COR-07): dado uma conta sem categoria, então ela aparece em "Sem categoria" no resumo, no filtro e na tela da categoria.
- CA07 (COR-09): Perfil mostra identidade, dados, preferências, exportar e excluir (zona de perigo), em 390×844 e 1440×900; reautenticação abre em folha/modal.
- CA08 (COR-11): da aba Grupos chega-se às contas de uma categoria e ao detalhe, e volta para a categoria.
- CA09 (COR-12): no formulário de `/entrar`, o POST para `/accounts/google/login/` leva `Origin` do próprio site (não `null`).
- CA10 (COR-10): dado um admin que personaliza duas categorias com ações diferentes para duas pessoas, então cada ação permitida funciona e cada negada é recusada também por chamada direta à API (404 sem "ver", 403 sem a ação); trocar ids não dá acesso cruzado; contagens, totais, opções e arquivos não revelam contas sem "ver"; versão antiga dá 409.
- CA11: `make test`, `make lint`, `make types` (sem diff) e `make e2e` verdes.

## Fora de escopo

- Produção, CA13/18 da 11, reexportação da especificação (P6).
- Categoria de orçamento (v3, ADR 0005).
- Mudar o canvas do Doop.
