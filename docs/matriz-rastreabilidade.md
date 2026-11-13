# Matriz de rastreabilidade

> **Contém:** para cada requisito, os casos de uso, regras, telas do Doop, etapa e testes que o cobrem.
> **Origem:** `docs/especificacao-varal.md` (seções 4–7 e 12) e o plano de etapas; a coluna Testes é preenchida pelo `varal-qa`.

Telas: frame mobile ↔ frame desktop no canvas `k0kB5dc-Vo` (ids e equivalência em [design/README.md](design/README.md)). Testes: nome do teste com o ID da regra (`test_rn14_...`).

## Requisitos funcionais

| RF | CU | RN | Tela mobile ↔ desktop (Doop) | Etapa | Testes |
| --- | --- | --- | --- | --- | --- |
| RF01 | CU01 | RN03 | 01 · Entrar ↔ D01 | 02 | — |
| RF02 | CU01 | RN03 | 01 · Entrar ↔ D01 | 02 | — |
| RF03 | CU01 | — | 01 · Entrar ↔ D01 | 02 | — |
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
| RNF01 | 03 (filtro central), revisado em toda etapa | — |
| RNF02 | 02 | — |
| RNF03 | 06 | — |
| RNF04 | 11 (RN30, [ADR 0003](arquitetura/adr/0003-rn30-exportar-e-excluir-dados.md)) | — |
| RNF05 | 11 | — |
| RNF06 | 06, 09 | — |
| RNF07 | 09 | — |
| RNF08 | 01, 11 | e2e `rnf08 ca13: … alvos ≥ 44px em 360px` (vitrine e 5 páginas), `ca05/d1: Button renderizado com 52px…` (`web/e2e/design-system.spec.ts`); Vitest `ca05/d1: the button is 52px tall…` (`button.test.tsx`) |
| RNF09 | 01, 11 | Vitest `ca08/rnf09: every status shows the Doop icon and text, never colour alone` (`status-badge.test.tsx`), `ca09/rnf09: badge and main text pairs reach 4.5:1` (`tokens.test.ts`) |
| RNF10 | 09, 11 | — |
| RNF11 | 00 (fuso/UTC), 04 (centavos) | — |
| RNF12 | 00 (`make types` + CI) | `api.yml` job `types` |

## Regras acrescentadas por ADR

| RN | Origem | Tela | Etapa | Testes |
| --- | --- | --- | --- | --- |
| RN30 | RNF04, ADR 0003 | Perfil (ainda não existe no Doop) | 11 | — |

## Fundação (Etapa 00)

| Item | Testes |
| --- | --- |
| Healthcheck `/api/health/` | `api/tests/test_fundacao.py::test_health_ok`, `web/src/app/page.test.tsx` |
| OpenAPI servido | `api/tests/test_fundacao.py::test_schema_documents_health` |
| Celery configurado | `api/tests/test_fundacao.py::test_celery_ping_task` |
