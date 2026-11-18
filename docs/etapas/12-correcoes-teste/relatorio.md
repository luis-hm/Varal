# Relatório — Etapa 12 (parcial)

> **Contém:** o que foi feito até agora, testes e o que falta.
> **Origem:** sessão do Claude Code de 18/11/2026. Etapa **em andamento**; o restante está no [handoff](handoff-codex.md).

## Feito

| COR | Resultado |
| --- | --- |
| COR-01 | Voltar à aba revalida sem mascarar; só mascara quando a identidade muda, 401/403 ou `pagehide`. |
| COR-02/03 | Contas sem mês obrigatório; mês, status, categoria e pagador combinam. |
| COR-04 | Casa → categoria com 14 ícones ([ADR 0016](../../arquitetura/adr/0016-categorias-com-icone.md)). |
| COR-05 | Contas abre pessoal; `?espaco=` escolhe o grupo. |
| COR-06 | Nova conta nasce no destino da tela. |
| COR-07 | "Sem categoria" no resumo, filtro e tela própria; filtro ativo continua visível e removível. |
| COR-08 | Grupo, Início, Contas, Detalhe e Perfil com 24px entre seções. |
| COR-09 | Perfil redesenhado (identidade, dados, preferências, exportar, zona de perigo; reautenticação em folha). |
| COR-11 | Grupos → grupo → categoria → contas → detalhe. |
| COR-12 | Referrer `strict-origin` em `/entrar` e `/criar-conta` (Next e edge). Falta a URI no Google Console (dono). |

## Auditoria do escopo inicial (feito)

- Confirmações em folha do app no lugar de `window.confirm` (remover membro, sair, encerrar recorrência, desfazer pagamento, cancelar conta).
- Recorrência clicada no grupo abre direto nela.
- CU02: criar grupo já abre o convite.
- CU01: e-mail já cadastrado oferece entrar ou recuperar a senha.
- CU05: PDF inválido ou sem código oferece colar o código (a folha testava um estado `"falhou"` que a API não tem).
- "5 MB" unificado; código sem uso removido.

## Testes

- API (projeto `varaltest`): suíte completa verde (546 no início; arquivos afetados 201 verdes após as mudanças).
- Web: 165/165 Vitest, `tsc` e lint limpos.
- E2E: **não rodado**; pontos que vão quebrar estão no [handoff §4](handoff-codex.md#4-e2e-playwright).

## Falta

COR-10 (aguarda ok do dono no [ADR 0017](../../arquitetura/adr/0017-permissoes-por-categoria.md)), auditoria, E2E, validação visual e docs finais — ver [handoff](handoff-codex.md). Perguntas abertas: [decisões](decisoes.md#perguntas-ao-dono-abertas).
