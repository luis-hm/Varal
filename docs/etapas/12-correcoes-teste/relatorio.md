# Relatório — Etapa 12

> **Contém:** o que a etapa entregou, os testes, o que ficou com o dono.
> **Origem:** sessões do Claude Code de 18/11/2026. Base: [spec](spec.md), [decisões](decisoes.md), [handoff](handoff-codex.md).

## Feito

| COR | Resultado |
| --- | --- |
| COR-01 | Voltar à aba revalida a sessão sem mascarar a tela. Só mascara quando a identidade muda, a API responde 401/403 ou acontece `pagehide`. |
| COR-02/03 | Contas sem mês obrigatório. Mês, status, categoria e pagador combinam. |
| COR-04 | Casa vira categoria, com 14 ícones ([ADR 0016](../../arquitetura/adr/0016-categorias-com-icone.md)). |
| COR-05 | Contas abre pessoal; `?espaco=` escolhe o grupo. |
| COR-06 | Nova conta nasce no destino da tela: grupo, categoria ou Contas filtrada por grupo. No Início, é pessoal. |
| COR-07 | "Sem categoria" aparece no resumo, no filtro e em tela própria. Um filtro ativo continua visível e removível. |
| COR-08 | Grupo, Início, Contas, Detalhe e Perfil com 24px entre seções. Margem lateral de 20px no celular também em Avisos e no modo simples. |
| COR-09 | Perfil redesenhado: identidade, dados, preferências, exportar e zona de perigo. Reautenticação em folha. |
| COR-10 | Permissões por categoria ([ADR 0017](../../arquitetura/adr/0017-permissoes-por-categoria.md)): regra central em `acesso.py`, endpoint do admin com versão e histórico, folha "Quem pode fazer o quê". Nova conta e recorrências oferecem só as categorias permitidas. Quem muda de papel ou entra no grupo recebe o padrão do papel; quem cria nasce pagador. |
| COR-11 | Navegação Grupos → grupo → categoria → contas → detalhe, e volta para a categoria. |
| COR-12 | Referrer `strict-origin` em `/entrar` e `/criar-conta` (Next e edge). Falta a URI no Google Console, que é ação do dono. |

## Auditoria do escopo inicial

- Confirmações abrem em folha do app, não em `window.confirm`: remover membro, sair, encerrar recorrência, desfazer pagamento e cancelar conta.
- Recorrência clicada no grupo abre direto nela.
- CU02: criar grupo já abre o convite. Fechar o convite antes de o link chegar deixava um convite pendente; agora esse link também é revogado (RN31).
- CU01: e-mail já cadastrado oferece entrar ou recuperar a senha.
- CU05: PDF inválido ou sem código oferece colar o código.
- Textos com "5 MB" unificados; código sem uso removido; espaçamentos soltos trocados por tokens.
- Validação visual nas duas larguras ([evidências](evidencias/)). Corrigidos três defeitos:
  - no Perfil a 390px, o botão "Sair da conta" espremia o nome;
  - nome longo sobrepunha a borda na folha de permissões;
  - "Preferências de notificações" ficava com espaço vazio.

## Testes (18/11/2026)

| Suíte | Resultado |
| --- | --- |
| API (pytest, projeto `varaltest`) | 569/569. Ruff limpo. |
| Web (Vitest) | 171/171. `tsc` e ESLint limpos. |
| Tipos (`make types`) | Sem diferença. |
| E2E (Playwright, 390×844 e 1440×900) | 153 passaram, 3 pulados. Os 2 casos acrescentados depois (CU05 e recorrência clicada) foram rodados à parte: 4/4. |

O E2E rodou na stack isolada `varaltest`, com o Next na porta 3100, porque a 3000 estava ocupada por outro projeto da máquina. Por isso as specs usam `ORIGIN` em vez de `localhost:3000`.

Casos novos estão em `web/e2e/etapa12.spec.ts`:

- CA01: sessão ao voltar à aba;
- CA02/04: Contas pessoal, todos os meses, mês e status combinados;
- CA03/05/06/08: categoria com ícone, navegação, Sem categoria e destino do "+";
- CA10: membro sem "Ver";
- recorrência clicada;
- capturas.

As specs antigas foram ajustadas às regras novas (COR-05/06, CU01, COR-09).

## Ajustes aplicados

Nenhum. Todos os itens de "Varal — Ajustes" já estavam marcados como feitos (lido em 18/11/2026).

## Depois do fechamento: Q12-2 (nome)

Aprovado pelo dono em 18/11/2026, na branch `etapa/12-nome-perfil`:

- Cadastro com "Nome (opcional)", até 150 caracteres (`ACCOUNT_SIGNUP_FORM_CLASS`).
- Perfil edita o nome no cartão "Seus dados" (`PATCH /api/me/`, só o próprio nome; vazio é permitido).
- Frames novos no Doop: 14 · Perfil (`jbgXyOMpqy`) e D07 · Perfil (`GLWxRQP3Lr`). O frame 01/D01 não ganhou o campo; ele segue o componente Field.
- Testes: API 560/560; web 174/174; E2E `auth` + `etapa12` + `privacidade11` 42/42. Capturas `perfil-nome-*`.

## Pendências do dono

- Google Console: cadastrar `https://hmgvaral.codehub.systems/accounts/google/login/callback/` e testar o login Google na HMG (COR-12).
- `make e2e` na máquina do dono: a senha do volume `varal_pgdata` não confere com o `infra/.env` atual, e a porta 3000 está em uso.
