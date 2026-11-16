# Tarefas — Etapa 09 (Notificações)

> **Contém:** checklist da etapa aberta, responsáveis e critérios a comprovar.
> **Origem:** [spec](spec.md), [plano](plano.md), [Q09-1–9/D09-1–3](decisoes.md) e delegação vigente.

Etapa concluída em 16/11/2026: 483 pytest, 111 Vitest, tipos duas vezes determinísticos e lint verdes; Playwright completo final 131 aprovados/3 skips em serviços locais existentes verificados, sem rebuild. Wrapper make e2e anterior falhou no GHCR antes do navegador. QA confirmou matriz/cleanup; segurança e decisões sem bloqueantes.

| # | Tarefa | Responsável | CA |
| --- | --- | --- | --- |
| 1 | [x] Registrar commits/merge da 08, abrir branch 09 e conferir Ajustes pelo relato vigente do dono no chat | orquestrador/docs | todos |
| 2 | [x] Integrar Q09-1–9/D09-1–3/ADR 0013 e alinhar spec/plano/tarefas | docs/decisor | todos |
| 3 | [x] Modelos/migrações e invariantes de aviso/entrega/inscrição/checkpoint; identidade e revogação terminal | backend | CA03–CA10, CA12 |
| 4 | [x] Rotina única ordenada 08→09 às 07:00, fases/janela e reavaliação idempotente | backend | CA01, CA02, CA08, CA09, CA14 |
| 5 | [x] Consumir todos os EventosPagamento da 07; RN21/P7 novos e importação legada somente central | backend | CA03–CA05, CA07, CA09 |
| 6 | [x] Outbox/lease/até três tentativas totais, estado incerto e filhos por dispositivo; transporte protegido contra SSRF | backend | CA06, CA10, CA12 |
| 7 | [x] API central/resumo/leitura individual/em lote, preferências e push; schema e tipos determinísticos | backend | CA07, CA10–CA13 |
| 8 | [x] Configuração local SMTP/Web Push/VAPID, worker e beat; provar transportes reais e registrar limites | DevOps | CA06, CA10, CA12, CA14 |
| 9 | [x] Ler Doop/guia e integrar central/gaveta/recentes/não lidos e estados vazios/erro nas duas larguras | frontend | CA11, CA13 |
| 10 | [x] Gesto de push, permissão negada, SW/SSR seguros, logout/troca de conta e preferências na central existente | frontend | CA10, CA12 |
| 11 | [x] Testes CA01–CA14, concorrência, privacidade/P7/legados/revogação terminal, retries e provas reais | QA/backend/DevOps | todos |
| 12 | [x] Comparação Doop/capturas e navegação/foco comprovados; matriz e cleanup finais confirmados pelo QA | QA/frontend | CA11–CA13 |
| 13 | [x] Segurança em leitura e auditoria decisória sem bloqueantes; Ajustes finais atestados no chat e relatório definitivo com QA final | segurança/decisor/docs | todos |

P6 externa e P11/destino pendente preservadas. P10 resolvida por delegação expressa para composição do Perfil na 11, sem implementação agora; P7 resolvida pela entrega RN32 privada e legado seguro, com critérios verdes. Sem push/deploy; liberar a 10 somente após fechamento da 09. Não marcar execução como concluída por proposta, leitura preparatória ou mock de provedor.
