# Relatório — Etapa 04 (Contas, núcleo)

> **Contém:** entregas, CAs e testes, comparação com o Doop, segurança, ajustes, decisões a confirmar e pendências da Etapa 04.
> **Origem:** branch `etapa/04-contas` (commits a250a74, 009c3e4, 94a224d, 1c17132, 6e5b847, 19fb5fe, f072ce5), QA, revisão `varal-seguranca` e "Varal — Ajustes" rev 24 relido ao vivo em 15/11/2026.

**Estado: concluída em 15/11/2026.** Sem push; a Etapa 05 só começa com novo `/etapa`.

## Entregas

- **Modelo (RF10, RF11, RN11, RN12, RN22, RN30):** `apps/lancamentos` com `Lancamento` (centavos > 0 e status válidos no banco, índice `(espaco, vencimento)`, `acesso` em `lancamento_acesso`) e `Historico`; sem categoria (ADR 0005). `criador`, `pagador` e autor do histórico `SET_NULL` ("Ex-membro"). Migrações `lancamentos.0001` e `espacos.0006` (janela 1–7, valores fora do intervalo ajustados sem perda). Admin do Django só leitura. Detalhes em [modelo](../../dados/modelo.md#implementação-da-etapa-04).
- **Visibilidade (RN02, RN06, RN07, RNF01, ADR 0008):** `acesso.py` com `lancamentos_visiveis`, `lancamento_ou_404` (404 para quem não vê, 403 só para quem vê sem `editar_conta`) e `quem_ve`. Lista, detalhe, totais, contagens, `atencao`, `por_casa` e `opcoes` saem só daí. Admin não vê restrita por ser admin.
- **Status calculado (RN12, RN13, RNF11):** `com_status` anota `vence`/`vencida` sobre `pendente` com `timezone.localdate()` (Fortaleza) e a janela do espaço; janela editável pelo admin (`PATCH /api/grupos/{id}/`).
- **Serviços:** criar, editar (histórico só do que mudou; 400 da Q19b), cancelar (só abertas; nada é apagado). RN21 e RN32 em `_desligar`: a saída voluntária bloqueia com 409 `conta_restrita_orfa` e aceita `resolucoes` (ADR 0007); a remoção pelo admin cancela a órfã sem sinal ao admin; a troca para pagador preserva o acesso (ADR 0008); a guarda `pre_delete` em `Usuario` bloqueia a exclusão.
- **API:** contas, `resumo`, `opcoes` na lista, `sair` com `resolucoes` e `usuario` no MembroSerializer ([api/README](../../api/README.md#contas-etapa-04)). Seed com os casos de visibilidade.
- **P5:** `ACCOUNT_RATE_LIMIT_SIGNUP` só no `make e2e` e no job `e2e` (1c17132); saiu o retry em 429 do E2E.
- **Web:** Início (02 ↔ D02) com "Total de <mês>", `count-up`, varal `swing` e "Precisa de atenção"; Contas e Detalhe (03/07 ↔ D03) com filtros na URL, folha "Filtros" no mobile e painel `slide-in`; formulário em folha/modal com o aviso "Quem paga também vê esta conta"; espaço atual em cookie (seletor no SideNav e no cabeçalho do Início); "Configurações" do grupo (só admin); folha de saída barrada pela RN32; lista do pagador em `/grupos/[id]/simples`; HouseCard com total e "N contas". BillCard novo; vitrine atualizada; linha do healthcheck removida.
- **Variáveis fora do Doop:** `--tracking-hero`, `--text-tag`, `--text-tag-desktop`, `--leading-small`, `--shadow-selected`, `--opacity-cancelled`, `--list-width`. Nenhuma cor nova ([tokens](../../design/tokens.md#fora-do-doop)).

## Critérios e testes

**CA01–CA34 passam.** Nomes completos na [matriz](../../matriz-rastreabilidade.md) (tabela CA → testes do QA). Testes em `api/tests/test_contas.py`, `web/src/**/*.test.ts(x)` e `web/e2e/contas.spec.ts` (12 testes × 2 resoluções, API e PostgreSQL reais).

| CA | Evidência principal |
| --- | --- |
| CA01–CA04 | `test_rf10_*`, `test_rn11_*`, `test_rn05_contas_por_papel`, `test_rf11_casa_pagador_e_escolhidos_validados`, `test_rn01_rf11_editar_com_dados_de_outro_grupo_400_e_nada_grava`; E2E `ca01/ca16/ca17/ca31…` |
| CA05–CA09 | `test_rn02_*`, `test_rn01_rnf01_*`, `test_rn06_admin_nao_escolhido_404_e_agregados_sem_a_conta`, `test_rn06_pagador_nao_escolhido_ve_a_conta`, `test_rn07_*`, `test_rn06_rn07_acesso_explicito_prevalece`; E2E `ca07/ca08/ca09/ca28…` |
| CA10–CA11 | `test_rn12_*`, `test_rnf11_hoje_em_fortaleza`, `test_rn13_*`; E2E `ca11 rn13 q10…` |
| CA12–CA17 | `test_rn22_*`, `test_d2_*`, `test_rf13_*`; Vitest `inicio.test.tsx`, `contas.test.ts`; E2E `ca12/ca13/ca14…`, `ca15…` |
| CA18–CA25 | `test_rn21_*`, `test_rn32_*` (inclui `concorrencia_editar_e_sair` e `concorrencia_excluir_conta_e_remocao_admin`, com threads), `test_rn05_rn32_*`, `test_rn06_rn07_alterar_papel_preserva_acesso`; E2E `ca19/ca22/ca23…`, `ca20/ca21/ca22…` |
| CA26 | `test_rn30_criador_excluido_ex_membro`, `test_rn30_historico_sem_email_e_ex_membro_apos_exclusao` |
| CA27–CA32 | Vitest `nav.test.tsx`, `conta-folha.test.tsx`; E2E `ca27…`, `ca29…` (screenshots), `ca30…`, `ca32…` (360px, movimento reduzido) |
| CA33 | `make types` sem diff |
| CA34 | Tabela abaixo; segurança sem bloqueantes; docs e matriz atualizadas |

| Verificação final | Resultado |
| --- | --- |
| `make test` | **204 pytest e 65 Vitest (18 arquivos) passaram** |
| `make lint` | **Passou** (ruff, ESLint, `tsc`) |
| `make types` | **Sem diff**, salvo a descrição de `Historico.dados` (f072ce5), já commitada |
| `make e2e` | **74 passaram, 2 ignorados de propósito** (360px só no projeto mobile); nenhum 429 |

**Registro honesto do E2E:** uma execução anterior teve um 429 isolado no primeiro cadastro, na partida a frio da API recriada pelo `make e2e` (o `cache_lock` do allauth espera 1 s no Redis). A reexecução completa passou. Fica como P8.

**Correções do QA (19fb5fe):** Chip com rótulo longo trunca com reticências e `title`; a vitrine `/dev/componentes` não rola mais em 360px; E2E `grupos` e `auth` ajustados ao Início, ao HouseCard e ao seletor por cookie; helpers movidos para `web/e2e/fixtures.ts`.

## Comparação com o Doop (CA29)

Screenshots `web/e2e/__screens__/` (`inicio-*`, `contas-*`, `conta-detalhe-*`, `conta-form-*`, `grupo-*`) comparados com 02/D02, 03/D03, 07, 05/M01, 06/M02 e 10/D04 em 390×844 e 1440×900. Composição, componentes, cores, fontes e espaçamentos correspondem, exceto as diferenças esperadas da [spec](spec.md#telas-do-doop) e estas:

1. **D02:** pílula "N CONTAS" ao lado de "Total de novembro", com um vazio onde ficava a barra (efeito da Q12).
2. **03 mobile:** "Total de novembro: R$ … · espaço" quebra em 2 linhas (efeito da Q9).
3. **D03:** os chips de filtro quebram em 2 linhas por causa de "Canceladas" e "Quem paga".
4. **07 mobile:** a TabBar continua visível no detalhe; o frame 07 não tem TabBar.
5. Nomes longos ou e-mail quebram em várias linhas no BillCard e no detalhe.
6. **M01:** "Onde fica" põe Pessoal primeiro; no Doop o grupo vem primeiro.
7. O campo de data aparece em mm/dd/yyyy no Chromium en-US do Playwright (o formato segue o idioma do navegador).

Canvas não alterado.

## Segurança

Revisão `varal-seguranca`: **sem bloqueantes**. Correções em f072ce5, com testes que falham sem elas.

- **I1 (corrigido):** corrida entre editar a conta (tirando-se de "Quem vê" e pondo X) e a saída ou remoção de X deixava uma restrita aberta sem ninguém. Agora saída, remoção e troca de papel travam todas as restritas abertas do grupo antes de calcular órfãs. Isso revelou um segundo deadlock (`FOR UPDATE` do `Usuario` pelo `select_related` × FK deferida da edição), corrigido com `select_for_update(of=("self",))`. Teste `test_rn32_concorrencia_editar_e_sair` (sair e remover).
- **I2 (corrigido):** o histórico gravava e-mail ou nome. Agora `dados` guarda ids e a leitura resolve os nomes ("Pessoa sem nome"/"Ex-membro", nunca e-mail). Teste `test_rn30_historico_sem_email_e_ex_membro_apos_exclusao`.
- **M1 (corrigido):** deadlock entre excluir a conta de usuário e o admin remover. Ordem única de travas: admins → membro → contas. Teste `test_rn32_concorrencia_excluir_conta_e_remocao_admin`.
- **M3 (corrigido):** `resolucoes` sem limite; agora no máximo 50.
- **M7 (corrigido):** faltava teste de PATCH com casa, pagador ou escolhido de outro grupo. Teste `test_rn01_rf11_editar_com_dados_de_outro_grupo_400_e_nada_grava`.
- **Aceitos e registrados, sem mudança:**
  - **M2:** uma consulta a mais em `lancamento_ou_404` quando a conta existe; só revela algo a quem já tem o UUID.
  - **M4:** o pagador recebe nomes de membros no 409 da saída (`pessoas`), exigido pelo ADR 0007.
  - **M5:** o admin do Django mostra restritas ao superusuário; é ferramenta de operador. Minimização de dados na Etapa 11.
  - **M6:** o container `api` de dev herda `ACCOUNT_RATE_LIMIT_SIGNUP` do último `make e2e` até o próximo `make dev`.

## Desvios em relação ao plano

- Ação nova `acesso_removido` no histórico (RN21 tirando alguém de "Quem vê"); o plano só previa `pagador_removido`.
- Opções dos filtros "Casa" e "Quem paga" vêm do campo `opcoes` da lista (`casas`, `pagadores`, `sem_pagador`), calculado só sobre o visível do mês. Não é endpoint próprio.
- `MembroSerializer` ganhou `usuario` (id do usuário), usado em "Quem paga" e "Quem vê".
- `Historico.dados` com ids de usuário em vez de nomes (I2).

## Ajustes aplicados

Nenhum. "Varal — Ajustes" relido ao vivo no fim (rev 24): os 18 itens já estão marcados e não há itens novos.

## Ajustes pendentes

Nenhum.

## Decisões para o dono confirmar

Implementadas com o padrão abaixo; nada bloqueia.

| # | Origem | Assunto | Padrão adotado |
| --- | --- | --- | --- |
| 1 | Etapa 03, 1 | Limite de aceite (RN31) | 10/h por usuário; por IP só com a P3 |
| 2 | Etapa 03, Q1 | Entropia do token de convite | 256 bits (`token_urlsafe(32)`) |
| 3 | Etapa 03, Q2 | "Gerenciar papéis" (D04) | Escondido; o admin toca na linha do membro |
| 4 | Etapa 03, Q3 | Sair do grupo | Vale para todo papel, inclusive observador e pagador |
| 5 | Etapa 03, Q4 | Grupo de um membro só | O único admin não pode sair, com mensagem |
| 6 | Etapa 03, Q5 | Telas sem frame | Montadas com os componentes do `varal-ui` |
| 7 | Etapa 03, 3 | Fundo atrás da folha | `--scrim-sheet` ink 60%; o frame 11 pinta sólido |
| 8 | Etapa 03, 4 | Detalhe do seletor | `Grupo · <papel>` |
| 9 | Etapa 03, 5 | Confirmações | `window.confirm` nativo (agora também em "Cancelar conta") |
| 10 | Etapa 03, 6 | Foco no `<dialog>` | Comportamento nativo |
| 11 | Etapa 03, 7 | Nomes longos de casa | Quebram no meio da palavra no mobile |
| 12 | Etapa 03, 8 | Membro sem nome | Aparece pelo e-mail na página do grupo |
| 13 | Spec 04, decisão 1 | Rotas | `/`, `/contas?mes=&status=&casa=&pagador=`, `/contas/[id]`; mesmas nas duas larguras |
| 14 | Spec 04, decisão 2 | Espaço atual | Cookie `espaco` validado contra `/api/me/`; inválido → pessoal; grupo de pagador → `/grupos/[id]/simples` sem gravar |
| 15 | Spec 04, decisão 3 | `on_delete` | `criador`, `pagador` e autor do histórico `SET_NULL`; `espaco` `CASCADE`; `subgrupo` `RESTRICT` |
| 16 | Spec 04, decisão 4 | Hoje | `timezone.localdate()` (Fortaleza); `vencimento` é data civil |
| 17 | Spec 04, decisão 5 | Status calculado | Só `pendente` vira `vence`/`vencida` |
| 18 | Spec 04, decisão 6 | Conta pessoal | Pagador = dono, visibilidade `grupo`, sem casa; campos escondidos no formulário |
| 19 | Spec 04, decisão 7 | Escolhidos em "Quem vê" | Novos só admin, membro ou observador; quem já estava e virou pagador continua |
| 20 | Spec 04, decisão 8 | Ações automáticas | Sem autor; nunca aparecem como "Ex-membro" |
| 21 | Backend 04 | Ação `acesso_removido` | Linha automática no histórico quando a RN21 tira alguém de "Quem vê" (`dados.pessoa`) |
| 22 | Backend 04 | `opcoes` dos filtros | Campo da lista com casas, pagadores e `sem_pagador` só das contas visíveis do mês |
| 23 | Backend 04 | Nome de quem não tem nome | Histórico: "Pessoa sem nome" (nunca e-mail). Detalhe, lista e opções: e-mail, a mesma regra do MembroSerializer. **Pergunta:** no detalhe, deve aparecer "Pessoa sem nome"? |
| 24 | Backend 04 | Ordem das travas | Admins → membro (`FOR UPDATE OF self`) → todas as restritas abertas do grupo por `pk` → contas da RN21; `editar` e `cancelar` travam só a conta. Vale para sair, remover, trocar papel e excluir usuário |
| 25 | P7 | Aviso ao removido | Adiado para a Etapa 09; a 04 só grava `cancelada_automaticamente` com `dados.removido` |
| 26 | Q9 | Conta `aguardando` no Início | Não entra em "Precisa de atenção" (só `pendente` vira `vence`/`vencida`). **Pergunta:** deve entrar? |
| 27 | Diferença visual 1 | D02 | Pílula "N CONTAS" com vazio no lugar da barra |
| 28 | Diferença visual 4 | 07 mobile | TabBar visível no detalhe |
| 29 | Diferença visual 5 | BillCard e detalhe | Nomes longos ou e-mail quebram em várias linhas |
| 30 | Diferença visual 6 | M01 | "Onde fica" com Pessoal primeiro |

A decisão 2 da Etapa 03 (rota do pagador) foi confirmada pela Q5 desta etapa.

## Pendências

- **P6 (abertura da 05):** reexportar a origem rev 50 (sem categoria) e alinhar CU05, `dados/modelo.md` e ADR 0005.
- **P7 (Etapa 09):** aviso ao removido das contas canceladas pela RN32 (decisão 25).
- **P8 (nova):** 429 isolado do allauth na partida a frio do `make e2e`. Se repetir, o `varal-devops` aquece a API antes do Playwright.
- **P1, P3, P4:** sem mudança (Etapas 06 e 11).
- **Banco de dev** com dados de teste antigos: grupo `x` (revisão de segurança da 03), grupos "Teste UI …" e 4 contas `burst-*@varal.test` do QA. Nada foi apagado.
- **Node local v20**; o projeto pede 22+.
- **CI** não disparou no GitHub no push inicial (causa desconhecida).
- **Sem push:** nada desta etapa foi enviado ao remoto.
