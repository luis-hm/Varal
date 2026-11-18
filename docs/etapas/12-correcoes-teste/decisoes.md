# Decisões — Etapa 12

> **Contém:** decisões tomadas sem o dono (reversíveis só no código) e as perguntas que ficam com ele.
> **Origem:** propostas do dono em [correções do teste inicial §12](../../produto/correcoes-teste-inicial-2026-11-16.md#12-decisões-para-a-próxima-conversa) e o chat de 18/11/2026.

## Seguem a proposta escrita pelo dono

| ID | Decisão | Onde está |
| --- | --- | --- |
| DEC-01 | Categoria substitui casa dentro do grupo (do dono, 17/11). | ADR 0016 |
| DEC-02 | Casas existentes viram categorias com ícone `casa`; nada é remapeado. | migração `0007_subgrupo_icone` |
| DEC-03 | Escolher um grupo em Contas substitui a lista pessoal; limpar volta ao pessoal. | `contas-pagina.tsx` |
| DEC-05 | "A pagar" = `pendente` + `aguardando`; "Todas" inclui pagas; canceladas só no filtro próprio; mês = mês do vencimento. | `LancamentosView.get` |
| DEC-06 | Contas sempre abre pessoal; o detalhe volta à consulta (`?espaco=`, filtros na URL); cadastro dentro de grupo/categoria sugere esse destino. | `destinoDaTela` em `app-shell.tsx` |
| DEC-07 | Início e resumo do grupo continuam por mês (o mês atual); só Contas perde o mês obrigatório. | `ResumoView` |
| DEC-09 | Categoria opcional; "Sem categoria" é visível em todo lugar e não é personalizável. | ADR 0016 |

## Decisões de código (reversíveis)

| Decisão | Motivo | Como desfazer |
| --- | --- | --- |
| API mantém `subgrupo`/`casas`/`por_casa` nos contratos; a UI diz "categoria". | Evitar quebrar tipos e E2E de uma vez. | Renomear contratos + `make types`. |
| Lista sem mês não tem paginação (comentário `ponytail:` no código). | Volume de um grupo familiar é pequeno. | Paginação por cursor quando passar de ~500 contas. |
| `varal_owner` com `Max-Age` de 14 dias. | Cookie de sessão sumia ao fechar o navegador e mascarava a volta. | Tirar o `Max-Age`. |
| Referrer `strict-origin` só em `/entrar` e `/criar-conta`; o resto segue `no-referrer`. | O formulário do Google precisa de `Origin` para o CSRF do Django; não enfraquece CSRF. | Voltar a regra única em `next.config.ts` e no edge. |
| Capturas da etapa em JPEG (qualidade 70) versionadas em [evidencias/](evidencias/), geradas pelo teste "evidências da etapa 12" de `etapa12.spec.ts`. | O handoff pede as capturas na etapa; em JPEG somam ~0,6 MB. As outras etapas seguem em `web/e2e/__screens__` (ignorado). | Apagar a pasta e o teste. |
| Specs E2E usam `ORIGIN` (`LAB_BASE_URL`) no lugar de `localhost:3000` fixo. | A porta 3000 da máquina estava ocupada por outro projeto; o E2E rodou na 3100. | Voltar o literal. |

## Perguntas ao dono (abertas)

| ID | Pergunta | Proposta |
| --- | --- | --- |
| Q12-1 | Aprova a política de permissões por categoria (DEC-04/08/10)? | **Aprovada pelo dono em 18/11/2026** ([ADR 0017](../../arquitetura/adr/0017-permissoes-por-categoria.md)); implementada. |
| Q12-4 | Regras que completam o COR-10 após a revisão de segurança | **Respondida em 18/11/2026:** troca de papel e membro novo recebem o padrão do papel; o criador nasce pagador (só trocar o pagador para si exige "Pagar"); demais regras aprovadas. Ver [ADR 0017](../../arquitetura/adr/0017-permissoes-por-categoria.md#implementação). |
| Q12-2 | O cadastro deve pedir o nome da pessoa e o Perfil deve deixar editar? Hoje o Perfil mostra "Não informado". | Pedir nome opcional no cadastro e editar no Perfil (`PATCH /api/me/`). |
| Q12-3 | Cadastrar no Google Console a URI `https://hmgvaral.codehub.systems/accounts/google/login/callback/` (ação do dono, COR-12). | — |
