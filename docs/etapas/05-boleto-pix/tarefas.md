# Tarefas — Etapa 05 (Boleto e Pix)

> **Contém:** checklist ordenada e responsáveis para a fatia boleto/Pix.
> **Origem:** spec e plano da Etapa 05; autorização do dono de continuidade entre etapas em 15/11/2026.

Etapa aberta em 16/11/2026 após merge local da 04 em `fe48cbe`, concluída e validada no mesmo dia: 354 pytest, 83 Vitest e 91 E2E verdes (3 skips previstos), lint, tipos determinísticos, capturas revistas e segurança sem bloqueantes. Commit/merge local a cargo do orquestrador; sem push.

| # | Tarefa | Responsável | CA |
| --- | --- | --- | --- |
| 1 | [x] Encerrar correções/QA/segurança da 04; merge local --no-ff; branch `etapa/05-boleto-pix`; registrar declaração atual dos Ajustes e P6 externa | orquestrador | todos |
| 2 | [x] Conferir plano/decisões e política de fator/valor; anotar decisões novas por delegação, sem inventar resposta literal do dono | varal-decisor | CA02,CA08 |
| 3 | [x] Parser bancário 47: normalização, DVs, valor, fator novo/ausente, vetores e erros; testes puros integrados | varal-boletos | CA01,CA02,CA04 |
| 4 | [x] Parser arrecadação 48: segmentos/identificadores válidos, módulo indicado, DVs de blocos/geral, referência/valor, data solicitada | varal-boletos | CA03,CA04 |
| 5 | [x] Pix BR Code/chave: TLV, CRC, montante, normalização, limites, chave embutida canônica, valor zero estático rejeitado, valor dinâmico ignorado, sem rede; suíte pura atual com 65 verdes, incluindo aviso RNF11 | varal-boletos | CA05–CA07 |
| 6 | [x] Modelo Instrumento/migração; preview autenticado documentado; validação e criação/edição atômicas com histórico sem código/chave integral; 54 testes API direcionados e 89 regressões de contas verdes | varal-backend | CA08,CA10,CA11 |
| 7 | [x] Detalhe autorizado, permissões por papel/espaço, 404 uniforme e minimização no admin/logs; revisão de leitura do backend sem bloqueantes | varal-backend | CA09 |
| 8 | [x] Schema/tipos gerados e regeneração determinística confirmada em `make types`; nenhuma mudança posterior de API | orquestrador | CA14 |
| 9 | [x] Reler HTML/screenshots 05/M01, 06/M02,07/D03, guia e componentes do Doop; canvas somente leitura | varal-frontend | CA13 |
| 10 | [x] Formulário boleto/Pix/chave, conferência/cópia/fallback, controles protegidos em gravação e sessão local preservada no refetch; 27 testes pertinentes finais, lint/typecheck verdes; três regressões falharam antes do patch | varal-frontend | CA04,CA06–CA08,CA11–CA13,CA15–CA16 |
| 11 | [x] QA integral: 354 pytest, 83 Vitest, 91 E2E passaram e 3 skips previstos; teclado/4096 caracteres e capturas finais 390×844/1440×900 comparadas ao Doop; lint e tipos determinísticos verdes | varal-qa | CA01–CA16 |
| 12 | [x] Acesso, parser adversário, ausência de fetch dinâmico, logs/histórico e interface revisados; dois achados funcionais corrigidos, reauditoria final sem bloqueantes | varal-seguranca; agentes da área | CA09,CA14–CA16 |
| 13 | [x] Auditoria das decisões e relatório/progresso/modelo/API/design/matriz atualizados com evidência final; P6 preservada externa, sem fingir reexportação | varal-decisor, varal-docs | CA14 |
| 14 | [x] Commits locais Conventional Commits pt-BR, sem push; relatório; seguir autorização vigente para próxima etapa | orquestrador | CA14 |
