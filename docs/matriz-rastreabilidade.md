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
| RF06 | CU03 | RN04, RN05, RN21, RN32 (04) | 10 · Grupo ↔ D04 | 03; RN21 nas contas e RN32 na 04 | `api/tests/test_grupos.py`: `test_rn04_ultimo_admin_nao_se_rebaixa_remove_nem_sai`, `test_rn04_com_outro_admin_pode_rebaixar_e_sair`, `test_rn04_concorrencia_dois_admins_sobra_um` (3 casos), `test_rn04_exclusao_usuario_ultimo_admin_orm_e_queryset`, `test_rn04_exclusao_usuario_ultimo_admin_admin_django`, `test_rn21_removido_e_quem_sai_perde_acesso_na_hora`, `test_rn21_rn31_saida_do_admin_revoga_convites_que_ele_gerou` (3 casos), `test_rn05_gestao_negada_a_quem_nao_e_admin`, `test_rn05_admin_gerencia`; Vitest `ca14/ca15` (`grupo-pagina.test.tsx`); E2E `ca12/ca14 rf06 rn04/rn21…` (`web/e2e/grupos.spec.ts`) |
| RF07 | CU04 | — | 10 · Grupo ↔ D04 | 03 | `api/tests/test_grupos.py`: `test_rf07_criar_renomear_arquivar_casa`, `test_rn05_gestao_negada_a_quem_nao_e_admin` (casos `criar_casa`, `renomear_casa`, `arquivar_casa`); Vitest `ca18: a house with no bills has no progress bar`; E2E `ca01/ca04/ca05/ca17 rf04/rf05/rf07…` (+ Nova casa) e `ca20 rnf08/rnf09: 360px…` (editar casa) (`web/e2e/grupos.spec.ts`) |
| RF08 | CU05 | RN08, RN09, RN10, RN11 | 05 · Nova conta ↔ M01, 06 · Conferir conta ↔ M02 | 05 | — |
| RF09 | CU05 | RN11 | 05 · Nova conta ↔ M01, 06 · Conferir conta ↔ M02 | 05 | — |
| RF10 | CU05 | RN11 | 05 · Nova conta ↔ M01, 06 · Conferir conta ↔ M02 | 04 | — |
| RF11 | CU05 | RN01, RN06, RN07, RN32 | 06 · Conferir conta ↔ M02 (sem frame: "Quem vê" e o aviso "Quem paga também vê esta conta") | 04 | — |
| RF12 | CU07 | RN22 | 07 · Detalhe da conta ↔ D03 | 04 | — |
| RF13 | CU06 | RN02, RN06, RN07, RN12, RN13 | 02 · Início ↔ D02, 03 · Contas ↔ D03 | 04 | — |
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
| RNF01 | 02 (dados próprios), 03 (filtro central), revisado em toda etapa | `test_rnf01_ca10_dados_proprios_sem_vazamento` (`api/tests/test_autenticacao.py`); E2E de dois usuários e espaços distintos em `auth.spec.ts`. Etapa 03 (filtro central `acesso.py`): `test_rnf01_rn01_fora_do_grupo_recebe_404_em_todas_as_rotas`, `test_rnf01_ids_de_outro_grupo_na_url_do_meu_grupo_404`, `test_rn02_espaco_pessoal_de_outro_nunca_aparece`, `test_rn03_*`, `test_rnf01_basic_auth_nao_autentica` (só sessão no DRF, B1 da revisão) (`api/tests/test_grupos.py`); E2E `ca09/ca11/ca15/ca17 rn01/rn05/rn07 rnf01…` (`web/e2e/grupos.spec.ts`). Filtro de lançamentos na Etapa 04. |
| RNF02 | 02 | `test_rnf02_ca11_*` e `test_rnf02_ca11_google_callback_aberto_e_origem_estranha_bloqueados` (`api/tests/test_autenticacao.py`); Vitest rotação de CSRF/401 confirmado (`web/src/lib/auth/client.test.ts`); E2E `rnf02 ca11…` e fluxo de sessão/saída/Back (`web/e2e/auth.spec.ts`) |
| RNF03 | 06 | — |
| RNF04 | 03 (minimização), 11 (RN30, [ADR 0003](arquitetura/adr/0003-rn30-exportar-e-excluir-dados.md)) | Etapa 03: `test_rnf04_email_de_membros_so_para_admin_ou_sem_nome` (`api/tests/test_grupos.py`). Exportação/exclusão na Etapa 11 |
| RNF05 | 11 | — |
| RNF06 | 02 (e-mail), 06, 09 | `test_rf03_ca07_recuperacao_resposta_generica_email_async` (`api/tests/test_autenticacao.py`): enfileira o link após commit, sem envio síncrono. PDF e notificações de contas nas etapas futuras. |
| RNF07 | 09 | — |
| RNF08 | 01, 02, 11 | E2E `rnf08 ca13: … alvos ≥ 44px em 360px` (vitrine e 5 páginas), `ca05/d1: Button renderizado com 52px…` (`web/e2e/design-system.spec.ts`); `ca13/ca14 rnf08/rnf09…` (`web/e2e/auth.spec.ts`: login/cadastro/recuperação em 360px e screenshots 390×844/1440×900); Vitest `ca05/d1…` (`button.test.tsx`); Etapa 03: E2E `ca20 rnf08/rnf09: 360px…` (grupos, criar, página, convite, gestão, casa e aceite) e `ca19/ca20 rn31 rnf08/rnf09…` (`web/e2e/grupos.spec.ts`) |
| RNF09 | 01, 02, 11 | Vitest `ca08/rnf09…` (`status-badge.test.tsx`), `ca09/rnf09…` (`tokens.test.ts`), `ca02/ca14: API validation is associated with its labelled field and announced` (`auth-form.test.tsx`); E2E `ca13/ca14 rnf08/rnf09…` (`web/e2e/auth.spec.ts`, alvos e movimento reduzido); Etapa 03: Vitest `ca20` (`componentes.test.tsx`: RadioCard rádio nativo, papel em texto); E2E `ca19/ca20 rn31 rnf08/rnf09…` (foco, Esc, setas, movimento reduzido) (`web/e2e/grupos.spec.ts`) |
| RNF10 | 09, 11 | — |
| RNF11 | 00 (fuso/UTC), 04 (centavos) | — |
| RNF12 | 00, 02 (`make types` + CI) | `test_rnf12_ca15_schema_completo_e_deterministico` (`api/tests/test_autenticacao.py`), `api.yml` job `types`; `make types` compõe schema DRF/allauth validado e gera tipos usados pelo frontend |

## Regras acrescentadas por ADR

| RN | Origem | Tela | Etapa | Testes |
| --- | --- | --- | --- | --- |
| RN30 | RNF04, ADR 0003 | Perfil (ainda não existe no Doop) | 11 | — |
| RN31 | RF05, CU03, RN24, ADR 0004 | 11 · Convidar membro ↔ M05; aceite `/c/[token]` (sem frame) | 03 | `api/tests/test_grupos.py`: `test_rf05_rn24_rn31_link_inteiro_uma_vez_e_banco_so_com_hash`, `test_rn31_log_do_servidor_sem_token`, `test_rn31_admin_django_nao_mostra_token_hash`, `test_rn24_rn31_convite_invalido_mesma_resposta_e_nada_muda` (4 estados), `test_rn24_rn31_dois_aceites_simultaneos_geram_um_membro`, `test_rn31_revogar_convite_pendente`, `test_rn31_revogar_so_vale_para_pendente_usado_da_404_e_membro_fica`, `test_rn31_revogar_e_listar_convites_sem_ser_admin_403`, `test_rn31_limite_aceite_11a_tentativa_429_por_usuario`, `test_rn21_rn31_saida_do_admin_revoga_convites_que_ele_gerou`; Vitest `ca19/rn31…`; E2E `ca01/ca04/ca05/ca17 … rn24/rn31…` (link encurtado na tela, inteiro na cópia, reuso 410) e `ca19/ca20 rn31…` (fechar sem usar revoga) (`web/e2e/grupos.spec.ts`) |
| RN32 | RF06, RF11, CU03, CU05, RN06, RN07, RN21, ADR 0006 | 10 · Grupo ↔ D04 (sair/remover); mensagem do 409 sem frame | 04 | — |

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

## Validação da Etapa 03

Em 14/11/2026 (QA): `make test` passou (138 pytest, 57 Vitest), `make lint` passou, `make types` regenerou sem diff e `make e2e` passou (51 Playwright e 1 ignorado de propósito: o teste de 360px roda só no projeto mobile). Em 15/11/2026, após a correção de segurança (c305f27): 143 pytest (+5 casos de 3 testes) e 57 Vitest, lint verde, tipos regenerados e sincronizados. Uma execução do E2E logo após outra suíte teve 3 falhas pelo limite de cadastro do allauth; a reexecução passou 51/51 (P5). `web/e2e/grupos.spec.ts` usa API e PostgreSQL reais, com usuários e grupos criados pelo próprio teste. Screenshots em `web/e2e/__screens__/` (`grupos-*`, `grupo-*`, `convite-*`, `convite-aceite-*`); a comparação com 10/D04 e 11/M05 vai no relatório.

## Fundação (Etapa 00)

| Item | Testes |
| --- | --- |
| Healthcheck `/api/health/` | `api/tests/test_fundacao.py::test_health_ok`, `web/src/app/(app)/page.test.tsx` |
| OpenAPI servido | `api/tests/test_fundacao.py::test_schema_documents_health` |
| Celery configurado | `api/tests/test_fundacao.py::test_celery_ping_task` |

## Validação da Etapa 02

Em 13/11/2026: `make test` passou (31 pytest, 39 Vitest), `make lint` passou e `make e2e` passou (38 Playwright, nos projetos mobile e desktop). No build final, passaram os testes de HTTP 404 real da vitrine com sessão (2 Playwright, `web/e2e/production.spec.ts`) e de sessão/saída/Back (2 Playwright). A regressão da vitrine em desenvolvimento passou (12 testes focados: guarda, fontes, layout, alvos, navegação e capturas). Os logs de produção ficaram sem erros de hidratação ou validação `instant`. A configuração `web/playwright.production.config.ts` reutiliza apenas o servidor de produção já iniciado, sem iniciar `next dev`; seu teste falhou com HTTP 200 antes da correção e passou com HTTP 404 depois.

As integrações de cadastro, sessão, recuperação pública, CSRF e isolamento usam API/PostgreSQL reais; somente o cenário de apresentação “Google indisponível” controla a resposta de configuração. Os testes de Google no backend usam respostas externas controladas. O início real do OAuth foi conferido até a página do Google “Sign in to continue to Varal”, sem concluir autenticação externa. A comparação visual com o Doop é registrada no relatório da etapa.

Após a correção da inicialização dos formulários, o fluxo central passou novamente nas duas resoluções (2 testes), verificando controles desabilitados no HTML SSR, habilitação após hidratar e navegação Voltar/saída/login sem perder campos. A recuperação válida foi conferida também no navegador de produção com conta descartável, incluindo confirmação estável após consumo do token e login com a nova senha. O teste Vitest `ca08: a consumed recovery key keeps the successful password-change message` cobre essa confirmação.
