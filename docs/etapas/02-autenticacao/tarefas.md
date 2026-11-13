# Tarefas — Etapa 02 (Autenticação)

> **Contém:** checklist ordenada, responsáveis e critérios de aceite da Etapa 02.
> **Origem:** [spec.md](spec.md) e [plano.md](plano.md).

**Estado: implementação e validação concluídas em 13/11/2026; commit/apresentação pelo orquestrador.** Aprovados os estados de cadastro/recuperação no mesmo layout, uso dos frames apresentados e animação da folha conforme o guia (`100%`, `0,5s`). Não se aplica `varal-boletos`.

| # | Tarefa | Responsável | CA |
| --- | --- | --- | --- |
| 1 | [x] Apresentar escopo/ajustes/riscos e obter ok, incluindo estados de formulário sem frame, frames draft e divergência de movimento | orquestrador | CA13–CA14 |
| 2 | [x] Conferir compatibilidade nos locks e schema da versão escolhida; fixar allauth e validar montagem `/api/auth/`, CSRF, payloads e renderização do schema nativo | varal-backend | CA11–CA12, CA15 |
| 3 | [x] Acrescentar campos de usuário e modelo/restrição de espaço pessoal; manter username interno único/seed/admin; testar dois cadastros, migração de dados, seed repetido, rollback e unicidade | varal-backend | CA01, CA04–CA05 |
| 4 | [x] Configurar cadastro/login e-mail, adapters Google e sessão; impedir vínculo automático inseguro e duplicação; teste de credencial inválida/inativo/cancelamento | varal-backend | CA01–CA06 |
| 5 | [x] Implementar recuperação por link, envio Celery e testes de e-mail desconhecido/token inválido, expirado e reutilizado | varal-backend | CA07–CA08 |
| 6 | [x] Implementar `/api/me/`, saída e proteções CSRF/cookies; testar isolamento entre dois usuários e ausência de segredos | varal-backend | CA09–CA12 |
| 7 | [x] Compor schema allauth + DRF com validação, teste de referências/colisões e geração determinística; ajustar comando usado por Makefile/CI | varal-backend + varal-devops | CA15 |
| 8 | [x] Rodar `make types`; versionar OpenAPI e tipos gerados, sem tipos de API manuais | orquestrador | CA15 |
| 9 | [x] Reler os dois frames e screenshots, guia, tokens e componentes; aplicar decisões aprovadas sem escrever no Doop | varal-frontend | CA13–CA14 |
| 10 | [x] Integrar cliente tipado após validar schema composto, proxy headless sem barra preservando POST e cookies/Set-Cookie, CSRF e guarda sem cache compartilhado | varal-frontend | CA03, CA09, CA11, CA15 |
| 11 | [x] Implementar Entrar e estados aprovados de cadastro/recuperação/retorno Google nas duas resoluções; dados próprios e saída no shell | varal-frontend | CA01–CA03, CA06–CA10, CA13–CA14 |
| 12 | [x] Documentar variáveis Google vazias e e-mail; conferir retorno OAuth em 8000 e origem 3000; adaptar ambiente/CI de E2E com API real | varal-devops | CA07, CA12, CA16 |
| 13 | [x] Testar fluxos integrados e estados de erro, adaptar regressões da Etapa 01 à autenticação e comparar screenshots 390×844/1440×900 com o Doop | varal-qa | CA01–CA16 |
| 14 | [x] Executar `make test`, `make lint`, E2E e regeneração sem diff; distinguir testes simulados de validação real do Google | varal-qa | CA15–CA16 |
| 15 | [x] Revisar sessão, CSRF, cookies, recuperação, redirect e vínculo Google, dados próprios e segredos; corrigir bloqueantes | varal-seguranca; correções pelo agente da área | CA06–CA12, CA16 |
| 16 | [x] Rever ajustes com a fonte disponível; marcar apenas o concluído, sem reescrever itens; registrar limitações de acesso ao remoto | orquestrador | CA12, CA16 |
| 17 | [x] Escrever relatório e atualizar PROGRESSO, matriz, API/stack/design com comportamento e testes reais; registrar decisões/desvios | varal-docs | CA16 |
| 18 | [x] Fazer commits locais pt-BR, apresentar relatório e parar; sem push e sem iniciar Etapa 03 | orquestrador | CA16 |

Evidências: [relatorio.md](relatorio.md). `make test`: API 31/31, Vitest 38/38; lint verde; E2E integral 38/38; tipos regenerados sem alteração; build de produção verde e smoke posterior 4/4 nas duas resoluções.
