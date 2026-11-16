# Tarefas — Etapa 07 (Pagamento)

> **Contém:** checklist de implementação e validação de pagamento, comprovante, undo e progresso.
> **Origem:** spec/plano07, RF15–RF17/RN14–RN16/CU08, Q04-37/Q21/Q12/Q23 e autorização delegada do dono.

Etapa aberta em 16/11/2026 após merge local da 06 em `b21bd83`. Decisões Q07-1–11/ADR 0011 ratificadas por delegação; concluída com definição de pronto cumprida; commit/merge local pendente.

| # | Tarefa | Responsável | CA |
| --- | --- | --- | --- |
| 1 | [x] Encerrar06 com resultados reais, commit/merge local, abrir07 e conferir Ajustes vigentes sem editar origem | orquestrador/docs | todos |
| 2 | [x] Triar propostas vs fonte: integral/parcial, autoria/papel alterado, anexo posterior, retenção, métricas e reabertura | varal-decisor | todos |
| 3 | [x] Pagamento UUID/centavos/data/autoria e marca desfeita, restrição única ativa, migrações sem apagar histórico | varal-backend | CA01,CA02,CA04,CA08 |
| 4 | [x] Permissão central de pagar/desfazer, alvo UUID e transações compatíveis com saída/RN32; valor esperado/data Fortaleza | varal-backend | CA01–CA04,CA08 |
| 5 | [x] DocumentoComprovante e endpoints próprios com papel pagador; spool/S3/validação isolada foto/PDF, sem reaproveitar permissão de editar boleto | backend/devops | CA03,CA05–CA07,CA10 |
| 6 | [x] Confirmação/anexação posterior, upload tardio, undo preservando evidência histórica e limpeza apenas de draft/exclusão física após commit, sem retorno a draft | varal-backend | CA06–CA10 |
| 7 | [x] Históricos/flags de ações e detalhe, sem payload/URL em logs, autor excluído Ex-membro | varal-backend | CA01,CA08,CA10 |
| 8 | [x] Resumo/PorCasa/MemberRow pelo visível, barra/pagasvaral e contrato coletivo Ex-membro sem inferir FK apagada | varal-backend | CA11,CA12 |
| 9 | [x] OpenAPI/tipos determinísticos; reler Doop08/M03,09/M04,07/D03,02/D02,10/D04 e componentes atuais | orquestrador/frontend | CA13,CA14 |
| 10 | [x] UI pagar/data/comprovante/undo, estado bloqueado em gravação, confirmado e progresso; duas larguras/movimento reduzido | varal-frontend | CA01,CA02,CA05,CA06,CA08,CA11,CA13 |
| 11 | [x] test/lint/types/E2E, provas reais de arquivo/assinatura, duas marcações/undo/papel alterado/upload tardio e matriz | varal-qa | todos |
| 12 | [x] Segurança de todas as rotas/arquivos/papéis, contadores/404, limites e cleanup; corrigir bloqueantes | varal-seguranca | CA03–CA10,CA14 |
| 13 | [x] Auditoria final sem bloqueantes, ajustes e relatório/progresso/docs/matriz atualizados; P10/P11 específicos da 11 preservados | decisor/docs | CA14 |
| 14 | [ ] Commit e merge local, sem push | orquestrador | CA14 |


Implementação, tipos determinísticos, lint, provas reais S3/Celery e segurança final aprovados. `make test`:413 pytest/91 Vitest; após ajuste mínimo de estado vazio, web completa93/93. Foco pagamento10/10 e regressões de legenda6/6 verdes. Item11 concluído: E2E final107 aprovados/3 skips previstos em6,9min, status passed/exit0; lint final exit0. Rodada anterior com6 falhas corrigidas não vale aprovação. Item 13 concluído; resta o item 14 de commit/merge local. Ver [relatório](relatorio.md).
