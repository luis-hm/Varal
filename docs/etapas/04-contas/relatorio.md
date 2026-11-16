# Relatório — Etapa 04 (Contas, núcleo)

> **Contém:** entregas, CAs e testes, comparação com o Doop, segurança, ajustes, revisão do dono, decisões em aberto e pendências da Etapa 04.
> **Origem:** branch `etapa/04-contas` (commits a250a74, 009c3e4, 94a224d, 1c17132, 6e5b847, 19fb5fe, f072ce5; revisão do dono em e39c115, 4c9a1b2, 612aa34, d994907, 4539db0, 3d4ba32, 292ba72, f78a878), QA, revisão `varal-seguranca`, [decisoes.md](decisoes.md) e "Varal — Ajustes" rev 24 relido ao vivo em 15/11/2026.

**Estado: concluída em 15/11/2026.** O merge na `main` aguarda o dono confirmar as decisões em aberto (veja [abaixo](#decisões-para-o-dono-confirmar)). Sem push; a Etapa 05 só começa com novo `/etapa`.

## Entregas

- **Modelo (RF10, RF11, RN11, RN12, RN22, RN30):** `apps/lancamentos` com `Lancamento` (centavos > 0 e status válidos no banco, índice `(espaco, vencimento)`, `acesso` em `lancamento_acesso`) e `Historico`; sem categoria (ADR 0005). `criador`, `pagador` e autor do histórico `SET_NULL` ("Ex-membro"). Migrações `lancamentos.0001` e `espacos.0006` (janela 1–7, valores fora do intervalo ajustados sem perda). Admin do Django só leitura. Detalhes em [modelo](../../dados/modelo.md#implementação-da-etapa-04).
- **Visibilidade (RN02, RN06, RN07, RNF01, ADR 0008):** `acesso.py` com `lancamentos_visiveis`, `lancamento_ou_404` (404 para quem não vê, 403 só para quem vê sem `editar_conta`) e `quem_ve`. Lista, detalhe, totais, contagens, `atencao`, `por_casa` e `opcoes` saem só daí. Admin não vê restrita por ser admin.
- **Status calculado (RN12, RN13, RNF11):** `com_status` anota `vence`/`vencida` sobre `pendente` com `timezone.localdate()` (Fortaleza) e a janela do espaço; janela editável pelo admin (`PATCH /api/grupos/{id}/`).
- **Serviços:** criar, editar (histórico só do que mudou; 400 da Q19b), cancelar (só abertas; nada é apagado). RN21 e RN32 em `_desligar`: a saída voluntária bloqueia com 409 `conta_restrita_orfa` e aceita `resolucoes` (ADR 0007); a remoção pelo admin cancela a órfã sem sinal ao admin; a troca para pagador preserva o acesso (ADR 0008); a guarda `pre_delete` em `Usuario` bloqueia a exclusão.
- **API:** contas, `resumo`, `opcoes` na lista, `sair` com `resolucoes` e `usuario` no MembroSerializer ([api/README](../../api/README.md#contas-etapa-04)). Seed com os casos de visibilidade.
- **P5:** `ACCOUNT_RATE_LIMIT_SIGNUP` só no `make e2e` e no job `e2e` (1c17132); saiu o retry em 429 do E2E.
- **Web:** Início (02 ↔ D02) com "Total de <mês>", `count-up`, varal `swing` e "Precisa de atenção"; Contas e Detalhe (03/07 ↔ D03) com filtros na URL, folha "Filtros" no mobile e painel `slide-in`; formulário em folha/modal com o aviso "Quem paga também vê esta conta"; espaço atual em cookie (seletor no SideNav e no cabeçalho do Início); "Configurações" do grupo (só admin); folha de saída barrada pela RN32; lista do pagador em `/grupos/[id]/simples`; HouseCard com total e "N contas". BillCard novo; vitrine atualizada; linha do healthcheck removida.
- **Variáveis fora do Doop:** `--tracking-hero`, `--text-tag`, `--text-tag-desktop`, `--leading-small`, `--shadow-selected`, `--opacity-cancelled`, `--list-width` e, na revisão do dono, `--hero-padding-y` e `--hero-varal-width` (D04-2). Nenhuma cor nova ([tokens](../../design/tokens.md#fora-do-doop)).

## Critérios e testes

**CA01–CA34 passam.** Nomes completos na [matriz](../../matriz-rastreabilidade.md) (tabela CA → testes do QA e tabela das decisões 23 e 26–30). Testes em `api/tests/test_contas.py`, `web/src/**/*.test.ts(x)` e `web/e2e/contas.spec.ts` (API e PostgreSQL reais).

| CA | Evidência principal |
| --- | --- |
| CA01–CA04 | `test_rf10_*`, `test_rn11_*`, `test_rn05_contas_por_papel`, `test_rf11_casa_pagador_e_escolhidos_validados`, `test_rn01_rf11_editar_com_dados_de_outro_grupo_400_e_nada_grava`; E2E `ca01/ca16/ca17/ca31…` |
| CA05–CA09 | `test_rn02_*`, `test_rn01_rnf01_*`, `test_rn06_admin_nao_escolhido_404_e_agregados_sem_a_conta`, `test_rn06_pagador_nao_escolhido_ve_a_conta`, `test_rn07_*`, `test_rn06_rn07_acesso_explicito_prevalece`; E2E `ca07/ca08/ca09/ca28…` |
| CA10–CA11 | `test_rn12_*`, `test_rnf11_hoje_em_fortaleza`, `test_rn13_*` (inclui `test_rn13_atencao_inclui_aguardando_na_janela`); E2E `ca11 rn13 q10…` |
| CA12–CA17 | `test_rn22_*`, `test_d2_*`, `test_rf13_*`; Vitest `inicio.test.tsx`, `contas.test.ts`; E2E `ca12/ca13/ca14…`, `ca15…`, `dec27` |
| CA18–CA25 | `test_rn21_*`, `test_rn32_*` (inclui `concorrencia_editar_e_sair` e `concorrencia_excluir_conta_e_remocao_admin`, com threads), `test_rn05_rn32_*`, `test_rn06_rn07_alterar_papel_preserva_acesso`; E2E `ca19/ca22/ca23…`, `ca20/ca21/ca22…` |
| CA26 | `test_rn30_criador_excluido_ex_membro`, `test_rn30_historico_sem_email_ex_membro_apos_saida_ou_exclusao`, `test_rn30_nome_por_contexto_membro_sem_nome_ex_membro`; E2E `dec23` |
| CA27–CA32 | Vitest `nav.test.tsx`, `conta-folha.test.tsx`, `app-shell.test.tsx`, `nome.test.tsx`; E2E `ca27…`, `ca29…` (screenshots), `ca30…`, `ca32…` (360px, movimento reduzido), `dec28`–`dec30` |
| CA33 | `make types` sem diff |
| CA34 | Tabela abaixo; segurança sem bloqueantes; docs e matriz atualizadas |

| Verificação final (f78a878, Node 22, API fria) | Resultado |
| --- | --- |
| `make test` | **207 pytest e 73 Vitest passaram** (no fechamento: 204 e 65) |
| `make lint` | **Passou** (ruff, ESLint, `tsc`) |
| `make types` | **Sem diff** |
| `make e2e` | **83 passaram, 3 ignorados de propósito** (360px só no mobile; `dec27` só no desktop); nenhum 429 |

**Registro honesto do E2E:** uma execução anterior teve um 429 isolado no primeiro cadastro, na partida a frio da API recriada pelo `make e2e` (o `cache_lock` do allauth espera 1 s no Redis), e duas medições feitas durante animações. Resolvido (P8, e39c115): o `globalSetup` do Playwright faz um cadastro sozinho antes dos workers, e as medições esperam `modal-pop`/`sheet-up` terminarem. Na revisão do dono, o Vitest `ca28` estourava o `findBy` de 1 s sob carga; a espera passou a 5 s, com justificativa no arquivo (f78a878).

**Correções do QA (19fb5fe):** Chip com rótulo longo trunca com reticências e `title`; a vitrine `/dev/componentes` não rola mais em 360px; E2E `grupos` e `auth` ajustados ao Início, ao HouseCard e ao seletor por cookie; helpers movidos para `web/e2e/fixtures.ts`.

## Comparação com o Doop (CA29)

Screenshots `web/e2e/__screens__/` (`inicio-*`, `contas-*`, `conta-detalhe-*`, `conta-form-*`, `grupo-*`) comparados com 02/D02, 03/D03, 07, 05/M01, 06/M02 e 10/D04 em 390×844 e 1440×900. Composição, componentes, cores, fontes e espaçamentos correspondem, exceto as diferenças esperadas da [spec](spec.md#telas-do-doop) e estas, que continuam:

1. **03 mobile:** "Total de novembro: R$ … · espaço" quebra em 2 linhas (efeito da Q9).
2. **D03:** os chips de filtro quebram em 2 linhas por causa de "Canceladas" e "Quem paga".
3. O campo de data aparece em mm/dd/yyyy no Chromium en-US do Playwright (o formato segue o idioma do navegador).

As diferenças 1 (vazio no hero do D02), 4 (TabBar no 07), 5 (nomes em várias linhas) e 6 (ordem de "Onde fica") do fechamento viraram as decisões 27–30, respondidas pelo dono e implementadas em 3d4ba32 ([revisão do dono](#revisão-do-dono)). Canvas não alterado.

## Segurança

Revisão `varal-seguranca`: **sem bloqueantes**. Correções em f072ce5, com testes que falham sem elas.

- **I1 (corrigido):** corrida entre editar a conta (tirando-se de "Quem vê" e pondo X) e a saída ou remoção de X deixava uma restrita aberta sem ninguém. Agora saída, remoção e troca de papel travam todas as restritas abertas do grupo antes de calcular órfãs. Isso revelou um segundo deadlock (`FOR UPDATE` do `Usuario` pelo `select_related` × FK deferida da edição), corrigido com `select_for_update(of=("self",))`. Teste `test_rn32_concorrencia_editar_e_sair` (sair e remover).
- **I2 (corrigido):** o histórico gravava e-mail ou nome. Agora `dados` guarda ids e a leitura resolve os nomes ("Pessoa sem nome"/"Ex-membro", nunca e-mail). Teste `test_rn30_historico_sem_email_ex_membro_apos_saida_ou_exclusao`.
- **M1 (corrigido):** deadlock entre excluir a conta de usuário e o admin remover. Ordem única de travas: admins → membro → contas. Teste `test_rn32_concorrencia_excluir_conta_e_remocao_admin`.
- **M3 (corrigido):** `resolucoes` sem limite; agora no máximo 50.
- **M7 (corrigido):** faltava teste de PATCH com casa, pagador ou escolhido de outro grupo. Teste `test_rn01_rf11_editar_com_dados_de_outro_grupo_400_e_nada_grava`.
- **Aceitos pelo `varal-seguranca`, sem mudança; o dono pediu para confirmar:**
  - **M2 (Q04-31):** uma consulta a mais em `lancamento_ou_404` quando a conta existe; só revela algo a quem já tem o UUID.
  - **M4 (Q04-32, decide-se na Q04-36):** o pagador recebe nomes de membros no 409 da saída (`pessoas`), exigido pelo ADR 0007; depois da decisão 23, também e-mails de quem não tem nome.
  - **M5 (Q04-33):** o admin do Django mostra restritas ao superusuário; é ferramenta de operador. Minimização de dados na Etapa 11.
  - **M6 (Q04-34):** o container `api` de dev herda `ACCOUNT_RATE_LIMIT_SIGNUP` do último `make e2e` até o próximo `make dev`.

## Desvios em relação ao plano

- Ação nova `acesso_removido` no histórico (RN21 tirando alguém de "Quem vê"); o plano só previa `pagador_removido`.
- Opções dos filtros "Casa" e "Quem paga" vêm do campo `opcoes` da lista (`casas`, `pagadores`, `sem_pagador`), calculado só sobre o visível do mês. Não é endpoint próprio.
- `MembroSerializer` ganhou `usuario` (id do usuário), usado em "Quem paga" e "Quem vê".
- `Historico.dados` com ids de usuário em vez de nomes (I2).
- Revisão do dono: componente `<Nome>` (`web/src/components/ui/nome.tsx`), fora do Doop, para nomes e e-mails em uma linha (decisão 29).

## Ajustes aplicados

Nenhum. "Varal — Ajustes" relido ao vivo no fim (rev 24): os 18 itens já estão marcados e não há itens novos.

## Ajustes pendentes

Nenhum.

## Revisão do dono

Respostas de 15/11/2026 ("Etapa 04 aprovada"), nas palavras dele em [decisoes.md](decisoes.md#respostas-do-dono-15112026-mensagem-etapa-04-aprovada).

| Decisão | Resposta | O que foi feito |
| --- | --- | --- |
| 23 · nome de pessoa | Por contexto: membro atual pelo nome ou, sem nome, pelo e-mail; quem saiu ou excluiu a conta é "Ex-membro", nunca o e-mail; histórico com id e nome resolvido na hora | 4c9a1b2: `rotulo` por contexto no detalhe, na lista, nas opções e no 409. Histórico mostra "Pessoa sem nome" ou "Ex-membro", inclusive nas linhas automáticas; quem volta ao grupo volta pelo nome (D04-8, D04-9). Testes `test_rn30_*` e E2E `dec23` |
| 26 · `aguardando` em "Precisa de atenção" | Entra toda conta aberta, `pendente` ou `aguardando`, vencida ou dentro da janela da RN13; o selo mostra o status real | 4c9a1b2: `atencao` pela data, contagens do hero separadas pela data. Teste `test_rn13_atencao_inclui_aguardando_na_janela`; sem E2E (a API ainda não cria `aguardando`). O chip "Vencidas" segue pelo status: em aberto na Q04-35 |
| 27 · vazio no hero do D02 | Corrigir agora; o container encolhe sem a barra | 3d4ba32: hero em grade de 2 colunas sem altura fixa, varal de 560px à direita, pílula "N contas" mantida (D04-1 a D04-3); tokens `--hero-padding-y` e `--hero-varal-width`. E2E `dec27` |
| 28 · TabBar no detalhe mobile | Tirar; detalhe é tela empilhada, com TopBar e voltar | 3d4ba32: `/contas/[id]` abaixo de 1024px sem TabBar, com TopBar e voltar também em carregando, erro e "Conta não encontrada" (D04-4). Vitest `app-shell.test.tsx`; E2E `dec28` |
| 29 · nomes e e-mails longos | Uma linha com reticências, valor inteiro no `title`/aria; testar com e-mail longo | 3d4ba32: `<Nome>` no BillCard, detalhe, MemberRow e SideNav; saudação do Início e Chip cortam igual (D04-5, D04-6). Vitest `nome.test.tsx`; E2E `dec29` com e-mail longo. Em aberto: Q04-38 e Q04-39 |
| 30 · ordem em "Onde fica" | Espaço atual primeiro e já selecionado | 3d4ba32: `espacosParaCriar` ordena pelo espaço atual; observador mantém a ordem e seleciona o primeiro; edição fica no espaço da conta (D04-7). Vitest `conta-folha.test.tsx`; E2E `dec30` |

Na mesma mensagem: Node 22 (D04-12), CI com `workflow_dispatch` (D04-13) e `make limpar-dev` (D04-11), em 612aa34. Fora da etapa: Codex com os mesmos comandos e agentes (d994907) e o agente `varal-decisor` (4539db0).

## Decisões para o dono confirmar

Tudo em [decisoes.md](decisoes.md), com proposta, caso contra e o que fazer enquanto não houver resposta. Nada bloqueia o código; o merge na `main` espera estas respostas.

- **Decisões 1–22, 24 e 25** (Q04-1 a Q04-22, Q04-24, Q04-25): padrões implementados nas Etapas 03 e 04.
- **Achados de segurança aceitos:** M2 (Q04-31), M5 (Q04-33) e M6 (Q04-34). O M4 (Q04-32) se decide na Q04-36.
- **Perguntas novas da auditoria:** Q04-35 ("vencida" com `aguardando`: hero × chip), Q04-36 (e-mail de membro sem nome para o pagador), Q04-37 (vários "Ex-membro" no filtro "Quem paga"), Q04-38 ("Quem vê" cortado numa linha) e Q04-39 (nome de grupo cortado no seletor e em "Onde fica").

## Pendências

- **P6 (abertura da 05):** reexportar a origem rev 50 (sem categoria) e alinhar CU05, `dados/modelo.md` e ADR 0005.
- **P7 (Etapa 09):** aviso ao removido das contas canceladas pela RN32 (decisão 25).
- **P8:** aberta e resolvida nesta etapa (veja o registro do E2E).
- **P9:** confirmar no próximo push que o CI dispara (`gh run list`; se nada aparecer, `gh workflow run web.yml --ref main`). Causa e correção em [PROGRESSO](../../PROGRESSO.md#resolvidas).
- **P1, P3, P4:** sem mudança (Etapas 06 e 11).
- **Banco de dev:** `make limpar-dev` existe e não foi executado; o dono roda quando quiser. A prévia apagaria 5 grupos de teste, 302 grupos sem membros e 858 usuários de teste.
- **Sem push:** nada desta etapa foi enviado ao remoto.
