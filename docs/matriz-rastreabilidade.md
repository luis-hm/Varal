# Matriz de rastreabilidade

> **Contém:** para cada requisito, os casos de uso, regras, telas do Doop, etapa e testes que o cobrem.
> **Origem:** `docs/especificacao-varal.md` (seções 4–7 e 12) e o plano de etapas; a coluna Testes é preenchida pelo `varal-qa`.

Telas: frame mobile ↔ frame desktop no canvas `k0kB5dc-Vo` (ids e equivalência em [design/README.md](design/README.md)). Testes: nome do teste com o ID da regra (`test_rn14_...`).

## Requisitos funcionais

| RF | CU | RN | Tela mobile ↔ desktop (Doop) | Etapa | Testes |
| --- | --- | --- | --- | --- | --- |
| RF01 | CU01 | RN03 | 01 · Entrar ↔ D01 | 02 | `api/tests/test_autenticacao.py`: `test_rf01_rf02_ca01_*`, `test_rf01_ca02_*`, `test_rf01_ca03_*`, `test_rf01_rn03_ca06_*`, `test_rf01_ca06_*`, `test_rf01_ca09_*`, `test_rf01_ca12_*`; E2E `rf01/rf02 rn03 ca01/ca03/ca09/ca10/ca11…` e `rf01 ca02…` (`web/e2e/auth.spec.ts`) |
| RF02 | CU01 | RN03 | 01 · Entrar ↔ D01 | 02 | `test_rf01_rf02_ca01_cadastro_email_sessao_hash_e_dois_usuarios`, `test_rn03_ca04_*`, `test_rn03_ca05_seed_idempotente_preserva_usuario_e_senha` (`api/tests/test_autenticacao.py`); `test_rn03_ca05_migracao_preserva_legado_e_cria_espaco_unico` (`api/tests/test_migracao_autenticacao.py`); E2E de cadastro/recarga/isolamento em `auth.spec.ts` |
| RF03 | CU01 | — | 01 · Entrar ↔ D01 | 02 | `test_rf03_ca07_recuperacao_resposta_generica_email_async`, `test_rf03_ca08_token_valido_troca_senha_e_nao_reutiliza`, `test_rf03_ca08_token_invalido_expirado_e_senha_fraca` (`api/tests/test_autenticacao.py`); Vitest `ca07`, `ca08` (`auth-form.test.tsx`, `client.test.ts`); E2E `rf03 ca07/ca08…` (`web/e2e/auth.spec.ts`) |
| RF04 | CU02 | RN04 | 10 · Grupo ↔ D04 | 03 | `api/tests/test_grupos.py`: `test_rf04_rn04_criar_grupo_criador_unico_admin_e_casas`, `test_rf04_criar_grupo_nome_invalido_nao_grava`, `test_rf04_rn04_criar_grupo_falha_no_meio_nao_grava`, `test_rn04_banco_recusa_grupo_com_dono_e_membro_duplicado`, `test_rn04_migracao_grupo_com_dono_vira_admin_sem_perder_dados`; E2E `ca01/ca04/ca05/ca17 rf04/rf05/rf07…` (`web/e2e/grupos.spec.ts`) |
| RF05 | CU03 | RN05, RN24, RN31 | 11 · Convidar membro ↔ M05 | 03 | `api/tests/test_grupos.py`: `test_rf05_rn24_rn31_link_inteiro_uma_vez_e_banco_so_com_hash`, `test_rf05_link_aberto_sem_sessao_e_aceito_depois_de_entrar`, `test_rf05_quem_ja_e_membro_nao_muda_papel_nem_consome_convite`, `test_rf05_me_e_lista_trazem_so_os_grupos_do_usuario`, `test_rn24_rn31_*`, `test_rn31_*`, `test_rnf02_retorno_google_preserva_proximo_local`; Vitest `ca04`/`ca05` (`aceite-convite.test.tsx`), `ca19/rn31` (`grupo-pagina.test.tsx`, `papeis.test.ts`), `ca04: proximo accepts only a local path`; E2E `ca01/ca04/ca05/ca17…`, `rnf02 ca04: ?proximo externo…`, `ca19/ca20 rn31…` (`web/e2e/grupos.spec.ts`) |
| RF06 | CU03 | RN04, RN05, RN21, RN32 (04), ADR 0007, ADR 0008 (04) | 10 · Grupo ↔ D04 | 03; RN21 nas contas, RN32 (sair bloqueia, remoção cancela), exceção da RN05 na saída e papel → pagador na 04 | `api/tests/test_grupos.py`: `test_rn04_ultimo_admin_nao_se_rebaixa_remove_nem_sai`, `test_rn04_com_outro_admin_pode_rebaixar_e_sair`, `test_rn04_concorrencia_dois_admins_sobra_um` (3 casos), `test_rn04_exclusao_usuario_ultimo_admin_orm_e_queryset`, `test_rn04_exclusao_usuario_ultimo_admin_admin_django`, `test_rn21_removido_e_quem_sai_perde_acesso_na_hora`, `test_rn21_rn31_saida_do_admin_revoga_convites_que_ele_gerou` (3 casos), `test_rn05_gestao_negada_a_quem_nao_e_admin`, `test_rn05_admin_gerencia`; Etapa 04: `test_rn21_abertas_perdem_pagador_pagas_mantem_e_criadas_ficam` (sair, remover), `test_rn32_*`, `test_rn05_rn32_*`, `test_rn06_rn07_alterar_papel_preserva_acesso` (`api/tests/test_contas.py`); Vitest `ca14/ca15`, `ca22/rn32: a blocked exit lists the bills…` (`grupo-pagina.test.tsx`); E2E `ca12/ca14 rf06 rn04/rn21…` (`web/e2e/grupos.spec.ts`), `ca19/ca22/ca23 rn32 adr0007…`, `ca20/ca21/ca22 rn32/rn06…` (`web/e2e/contas.spec.ts`) |
| RF07 | CU04 | — | 10 · Grupo ↔ D04 | 03 | `api/tests/test_grupos.py`: `test_rf07_criar_renomear_arquivar_casa`, `test_rn05_gestao_negada_a_quem_nao_e_admin` (casos `criar_casa`, `renomear_casa`, `arquivar_casa`); Vitest `ca18: a house with no bills has no progress bar`; E2E `ca01/ca04/ca05/ca17 rf04/rf05/rf07…` (+ Nova casa) e `ca20 rnf08/rnf09: 360px…` (editar casa) (`web/e2e/grupos.spec.ts`) |
| RF08 | CU05 | RN08, RN09, RN10, RN11 | 05 · Nova conta ↔ M01, 06 · Conferir conta ↔ M02 | 05 | — |
| RF09 | CU05 | RN11 | 05 · Nova conta ↔ M01, 06 · Conferir conta ↔ M02 | 05 | — |
| RF10 | CU05 | RN11 | 05 · Nova conta ↔ M01, 06 · Conferir conta ↔ M02 | 04 | `api/tests/test_contas.py`: `test_rf10_criar_conta_nasce_pendente_com_historico` (dono, admin, membro), `test_rn11_valor_invalido_400_e_nada_grava` (7 casos), `test_rn11_banco_recusa_valor_nao_positivo`, `test_rn05_contas_por_papel` (5 casos); Vitest `creating sends cents and opens the new bill in its month` (`conta-folha.test.tsx`), `money: pt-BR input to cents and back` (`contas.test.ts`); E2E `ca01/ca16/ca17/ca31 rf10/rf13 rn11 q12/q23…` (`web/e2e/contas.spec.ts`) |
| RF11 | CU05 | RN01, RN06, RN07, RN32, ADR 0005, ADR 0008 | 06 · Conferir conta ↔ M02 (sem frame: "Quem vê" e o aviso "Quem paga também vê esta conta") | 04 | `api/tests/test_contas.py`: `test_rf11_casa_pagador_e_escolhidos_validados` (casa alheia/arquivada, pagador fora/observador, escolhido fora/pagador, sem `categoria`, Q20), `test_rn06_rn07_acesso_explicito_prevalece`, `test_rn32_editar_sem_quem_veja_400`, `test_rn01_rf11_editar_com_dados_de_outro_grupo_400_e_nada_grava`; Vitest `ca28: restricted bill with another payer warns before saving…`, `q19b: the API's 400 message shows next to Quem vê…` (`conta-folha.test.tsx`); E2E `ca07/ca08/ca09/ca28 rn06/rn07…` (aviso antes de salvar, nas duas resoluções) (`web/e2e/contas.spec.ts`) |
| RF12 | CU07 | RN05, RN22, D2 | 07 · Detalhe da conta ↔ D03 | 04 | `api/tests/test_contas.py`: `test_rn22_edicao_registra_autor_e_so_o_que_mudou`, `test_rn22_cancelar_nao_apaga_e_so_aberta`, `test_rn05_contas_por_papel`, `test_rn05_fora_da_saida_observador_403_404`; Vitest `rn22/rn30: automatic actions have no author…` (`contas.test.ts`); E2E `ca12/ca13/ca14 rn22 d2…` (`web/e2e/contas.spec.ts`) |
| RF13 | CU06 | RN02, RN06, RN07, RN12, RN13, D2 | 02 · Início ↔ D02, 03 · Contas ↔ D03 | 04 | `api/tests/test_contas.py`: `test_rf13_filtros_mes_status_casa_pagador_e_contagens`, `test_rf13_resumo_total_do_mes_atencao_e_por_casa`, `test_d2_cancelada_fora_de_tudo_menos_do_filtro_canceladas`, `test_rn02_*`, `test_rn06_*`, `test_rn07_*`, `test_rn12_*`, `test_rn13_*`; Vitest `q9/q12/q23: the hero names its month…` (`inicio.test.tsx`), `d2: list groups by due date…` (`contas.test.ts`), `ca17/ca27…` (`nav.test.tsx`); E2E `ca01/ca16/ca17/ca31…`, `ca15 rf13 q14…` (filtros na URL, Voltar, folha Filtros), `ca30…` (lista + painel `slide-in` / 07 sozinho), `ca27 q4/q5 rn07…` (seletor e cookie), `ca29…` (screenshots) (`web/e2e/contas.spec.ts`) |
| RF14 | CU08 | RN29 | 07 · Detalhe da conta ↔ D03, 13 · Modo simples ↔ D05 | 05 | — |
| RF15 | CU08 | RN14 | 08 · Marcar como paga ↔ M03 | 07 | — |
| RF16 | CU08 | RN15 | 08 · Marcar como paga ↔ M03, 09 · Conta paga ↔ M04 | 07 | — |
| RF17 | CU08 | RN16 | 07 · Detalhe da conta ↔ D03 | 07 | — |
| RF18 | CU09 | RN17, RN23 | 05 · Nova conta ↔ M01, 10 · Grupo ↔ D04 | 08 | — |
| RF19 | CU12 | RN17, RN18, RN23 | — (agendador) | 08 | — |
| RF20 | CU12 | RN18, RN19 | 04 · Avisos ↔ D06 | 09 | — |
| RF21 | CU10 | RN20 | 12 · Pedir para alguém pagar ↔ M06 | 10 | — |
| RF22 | CU11 | RN07, RN14, RN15 | 13 · Modo simples ↔ D05 | 10 | — |
| RF23 | CU05 | RN25 | 05 · Nova conta ↔ M01 | 06 | — |
| RF24 | CU05 | RN26, RN27, RN28 | 06 · Conferir conta ↔ M02 | 06 | — |
| RF25 | CU08, CU11 | RN29 | 07 · Detalhe da conta ↔ D03, 13 · Modo simples ↔ D05 | 06 | — |

RF11 segue a origem rev 47: "Definir espaço, subgrupo, pagador e visibilidade", sem categoria ([ADR 0005](arquitetura/adr/0005-rf11-sem-categoria.md)).

## Requisitos não funcionais

| RNF | Etapa | Testes |
| --- | --- | --- |
| RNF01 | 02 (dados próprios), 03 (filtro central), revisado em toda etapa | `test_rnf01_ca10_dados_proprios_sem_vazamento` (`api/tests/test_autenticacao.py`); E2E de dois usuários e espaços distintos em `auth.spec.ts`. Etapa 03 (filtro central `acesso.py`): `test_rnf01_rn01_fora_do_grupo_recebe_404_em_todas_as_rotas`, `test_rnf01_ids_de_outro_grupo_na_url_do_meu_grupo_404`, `test_rn02_espaco_pessoal_de_outro_nunca_aparece`, `test_rn03_*`, `test_rnf01_basic_auth_nao_autentica` (só sessão no DRF, B1 da revisão) (`api/tests/test_grupos.py`); E2E `ca09/ca11/ca15/ca17 rn01/rn05/rn07 rnf01…` (`web/e2e/grupos.spec.ts`). Etapa 04 (lançamentos só por `acesso.py`, 404 e nunca 403 para quem não vê, agregados sem vazamento): `test_rn01_rnf01_conta_de_outro_grupo_404_e_so_no_proprio_espaco`, `test_rn02_conta_pessoal_so_o_dono_ve`, `test_rn06_admin_nao_escolhido_404_e_agregados_sem_a_conta`, `test_rn32_rn06_remocao_admin_sem_sinal` (`api/tests/test_contas.py`); E2E `ca07/ca08/ca09/ca28 rn06/rn07…`, `ca27 q4/q5 rn07…` (cookie de espaço alheio cai no pessoal; API 404) (`web/e2e/contas.spec.ts`) |
| RNF02 | 02 | `test_rnf02_ca11_*` e `test_rnf02_ca11_google_callback_aberto_e_origem_estranha_bloqueados` (`api/tests/test_autenticacao.py`); Vitest rotação de CSRF/401 confirmado (`web/src/lib/auth/client.test.ts`); E2E `rnf02 ca11…` e fluxo de sessão/saída/Back (`web/e2e/auth.spec.ts`) |
| RNF03 | 06 | — |
| RNF04 | 03 (minimização), 11 (RN30, [ADR 0003](arquitetura/adr/0003-rn30-exportar-e-excluir-dados.md)) | Etapa 03: `test_rnf04_email_de_membros_so_para_admin_ou_sem_nome` (`api/tests/test_grupos.py`). Exportação/exclusão na Etapa 11 |
| RNF05 | 11 | — |
| RNF06 | 02 (e-mail), 06, 09 | `test_rf03_ca07_recuperacao_resposta_generica_email_async` (`api/tests/test_autenticacao.py`): enfileira o link após commit, sem envio síncrono. PDF e notificações de contas nas etapas futuras. |
| RNF07 | 09 | — |
| RNF08 | 01, 02, 11 | E2E `rnf08 ca13: … alvos ≥ 44px em 360px` (vitrine e 5 páginas), `ca05/d1: Button renderizado com 52px…` (`web/e2e/design-system.spec.ts`); `ca13/ca14 rnf08/rnf09…` (`web/e2e/auth.spec.ts`: login/cadastro/recuperação em 360px e screenshots 390×844/1440×900); Vitest `ca05/d1…` (`button.test.tsx`); Etapa 03: E2E `ca20 rnf08/rnf09: 360px…` (grupos, criar, página, convite, gestão, casa e aceite) e `ca19/ca20 rn31 rnf08/rnf09…` (`web/e2e/grupos.spec.ts`); Etapa 04: E2E `ca32 rnf08: 360px…` (Início, Contas, Filtros, formulário, Detalhe, editar) (`web/e2e/contas.spec.ts`) |
| RNF09 | 01, 02, 11 | Vitest `ca08/rnf09…` (`status-badge.test.tsx`), `ca09/rnf09…` (`tokens.test.ts`), `ca02/ca14: API validation is associated with its labelled field and announced` (`auth-form.test.tsx`); E2E `ca13/ca14 rnf08/rnf09…` (`web/e2e/auth.spec.ts`, alvos e movimento reduzido); Etapa 03: Vitest `ca20` (`componentes.test.tsx`: RadioCard rádio nativo, papel em texto); E2E `ca19/ca20 rn31 rnf08/rnf09…` (foco, Esc, setas, movimento reduzido) (`web/e2e/grupos.spec.ts`); Etapa 04: E2E `ca32 rnf09/rnf11…` (status com ícone e texto; movimento reduzido desliga `swing`, `count-up`, `rise`, `slide-in` e `badge-pulse`, com controle), `ca01/ca16/ca17/ca31…` (Esc fecha o formulário e devolve o foco), `ca07/ca08/ca09/ca28…` (aviso em `aria-live`) (`web/e2e/contas.spec.ts`) |
| RNF10 | 09, 11 | — |
| RNF11 | 00 (fuso/UTC), 04 (centavos) | `test_rnf11_hoje_em_fortaleza` (23h30 em Fortaleza = 02h30 UTC do dia seguinte), `test_rn12_*`, `test_rn11_*` (`api/tests/test_contas.py`); Vitest `money: pt-BR input to cents and back` (`contas.test.ts`); E2E `ca32 rnf09/rnf11…` ("Venceu dd/mm" de outro mês, R$ pt-BR) (`web/e2e/contas.spec.ts`) |
| RNF12 | 00, 02 (`make types` + CI) | `test_rnf12_ca15_schema_completo_e_deterministico` (`api/tests/test_autenticacao.py`), `api.yml` job `types`; `make types` compõe schema DRF/allauth validado e gera tipos usados pelo frontend |

## Regras acrescentadas por ADR

| RN | Origem | Tela | Etapa | Testes |
| --- | --- | --- | --- | --- |
| RN30 | RNF04, ADR 0003 | Perfil (ainda não existe no Doop); "Ex-membro" no 07 ↔ D03 | 04 (`SET_NULL` e "Ex-membro"), 11 (exportar/excluir) | Etapa 04: `test_rn30_criador_excluido_ex_membro`, `test_rn30_historico_sem_email_e_ex_membro_apos_exclusao` (histórico só com ids; "Pessoa sem nome"/"Ex-membro", nunca e-mail), `test_rn32_exclusao_usuario_orm_e_queryset_bloqueada` (`api/tests/test_contas.py`); Vitest `rn22/rn30: automatic actions have no author…` (`contas.test.ts`) |
| RN31 | RF05, CU03, RN24, ADR 0004 | 11 · Convidar membro ↔ M05; aceite `/c/[token]` (sem frame) | 03 | `api/tests/test_grupos.py`: `test_rf05_rn24_rn31_link_inteiro_uma_vez_e_banco_so_com_hash`, `test_rn31_log_do_servidor_sem_token`, `test_rn31_admin_django_nao_mostra_token_hash`, `test_rn24_rn31_convite_invalido_mesma_resposta_e_nada_muda` (4 estados), `test_rn24_rn31_dois_aceites_simultaneos_geram_um_membro`, `test_rn31_revogar_convite_pendente`, `test_rn31_revogar_so_vale_para_pendente_usado_da_404_e_membro_fica`, `test_rn31_revogar_e_listar_convites_sem_ser_admin_403`, `test_rn31_limite_aceite_11a_tentativa_429_por_usuario`, `test_rn21_rn31_saida_do_admin_revoga_convites_que_ele_gerou`; Vitest `ca19/rn31…`; E2E `ca01/ca04/ca05/ca17 … rn24/rn31…` (link encurtado na tela, inteiro na cópia, reuso 410) e `ca19/ca20 rn31…` (fechar sem usar revoga) (`web/e2e/grupos.spec.ts`) |
| RN32 | RF06, RF11, RF12, CU03, CU05, CU07, RN06, RN07, RN21, ADR 0006 | 10 · Grupo ↔ D04 (sair; remover sem mudança visível); folha de saída barrada sem frame | 04 (aviso ao removido na 09) | `api/tests/test_contas.py`: `test_rn32_sair_bloqueado_lista_contas_e_nada_muda` (paga, confirmada e cancelada não bloqueiam), `test_rn32_sair_pagador_quando_o_criador_ja_saiu`, `test_rn32_exclusao_usuario_orm_e_queryset_bloqueada`, `test_rn32_exclusao_usuario_admin_django`, `test_rn32_concorrencia_os_dois_unicos_que_veem_saem_juntos` (threads), `test_rn32_concorrencia_editar_e_sair` (sair e remover × edição, threads), `test_rn32_concorrencia_excluir_conta_e_remocao_admin` (threads), `test_rn32_remocao_admin_cancela_orfa`, `test_rn32_remocao_admin_concorrencia_cancela_uma_vez` (threads), `test_rn32_rn06_remocao_admin_sem_sinal` (status, cabeçalhos, corpo, tempo e agregados), `test_rn32_editar_sem_quem_veja_400` (tirar-se de "Quem vê" e o pagador tirar-se de pagador), `test_rn32_admin_removendo_a_si_mesmo_e_saida_voluntaria`; Vitest `ca22/rn32…` (`grupo-pagina.test.tsx`), `q19b…` (`conta-folha.test.tsx`); E2E `ca19/ca22/ca23 rn32 adr0007…`, `ca20/ca21/ca22 rn32/rn06…` (`web/e2e/contas.spec.ts`) |
| RN05 (exceção) | RF06, CU03, RN32, ADR 0007 | folha de saída barrada (sem frame) | 04 | `api/tests/test_contas.py`: `test_rn05_rn32_excecao_so_na_saida` (observador; 400 para conta que não bloqueia, 409 sem mudar nada se sobra órfã), `test_rn05_rn32_pagador_resolve_na_saida` (papel pagador), `test_rn05_fora_da_saida_observador_403_404`; E2E `ca19/ca22/ca23 rn32 adr0007…` (`web/e2e/contas.spec.ts`) |
| RN06 × RN07 | RF06, RF11, RF13, CU03, CU06, ADR 0008 | 10 · Grupo ↔ D04 (alterar papel), 03 · Contas ↔ D03 | 04 | `api/tests/test_contas.py`: `test_rn06_rn07_acesso_explicito_prevalece`, `test_rn06_rn07_alterar_papel_preserva_acesso` (mesma resposta ao admin, admin segue com 404); E2E `ca07/ca08/ca09/ca28 rn06/rn07…` (`web/e2e/contas.spec.ts`) |

## Regras de negócio da Etapa 03

| RN | Testes |
| --- | --- |
| RN01 | `test_rnf01_rn01_fora_do_grupo_recebe_404_em_todas_as_rotas`, `test_rnf01_ids_de_outro_grupo_na_url_do_meu_grupo_404` (`api/tests/test_grupos.py`); E2E `ca09/ca11/ca15/ca17 rn01/rn05/rn07 rnf01…` (`web/e2e/grupos.spec.ts`) |
| RN02 | `test_rn02_espaco_pessoal_de_outro_nunca_aparece`, `test_rn05_tabela_papel_acao[dono-*]` (`api/tests/test_grupos.py`) |
| RN03 | `test_rn03_espaco_pessoal_recusa_convite_pela_api`, `test_rn03_servico_recusa_convite_e_aceite_no_pessoal` (`api/tests/test_grupos.py`) |
| RN04 | `test_rf04_rn04_*`, `test_rn04_*` (rebaixar/remover/sair, concorrência com threads, exclusão de `Usuario` por ORM, queryset e admin do Django) (`api/tests/test_grupos.py`); E2E `ca12/ca14 rf06 rn04/rn21…` (`web/e2e/grupos.spec.ts`) |
| RN05 / RN07 | `test_rn05_tabela_papel_acao` (5 papéis × 6 ações), `test_rn05_gestao_negada_a_quem_nao_e_admin` (3 papéis × 8 ações), `test_rn05_admin_gerencia`, `test_rn05_rn07_detalhe_grupo_por_papel` (`api/tests/test_grupos.py`); Vitest `ca11` (`grupo-pagina.test.tsx`), `ca17` (`nav.test.tsx`); E2E `ca09/ca11/ca15/ca17 rn01/rn05/rn07 rnf01…` (`web/e2e/grupos.spec.ts`) |
| RN21 | `test_rn21_removido_e_quem_sai_perde_acesso_na_hora`, `test_rn21_rn31_saida_do_admin_revoga_convites_que_ele_gerou` (`api/tests/test_grupos.py`); E2E `ca12/ca14 rf06 rn04/rn21…` (`web/e2e/grupos.spec.ts`). Efeito nas contas na Etapa 04; aviso na 09 |
| RN24 | `test_rn24_rn31_convite_invalido_mesma_resposta_e_nada_muda`, `test_rn24_rn31_dois_aceites_simultaneos_geram_um_membro`, `test_rf05_rn24_rn31_link_inteiro_uma_vez_e_banco_so_com_hash` (`api/tests/test_grupos.py`); E2E `ca01/ca04/ca05/ca17 … rn24/rn31…` (`web/e2e/grupos.spec.ts`) |
| RN31 | Ver a tabela "Regras acrescentadas por ADR" |

Casos de uso: CU02 = RF04; CU03 = RF05 e RF06; CU04 = RF07 (testes nas linhas acima).

## Regras de negócio da Etapa 04

| RN | Testes |
| --- | --- |
| RN01 / RNF01 | `test_rn01_rnf01_conta_de_outro_grupo_404_e_so_no_proprio_espaco`, `test_rn01_rf11_editar_com_dados_de_outro_grupo_400_e_nada_grava` (`api/tests/test_contas.py`) |
| RN02 | `test_rn02_conta_pessoal_so_o_dono_ve` (`api/tests/test_contas.py`); E2E `ca12/ca13/ca14…`, `ca27…` (espaço pessoal) (`web/e2e/contas.spec.ts`) |
| RN05 | `test_rn05_contas_por_papel` (dono e 4 papéis), `test_rn05_fora_da_saida_observador_403_404` (`api/tests/test_contas.py`); E2E `ca07/ca08/ca09/ca28…` (pagador abre o detalhe sem Editar), `ca11 rn13 q10…` (Configurações só admin) (`web/e2e/contas.spec.ts`) |
| RN06 | `test_rn06_admin_nao_escolhido_404_e_agregados_sem_a_conta` (admin, membro e observador não escolhidos; lista, filtros, contagens, resumo, "Por casa", detalhe de outra conta; 404 em GET/PATCH/cancelar), `test_rn06_pagador_nao_escolhido_ve_a_conta` (membro e pagador), `test_rn32_rn06_remocao_admin_sem_sinal` (`api/tests/test_contas.py`); E2E `ca07/ca08/ca09/ca28 rn06/rn07…` (API e tela: hero, "Por casa", HouseCard, chips, "Conta não encontrada") (`web/e2e/contas.spec.ts`) |
| RN07 | `test_rn07_pagador_so_ve_as_contas_dele`, `test_rn06_rn07_*` (`api/tests/test_contas.py`); E2E `ca07/ca08/ca09/ca28…` e `ca27 q4/q5 rn07…` (`/grupos/<id>/simples` só com as contas do pagador) (`web/e2e/contas.spec.ts`) |
| RN11 | `test_rn11_valor_invalido_400_e_nada_grava` (0, −1, decimal, texto, nulo, booleano, 2³¹; criar e editar), `test_rn11_banco_recusa_valor_nao_positivo` (`api/tests/test_contas.py`); E2E `ca01/ca16/ca17/ca31…` (valor vazio barrado no formulário) (`web/e2e/contas.spec.ts`) |
| RN12 | `test_rn12_status_calculado_com_janela_3` (4 datas), `test_rn12_so_pendente_vira_vence_ou_vencida`, `test_rnf11_hoje_em_fortaleza` (`api/tests/test_contas.py`) |
| RN13 | `test_rn13_janela_editavel_so_pelo_admin` (1–7, 0/8/texto/nulo 400, outros papéis 403, pessoal 404 e fica em 3, banco recusa 8), `test_rn13_migracao_janela_fora_do_intervalo_e_ajustada_sem_perda` (`api/tests/test_contas.py`); Vitest `q10/rn13…` (`grupo-pagina.test.tsx`); E2E `ca11 rn13 q10…` (`web/e2e/contas.spec.ts`) |
| RN21 | `test_rn21_abertas_perdem_pagador_pagas_mantem_e_criadas_ficam` (sair e remover; histórico automático sem autor; sai de "Quem vê"), `test_rn05_rn32_pagador_resolve_na_saida` (cancelada guarda o pagador, Q7) (`api/tests/test_contas.py`) |
| RN22 | `test_rn22_edicao_registra_autor_e_so_o_que_mudou`, `test_rn22_cancelar_nao_apaga_e_so_aberta` (`api/tests/test_contas.py`); E2E `ca12/ca13/ca14 rn22 d2…` (`web/e2e/contas.spec.ts`) |
| D2 | `test_d2_cancelada_fora_de_tudo_menos_do_filtro_canceladas` (`api/tests/test_contas.py`); Vitest `d2: list groups by due date…` (`contas.test.ts`); E2E `ca12/ca13/ca14 rn22 d2…` (fora do Início e de "Todas"; em "Canceladas" riscada e opaca) (`web/e2e/contas.spec.ts`) |
| ADR 0005 (sem categoria) | `test_rf10_criar_conta_nasce_pendente_com_historico`, `test_rf11_casa_pagador_e_escolhidos_validados` (`categoria` ignorada e ausente da resposta) (`api/tests/test_contas.py`) |
| ADR 0006 / 0007 / 0008 | Ver a tabela "Regras acrescentadas por ADR" (RN32, RN05 exceção, RN06 × RN07) |

Casos de uso: CU05 = RF10 e RF11 (só o manual); CU06 = RF13; CU07 = RF12 (testes nas linhas acima).

### Decisões da revisão da Etapa 04 (23, 26–30)

| Decisão | Testes |
| --- | --- |
| 23 · nome por contexto (RN30) | `test_rn30_nome_por_contexto_membro_sem_nome_ex_membro`, `test_rn30_historico_sem_email_ex_membro_apos_saida_ou_exclusao`, `test_rn30_criador_excluido_ex_membro` (`api/tests/test_contas.py`); Vitest `rn22/rn30: automatic actions have no author, a deleted author reads Ex-membro` (`contas.test.ts`); E2E `dec23 rn30: quem saiu do grupo aparece como Ex-membro em Criada por…` (o e-mail não aparece em lugar nenhum do DOM) e `ca19/ca22/ca23 rn32 adr0007…` (membro atual sem nome aparece pelo e-mail) (`web/e2e/contas.spec.ts`) |
| 26 · "Precisa de atenção" com `aguardando` (RN13) | `test_rn13_atencao_inclui_aguardando_na_janela` (`api/tests/test_contas.py`). Sem E2E: a API ainda não cria contas `aguardando` |
| 27 · hero do D02 sem vazio | E2E `dec27: no desktop o hero do Início tem a altura do conteúdo…` (só desktop) (`web/e2e/contas.spec.ts`) |
| 28 · `/contas/[id]` sem TabBar abaixo de 1024px | Vitest `ajuste 28: the bill detail (07) is a stacked screen without TabBar…` (`app-shell.test.tsx`); E2E `dec28: abaixo de 1024px /contas/[id] não tem TabBar e tem TopBar com voltar; no desktop o D03 segue…` e `ca29…` (formulário aberto a partir do Início) (`web/e2e/contas.spec.ts`) |
| 29 · nomes e e-mails em uma linha | Vitest `ajuste 29: …` (3 em `nome.test.tsx`, 1 em `contas.test.ts`); E2E `dec29: e-mail longo sem nome fica em uma linha no BillCard, em Quem paga e na MemberRow…` (altura de uma linha, `scrollWidth > clientWidth`, `title` inteiro; 360px sem rolagem no mobile) (`web/e2e/contas.spec.ts`) |
| 30 · espaço atual primeiro em "Onde fica" | Vitest `ajuste 30: …` (pessoal, grupo, observador; `conta-folha.test.tsx`); E2E `dec30: Nova conta abre com o espaço atual primeiro e selecionado…` (dois grupos e o pessoal) (`web/e2e/contas.spec.ts`) |
| 31 · 404 uniforme (RN06/RNF01) | `test_rn06_rnf01_404_mesmas_consultas_inexistente_e_invisivel` (com e sem trava; `api/tests/test_contas.py`); compara consultas, sem afirmar tempo constante |
| 33 · privacidade no admin (RN02/RN06) | `test_rn02_rn06_admin_django_filtra_contas_historicos_e_links`, `test_rn02_rn06_admin_django_exclusao_sem_previa_contas_pessoais` (`api/tests/test_contas.py`) |
| 35 · vencidas abertas por data (ADR 0009) | `test_rn12_rf13_vencidas_abertas_por_data_sem_mudar_selo` (`api/tests/test_contas.py`): contagens, filtro e selo preservado |
| 36/38 · pessoas relacionadas e Quem vê efetivo (RN06/RN30) | `test_rn06_quem_ve_inclui_criador_pagador_escolhidos_sem_duplicar`, `test_rn06_rn30_pagador_nome_email_so_de_quem_ve_conta_e_candidatos_saida` (`api/tests/test_contas.py`); Vitest `ajuste 29: detail Quem paga, Quem vê, Criada por and history keep a long…` (`nome.test.tsx`); E2E `dec38 rn06…` (`web/e2e/contas.spec.ts`) |
| 39 · nomes de espaços (RN01) | E2E `dec39 rn01…` (`web/e2e/contas.spec.ts`): prefixos iguais, identificação completa e gravação no espaço escolhido |

| Critério da revisão | Testes de concorrência (`api/tests/test_contas.py`) |
| --- | --- |
| CA35 · criação × desligamento | `test_rn01_rn05_criar_revalida_vinculo_apos_autorizacao`, `test_rn01_rn21_rn32_criacao_serializa_vinculos_com_desligamento` (criador, pagador e escolhido × saída, remoção e exclusão) |
| CA36 · grupo → restrita × desligamento | `test_rn32_concorrencia_grupo_para_restrita_e_saida` (saída e remoção) |
| CA37 · detalhe e resposta de edição consistentes | `test_rn06_detalhe_revalida_acesso_na_consulta_que_carrega_dados`, `test_rn06_detalhe_mantem_snapshot_ate_prefetch_e_historico`, `test_rn06_detalhe_espera_edicao_e_rele_acesso_em_snapshot_novo`, `test_rn06_resposta_propria_edicao_nao_le_edicao_alheia_posterior` |

## Rastreabilidade da Etapa 05

| Critérios / regras | Testes |
| --- | --- |
| CA01–03, RN08–RN10 · boleto, arrecadação e ciclos | `test_rn08_bancario_formatado_e_mutacoes`, `test_rn10_arrecadacao_referencias`, `test_febraban_official_modulo_examples`, `test_rn09_fator_ciclos`, `test_rn09_fator_ausente_e_legado` (`api/tests/test_boletos_parser.py`); `test_rn09_salvar_fator_ambiguo_somente_datas_codificadas` (`api/tests/test_boletos_api.py`); E2E `rf08/rn09/rf14…` (`web/e2e/boletos.spec.ts`) |
| CA04–07, RF09 · rejeição, Pix, rede e chave | `test_rn08_codigo_invalido`, `test_rf09_bcb_vetores_oficiais`, `test_rf09_valor_utf8_e_tlv_adversario`, `test_rf09_dinamico_ignora_valor_sem_acesso_rede`, `test_rf09_chave_pix`, `test_rf09_chave_invalida`, testes de TLV, chave canônica, valor e URL (`api/tests/test_boletos_parser.py`); `test_rf09_pix_estatico_valor_codificado_e_dinamico_ignorado`, `test_rf09_rn10_preview_campos_ausentes_permanecem_ausentes` (`api/tests/test_boletos_api.py`); Vitest `rn08…`, `rf09…` (`instrumento.test.tsx`); E2E `rf09/rf14/rn22…` |
| CA08–10, RN01/RN02/RN05/RN06/RN09/RN11/RN22 · revalidação, permissão e histórico | `test_rn09_rn11_save_revalida_400_sem_gravacao_parcial`, `test_rn09_patch_instrumento_ausente_ainda_valida_valor_data`, `test_rn01_rn02_rn06_instrumento_herda_404_conta`, `test_rn05_instrumento_so_edita_quem_pode_editar_conta`, `test_rn22_editar_trocar_remover_preservar_e_noop_sem_payload_historico`, `test_rn06_detalhe_nao_entrega_instrumento_novo_apos_revogar_acesso` (`api/tests/test_boletos_api.py`) |
| CA11 · manual legado | `test_rf10_manual_legada_sem_instrumento_e_null_noop` (`api/tests/test_boletos_api.py`), regressões de contas da Etapa 04 |
| CA12–13, RF14 · cópia e interface responsiva | Vitest `rf14: copying preserves…`, `rf14: denied clipboard…` (`copiar-codigo.test.tsx`); E2E `rf08/rn09/rf14…`, `rf09/rf14/rn22…` (`web/e2e/boletos.spec.ts`): cópia, alternativa, dados, teclado, entrada longa e dimensões nas duas resoluções |
| CA14, RNF01/RNF11/RNF12 · verificações e privacidade | `test_rnf01_preview_exige_csrf_da_sessao`, `test_rnf01_m5_instrumento_sem_admin_ou_exposicao_em_cascata`, `test_rf09_campos_textuais_rejeitam_nul_no_preview_e_save` (`api/tests/test_boletos_api.py`); suítes e determinismo registrados no relatório |
| Integridade durante edição e gravação | Vitest `rn22: pending %s cannot reset or send twice…` (criação e edição) e `rf08/rn22: a remote instrument refetch cannot replace the preview of a dirty local entry` (`instrumento.test.tsx`) |

Validação final em 16/11/2026: `make test` passou (354 pytest e 83 Vitest), `make lint` passou, duas execuções de `make types` preservaram os hashes e `make e2e` passou (91 Playwright, 3 ignorados por projeto). O teste de fator inclui aviso de data em formato brasileiro; capturas foram comparadas com os frames da etapa.

## Validação da Etapa 04

Revisão final em 16/11/2026: `make test` passou (235 pytest e 73 Vitest), `make lint` passou, `make types` preservou os hashes do schema e dos tipos, e `make e2e` passou (87 Playwright, 3 ignorados por projeto). Uma execução anterior teve dois timeouts de 45 s no cenário ca07; o limite específico foi ampliado para 75 s pela duração do fluxo de quatro usuários e três contextos, preservando as asserções. As capturas e a comparação visual foram registradas no relatório da etapa.

Em 15/11/2026 (QA): `make test` passou (199 pytest, 65 Vitest; 204 pytest após as correções de segurança em f072ce5), `make lint` passou, `make types` regenerou sem diff e `make e2e` passou (74 Playwright e 2 ignorados de propósito: os testes de 360px rodam só no projeto mobile), sem nenhum 429. Uma execução anterior teve um 429 isolado no primeiro cadastro logo após o `make e2e` recriar a API (trava de cache do allauth com espera de 1 s em partida a frio); a reexecução completa passou. `web/e2e/contas.spec.ts` (12 testes × 2 resoluções) usa API e PostgreSQL reais, com usuários, grupos e contas criados pelo próprio teste. QA corrigiu: rolagem horizontal da vitrine em 360px (coluna do BillCard) e Chip com nome longo (e-mail de quem não tem nome) saindo da folha/modal (reticências). Screenshots em `web/e2e/__screens__/` (`inicio-*`, `contas-*`, `conta-detalhe-*`, `conta-form-*`, além de `grupo-*`); a comparação com 02/D02, 03/D03, 07 e 05/M01/06/M02 vai no relatório.

Em 15/11/2026, após as decisões 23 e 26–30 (4c9a1b2, 3d4ba32), QA com Node 22 e a API fria: `make test` passou (207 pytest, 73 Vitest), `make lint` passou, `make types` sem diff e `make e2e` passou (83 Playwright, 3 ignorados de propósito: os de 360px e o `dec27`, só desktop). Entraram 5 E2E `dec23`/`dec27`–`dec30` (tabela acima); `ca29` abre o formulário a partir do Início (o 07 empilhado não tem FAB) e `ca19/ca22/ca23` escolhe o admin sem nome pelo e-mail (decisão 23). O Vitest `ca28` estourava o `findBy` de 1 s sob carga (3 de 3 rodadas paralelas): a espera pelo grupo em `conta-folha.test.tsx` passou a 5 s, com justificativa no arquivo.

## Validação da Etapa 03

Em 14/11/2026 (QA): `make test` passou (138 pytest, 57 Vitest), `make lint` passou, `make types` regenerou sem diff e `make e2e` passou (51 Playwright e 1 ignorado de propósito: o teste de 360px roda só no projeto mobile). Em 15/11/2026, após a correção de segurança (c305f27): 143 pytest (+5 casos de 3 testes) e 57 Vitest, lint verde, tipos regenerados e sincronizados. Uma execução do E2E logo após outra suíte teve 3 falhas pelo limite de cadastro do allauth; a reexecução passou 51/51 (P5). `web/e2e/grupos.spec.ts` usa API e PostgreSQL reais, com usuários e grupos criados pelo próprio teste. Screenshots em `web/e2e/__screens__/` (`grupos-*`, `grupo-*`, `convite-*`, `convite-aceite-*`); a comparação com 10/D04 e 11/M05 vai no relatório.

## Fundação (Etapa 00)

| Item | Testes |
| --- | --- |
| Healthcheck `/api/health/` | `api/tests/test_fundacao.py::test_health_ok` (a linha do healthcheck saiu do Início na Etapa 04, com o `page.test.tsx`) |
| OpenAPI servido | `api/tests/test_fundacao.py::test_schema_documents_health` |
| Celery configurado | `api/tests/test_fundacao.py::test_celery_ping_task` |

## Validação da Etapa 02

Em 13/11/2026: `make test` passou (31 pytest, 39 Vitest), `make lint` passou e `make e2e` passou (38 Playwright, nos projetos mobile e desktop). No build final, passaram os testes de HTTP 404 real da vitrine com sessão (2 Playwright, `web/e2e/production.spec.ts`) e de sessão/saída/Back (2 Playwright). A regressão da vitrine em desenvolvimento passou (12 testes focados: guarda, fontes, layout, alvos, navegação e capturas). Os logs de produção ficaram sem erros de hidratação ou validação `instant`. A configuração `web/playwright.production.config.ts` reutiliza apenas o servidor de produção já iniciado, sem iniciar `next dev`; seu teste falhou com HTTP 200 antes da correção e passou com HTTP 404 depois.

As integrações de cadastro, sessão, recuperação pública, CSRF e isolamento usam API/PostgreSQL reais; somente o cenário de apresentação “Google indisponível” controla a resposta de configuração. Os testes de Google no backend usam respostas externas controladas. O início real do OAuth foi conferido até a página do Google “Sign in to continue to Varal”, sem concluir autenticação externa. A comparação visual com o Doop é registrada no relatório da etapa.

Após a correção da inicialização dos formulários, o fluxo central passou novamente nas duas resoluções (2 testes), verificando controles desabilitados no HTML SSR, habilitação após hidratar e navegação Voltar/saída/login sem perder campos. A recuperação válida foi conferida também no navegador de produção com conta descartável, incluindo confirmação estável após consumo do token e login com a nova senha. O teste Vitest `ca08: a consumed recovery key keeps the successful password-change message` cobre essa confirmação.
