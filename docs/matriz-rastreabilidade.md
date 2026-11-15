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
| RF04 | CU02 | RN04 | 10 · Grupo ↔ D04 | 03 | — |
| RF05 | CU03 | RN05, RN24 | 11 · Convidar membro ↔ M05 | 03 | — |
| RF06 | CU03 | RN04, RN05, RN21 | 10 · Grupo ↔ D04 | 03 | — |
| RF07 | CU04 | — | 10 · Grupo ↔ D04 | 03 | — |
| RF08 | CU05 | RN08, RN09, RN10, RN11 | 05 · Nova conta ↔ M01, 06 · Conferir conta ↔ M02 | 05 | — |
| RF09 | CU05 | RN11 | 05 · Nova conta ↔ M01, 06 · Conferir conta ↔ M02 | 05 | — |
| RF10 | CU05 | RN11 | 05 · Nova conta ↔ M01, 06 · Conferir conta ↔ M02 | 04 | — |
| RF11 | CU05 | RN01, RN06 | 06 · Conferir conta ↔ M02 | 04 | — |
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

## Requisitos não funcionais

| RNF | Etapa | Testes |
| --- | --- | --- |
| RNF01 | 02 (dados próprios), 03 (filtro central), revisado em toda etapa | `test_rnf01_ca10_dados_proprios_sem_vazamento` (`api/tests/test_autenticacao.py`); E2E de dois usuários e espaços distintos em `auth.spec.ts`. Filtro de lançamentos/grupos permanece na Etapa 03. |
| RNF02 | 02 | `test_rnf02_ca11_*` e `test_rnf02_ca11_google_callback_aberto_e_origem_estranha_bloqueados` (`api/tests/test_autenticacao.py`); Vitest rotação de CSRF/401 confirmado (`web/src/lib/auth/client.test.ts`); E2E `rnf02 ca11…` e fluxo de sessão/saída/Back (`web/e2e/auth.spec.ts`) |
| RNF03 | 06 | — |
| RNF04 | 11 (RN30, [ADR 0003](arquitetura/adr/0003-rn30-exportar-e-excluir-dados.md)) | — |
| RNF05 | 11 | — |
| RNF06 | 02 (e-mail), 06, 09 | `test_rf03_ca07_recuperacao_resposta_generica_email_async` (`api/tests/test_autenticacao.py`): enfileira o link após commit, sem envio síncrono. PDF e notificações de contas nas etapas futuras. |
| RNF07 | 09 | — |
| RNF08 | 01, 02, 11 | E2E `rnf08 ca13: … alvos ≥ 44px em 360px` (vitrine e 5 páginas), `ca05/d1: Button renderizado com 52px…` (`web/e2e/design-system.spec.ts`); `ca13/ca14 rnf08/rnf09…` (`web/e2e/auth.spec.ts`: login/cadastro/recuperação em 360px e screenshots 390×844/1440×900); Vitest `ca05/d1…` (`button.test.tsx`) |
| RNF09 | 01, 02, 11 | Vitest `ca08/rnf09…` (`status-badge.test.tsx`), `ca09/rnf09…` (`tokens.test.ts`), `ca02/ca14: API validation is associated with its labelled field and announced` (`auth-form.test.tsx`); E2E `ca13/ca14 rnf08/rnf09…` (`web/e2e/auth.spec.ts`, alvos e movimento reduzido) |
| RNF10 | 09, 11 | — |
| RNF11 | 00 (fuso/UTC), 04 (centavos) | — |
| RNF12 | 00, 02 (`make types` + CI) | `test_rnf12_ca15_schema_completo_e_deterministico` (`api/tests/test_autenticacao.py`), `api.yml` job `types`; `make types` compõe schema DRF/allauth validado e gera tipos usados pelo frontend |

## Regras acrescentadas por ADR

| RN | Origem | Tela | Etapa | Testes |
| --- | --- | --- | --- | --- |
| RN30 | RNF04, ADR 0003 | Perfil (ainda não existe no Doop) | 11 | — |

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
