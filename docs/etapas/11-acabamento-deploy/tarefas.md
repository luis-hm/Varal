# Tarefas — Etapa 11

> **Contém:** checklist ordenada, responsáveis e dependências; abertura concluída; implementação e validação parciais, sem CA final aprovado.
> **Origem:** spec/plano/decisões 11, ADR0015 e protocolo ratificado do journal.

Abertura autorizada após merge 10 `5cd29ba`; execução local continua sem novo ok genérico. Não marcar código/testes pela existência destes documentos. Todos preservam alterações concorrentes.

| ID | Checklist | Responsável | Depende de | CAs |
| --- | --- | --- | --- | --- |
| T01 | [x] Integrar fontes atuais, Q11-1–11/T11-A–M, ADR0015, protocolo e abertura; registrar P10 resolvida/P11/P6 e Ajustes atestados | Docs + orquestrador | merge 10 | todos |
| T02 | [ ] Inventariar FKs/Collector/auth/fontes de R/ACL; migrações, triggers, wrappers e revisão de atomic externo | Backend; segurança leitura | T01 | 01–09 |
| T03 | [ ] Jobs/exportação/lotes/TTL/idempotência/fencing, artefato privado e download reautorizado | Backend | T02 | 01–04 |
| T04 | [ ] Guardas puras do conjunto, intenção/reauth/exclusão/capacidades e preservação do grupo/pins10 | Backend | T02 | 05–08 |
| T05 | [ ] Cliente/ledger/outbox journal, cleanup/barreiras08–10 e comandos de reconciliação/restore | Backend | T03/T04 e contrato journal | 04/08/09/16 |
| T06 | [ ] Writer externo serializado/fsync/checkpoint/recibos/retenção e testes de crash/terminal | DevOps | T01/protocolo | 09/16 |
| T07 | [x] Exportar OpenAPI composto e tipos reais duas vezes determinísticos no corte da integral 01; repetir se contrato mudar | Orquestrador + backend | API estabilizada | 18 |
| T08 | [ ] Ler Doop/guia atuais somente leitura; Perfil/reauth/estados reais, sem frame inventado | Frontend | T07 | 01–06/12 |
| T09 | [ ] PWA/SW/manifesto/assets públicos e isolamento sessão/abas/bfcache/respostas tardias/T11-H | Frontend | T01/contratos estáveis 09–10 e leitura Doop; não depende da API nova 11 | 10/11 |
| T10 | [ ] Acabamento/alvos/contraste/foco/labels/reduced-motion e capturas 360/390/1440 | Frontend | T08/T09 | 12 |
| T11 | [ ] Laboratório produtivo isolado TLS/proxy/SSR/migração/imagens/CI e guardas de volumes | DevOps | T01; API real para smoke | 14 |
| T12 | [ ] P3/P4 local: headers/IP/RN31 atômico/falha 503/sentinelas de logs | Backend + DevOps | T11 | 15 |
| T13 | [ ] S3 privado/backup consistente criptografado/restore novo; journal/ledger/pins antes de abertura | DevOps + backend | T05/T06/T11 | 09/16 |
| T14 | [ ] SMTP TLS/WebPush local reais sem egress, política09/SSRF e limites browser | DevOps + QA | T09/T11 | 10/17 |
| T15 | [ ] SSR restrito T11-G e medir 80 amostras Q11-8, p95 por série e artefatos reais | Frontend + QA | SSR pode iniciar com T01/T11 e contratos GET estáveis; medição após T10/T11 | 13 |
| T16 | [ ] Matriz CA→teste→resultado, concorrência/reauth/ACL/browser/visual e integral types/test/lint/E2E | QA | T03–15 | 01–18 |
| T17 | [ ] Segurança somente leitura, auditoria de decisões, correções e rechecagem dos bloqueantes | Segurança + decisor + donos | T16 | 01–18 |
| T18 | [ ] Ajustes finais atestados atuais, relatório/PROGRESSO/docs e matriz QA; commits locais conforme fluxo | Docs + orquestrador + QA | T17/resultados reais | 18 |
| T19 | [ ] Definir destino/condições P11 e revisar implantação remota concreta se autorizada | DevOps + dono | P11; prova local | implantação remota |

CA01–18 seguem abertos. Há testes/provas parciais concluídos, descritos no [checkpoint](relatorio.md); tarefas compostas permanecem desmarcadas até sua validação integral. T19 é dependência concreta P11; preparação local não encerra silenciosamente o escopo remoto. Sem push/envio externo/deploy real ou alteração dos volumes existentes.

## Checkpoint anterior das tarefas

T02–06: implementação API/journal/guardas/restore e testes dirigidos existentes; inventário, crashes e cadeia integrada ainda precisam do corte final. T08–10: Perfil/reauth/PWA/isolamento implementados; patch de main aninhado passou 5/5 e verificações estáticas, aguardando rebuild e novo axe/browser. T11–14: laboratório e provas isoladas reais disponíveis, mas atestado/cutover APP e transporte pela fila não concluídos. T15: SSR implementado, sem benchmark de 80 amostras. T16–18: integrais/QA/segurança em andamento, sem fechamento.

D11-3 tem smoke real do helper Redis com sentinelas e recusas; isso não é teste HTTP da cota. Manter E2E serial e Redis exclusivo, sem limpar desenvolvimento. Integral 01 reprovada (544 pytest aprovados/1 falha); integral 02 iniciada, sessão 46822, sem resultado; tipos herdados da 01 após conferência de hashes. Foco backend de isolamento eager somente nos testes/reauth nativa 299/300 s/multi-sessão/CSRF passou 10/10 em 38,53 s; diagnóstico 128/128 sem leak. Nodeid causador da integral permanece não identificado.

## Checkpoint vigente — prova operacional e janela QA

POS final ACL/direitos/objetos e ledger passou, com HMACs válidos ligados à mesma operação/época/fence/watermark e acl_sha256. Backup CURRENT `snapshot.T1fmz1pV` e `lab11-active stop/up` passaram: TLS confiável em ready/entrar e relay 200, web b1c9. D ativo fez login nativo novo e recebeu 404 duas vezes. Segurança adendo 21:46 encerrou os bloqueantes específicos de ACL/direitos/opt-out; não é aprovação global CA16/18.

Ferramenta RPO versionada passou exit 0, reproduzindo26,280613 s / 13 COMMITs do exercício anterior delimitado; não é RTO ACL novo, garantia de RPO ou perda zero. Make test546 API/149 web pré-Providers, web pós-delta152/152 e lint/build permanecem válidos nos seus cortes; app API/websrc não mudou.

E2E01 foi interrompido intencionalmente após 516,884 s, SIGTERM do supervisor/143 e comando-15; wrapper não aprovado, fontes iguais. Artefatos privados em `/tmp/varal11-e2e-partial-01-artifacts`. Foco01 não executou casos: webServer 120 s timeout com Next próprio órfão na 3000, depois encerrado com seu pai; preparo Compose com cwd web inválido não é prova e foi corrigido em up-corrected. Foco02 com worker real1 passou 7/8 em 1,6 min; boleto/Pix passaram e signup ainda falhou em URL5 s. Diagnóstico UI separado mediu POST200 em780 ms, raiz1797 ms e heading1955 ms, sem reproduzir causa. CPU disputada foi observada e não houve locks PG na inspeção posterior; não atribuir causalidade às falhas.

Sincronização auth de teste passou 1/1 mobile 28,3 s aguardando POST200 antes de URL; sem alteração de timeout/produto. Harness E2E/CI worker 1 apenas, sem mudar cota. Benchmark80, calibração e RNF10/WebKit têm GO/janela exclusiva agora, sem resultados antecipados. Worker/beat LAB e API/worker/beat padrão estão pausados; nenhum E2E/build/backup/teste disputa a janela. Desempenho vem antes do E2E final se houver necessidade de otimização.

CA01–18 seguem sem fechamento integrado, especialmente CA13/18; as provas específicas da restauração não aprovam todos os requisitos. [Relatório](relatorio.md) concentra cortes, limites e próximos resultados. Nenhum novo gate de autorização genérica; P11 destino remoto ausente, P6 externa e P9 próximo push autorizado. Sem push/deploy/limpar-dev.

## Corte final de estabilização

Implementação local e provas focais RN30/RN31 consolidadas no relatório; web156/156 após correção de hidratação. Integral E2E135/8/3, seguida de correções de testes e retestes direcionados, não equivale a integral verde. T15 permanece pendente por RNF05; T16–18 ainda não permitem aceite integral da etapa. LAB parado, ambiente padrão restaurado, volumes preservados. Não retomar variantes E1–E4/S1 por tentativa: D11-7 rege o próximo diagnóstico.
