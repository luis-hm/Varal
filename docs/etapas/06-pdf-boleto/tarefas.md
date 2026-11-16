# Tarefas — Etapa 06 (PDF do boleto)

> **Contém:** checklist de implementação e validação do PDF privado com leitura assíncrona.
> **Origem:** spec/plano da 06, RF23–RF25/RN25–RN29, ADR 0002/0010 e autorização delegada do dono.

Etapa aberta em 16/11/2026 após merge da 05 em `e5c94e3`. Definição de pronto alcançada em 16/11/2026: 390 pytest, 89 Vitest e 97 E2E passaram, com 3 skips previstos; lint, tipos determinísticos, prova real Celery/S3 e inspeção headed concluídos. Pronta para commit e merge local, sem push.

| # | Tarefa | Responsável | CA |
| --- | --- | --- | --- |
| 1 | [x] 05 validada/integrada; branch 06 aberta e fontes registradas sem editar origem; P6 externa/P1 preservadas | orquestrador/docs | todos |
| 2 | [x] Triagem de acesso/estados/limites/metadados/limpeza e ADR 0010, incluindo Q06-18/Q06-19 de candidatos/arquivo inteiro | varal-decisor | CA01–CA12 |
| 3 | [x] Extrator pdfplumber integrado: linhas 47/48, metadados, divergência, múltiplos códigos e fallback sem OCR | varal-boletos | CA04–CA07 |
| 4 | [x] Validação NUL/Unicode/limites fora do DRF e fixtures adversárias/linha quebrada integradas e cobertas no pytest integral | varal-boletos | CA02,CA04–CA07 |
| 5 | [x] DocumentoBoleto, destino/vínculo distintos, marca irreversível e Instrumento manual/metadados; migrações 0002/0003 sem backfill destrutivo | varal-backend | CA08–CA12 |
| 6 | [x] Spool 202 e Celery com processo dedicado, limites e resultado sanitizado; mutex operacional e tentativa UUID protegem execuções antigas | varal-backend | CA01–CA08,CA15 |
| 7 | [x] Confirmação/troca/remoção atômicas, acesso revalidado e sem retorno de documento antigo a draft; histórico minimizado | varal-backend | CA08–CA10 |
| 8 | [x] Intenção de limpeza persistida, disparo após commit/recuperação, expiração 24 h e chaves imutáveis; regressões de rollback/limpeza adicionadas | varal-backend | CA09,CA10 |
| 9 | [x] django-storages/S3 real, bucket privado/bootstrap, endpoints interno/público, spool compartilhado, Compose/CI/lock/env/stack atualizados | varal-devops | CA01,CA03,CA11,CA14 |
| 10 | [x] Prova real de objeto/Celery, spool removido, exclusão/cleanup e URLs pública/anônima/expirada; autorização coberta por regressões específicas | backend/devops | CA08,CA11 |
| 11 | [x] OpenAPI/tipos gerados e determinismo com exit 0; referências Doop 05/M01, 06/M02 e 07/D03 registradas; comparação final fica na tarefa 13 | orquestrador/frontend | CA13,CA14 |
| 12 | [x] Upload/polling/conferência/candidatos/prévia/download implementados e conferidos com PDF real/fallback em navegador headed | varal-frontend | CA05,CA06,CA12,CA13 |
| 13 | [x] test/lint/types/E2E verdes (390 pytest, 89 Vitest, 97 E2E e 3 skips previstos), screenshots/Doop e matriz atualizada; cenário uploader perde acesso após vínculo | varal-qa | todos |
| 14 | [x] Revisão final Astra por leitura sem bloqueantes após mutex/tentativa/intenção, cobrindo arquivos, acesso, isolamento/logs/limpeza; nenhuma nova execução de testes atribuída à revisão | varal-seguranca; área responsável | CA02,CA07–CA11,CA14,CA15 |
| 15 | [x] Auditoria de decisões, revisão atual de Ajustes e relatório/progresso/modelo/API/design/stack atualizados | decisor/docs | CA14 |
| 16 | [ ] Commit e merge local pelo orquestrador, sem push | orquestrador | CA14 |
