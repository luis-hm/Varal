# Matriz de rastreabilidade

> **Contém:** para cada requisito, os casos de uso, regras, telas do Doop, etapa e testes que o cobrem.
> **Origem:** `docs/especificacao-varal.md` (seções 4–7 e 12) e o plano de etapas; a coluna Testes é preenchida pelo `varal-qa`.

Telas: nome do frame no canvas `k0kB5dc-Vo` (ids em [design/README.md](design/README.md)). Testes: nome do teste com o ID da regra (`test_rn14_...`).

## Requisitos funcionais

| RF | CU | RN | Tela (Doop) | Etapa | Testes |
| --- | --- | --- | --- | --- | --- |
| RF01 | CU01 | RN03 | 01 · Entrar | 02 | — |
| RF02 | CU01 | RN03 | 01 · Entrar | 02 | — |
| RF03 | CU01 | — | 01 · Entrar | 02 | — |
| RF04 | CU02 | RN04 | 10 · Grupo | 03 | — |
| RF05 | CU03 | RN05, RN24 | 11 · Convidar membro | 03 | — |
| RF06 | CU03 | RN04, RN05, RN21 | 10 · Grupo | 03 | — |
| RF07 | CU04 | — | 10 · Grupo | 03 | — |
| RF08 | CU05 | RN08, RN09, RN10, RN11 | 05 · Nova conta, 06 · Conferir conta | 05 | — |
| RF09 | CU05 | RN11 | 05 · Nova conta, 06 · Conferir conta | 05 | — |
| RF10 | CU05 | RN11 | 05 · Nova conta, 06 · Conferir conta | 04 | — |
| RF11 | CU05 | RN01, RN06 | 06 · Conferir conta | 04 | — |
| RF12 | CU07 | RN22 | 07 · Detalhe da conta | 04 | — |
| RF13 | CU06 | RN02, RN06, RN07, RN12, RN13 | 02 · Início, 03 · Contas | 04 | — |
| RF14 | CU08 | RN29 | 07 · Detalhe da conta, 13 · Modo simples | 05 | — |
| RF15 | CU08 | RN14 | 08 · Marcar como paga | 07 | — |
| RF16 | CU08 | RN15 | 08 · Marcar como paga, 09 · Conta paga | 07 | — |
| RF17 | CU08 | RN16 | 07 · Detalhe da conta | 07 | — |
| RF18 | CU09 | RN17, RN23 | 05 · Nova conta, 10 · Grupo | 08 | — |
| RF19 | CU12 | RN17, RN18, RN23 | — (agendador) | 08 | — |
| RF20 | CU12 | RN18, RN19 | 04 · Avisos | 09 | — |
| RF21 | CU10 | RN20 | 12 · Pedir para alguém pagar | 10 | — |
| RF22 | CU11 | RN07, RN14, RN15 | 13 · Modo simples | 10 | — |
| RF23 | CU05 | RN25 | 05 · Nova conta | 06 | — |
| RF24 | CU05 | RN26, RN27, RN28 | 06 · Conferir conta | 06 | — |
| RF25 | CU08, CU11 | RN29 | 07 · Detalhe da conta, 13 · Modo simples | 06 | — |

## Requisitos não funcionais

| RNF | Etapa | Testes |
| --- | --- | --- |
| RNF01 | 03 (filtro central), revisado em toda etapa | — |
| RNF02 | 02 | — |
| RNF03 | 06 | — |
| RNF04 | **sem etapa** (ver Decisões pendentes no PROGRESSO) | — |
| RNF05 | 11 | — |
| RNF06 | 06, 09 | — |
| RNF07 | 09 | — |
| RNF08 | 01, 11 | — |
| RNF09 | 01, 11 | — |
| RNF10 | 09, 11 | — |
| RNF11 | 00 (fuso/UTC), 04 (centavos) | — |
| RNF12 | 00 (`make types` + CI) | `api.yml` job `types` |

## Fundação (Etapa 00)

| Item | Testes |
| --- | --- |
| Healthcheck `/api/health/` | `api/tests/test_fundacao.py::test_health_ok`, `web/src/app/page.test.tsx` |
| OpenAPI servido | `api/tests/test_fundacao.py::test_schema_documents_health` |
| Celery configurado | `api/tests/test_fundacao.py::test_celery_ping_task` |
