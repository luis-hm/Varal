# Relatório — Etapa 11

> **Contém:** checkpoint de implementação e provas locais, falhas preservadas e verificações finais pendentes; não é fechamento.
> **Origem:** contratos Q11-1–11/T11-A–M/D11-1–6, relatos backend/frontend/DevOps/QA, revisão final candidata de segurança/decisões e resultados supervisionados da orquestração em 16/11/2026.

**Estado: CA13/RNF05 reprovado no baseline oficial; otimização e validação local em andamento. CA01–18 ainda sem fechamento integrado; CA16/18 não aprovados por antecipação.** Branch `etapa/11-acabamento-deploy`, etapa 10 integrada no commit `062258c`/merge `5cd29ba`. Nenhum resultado da 10 é contado como teste da 11.

## Resultado do corte final

**Web final: 156/156, 44 arquivos, 156 s, exit 0**, com fontes estáveis após o fix de hidratação. API permanece no corte aprovado de 546 testes. ESLint web completo e TypeScript (`next typegen && tsc --noEmit`) passaram no corte final; Ruff permanece no corte sem alterações da API. E2E integral terminou 135/8/3; os cenários corrigidos e o defeito de hidratação tiveram retestes aprovados, sem uma nova integral verde. RNF05 segue reprovado; a etapa permanece aberta. Ambiente padrão restaurado e laboratórios parados, volumes preservados. Alterações de implantação do Silo produzidas em paralelo não pertencem a este commit de estabilização.

## Implementação e contratos

**Adendo de HMG e produção preparada (17/11/2026):** novo pedido expresso do dono autorizou projeto Varal no Coolify, branchdevelop via gh, dois workflows porpush e implantação somente HMG. `hmgvaral.codehub.systems` está publicado em3395d75 por webhook HMAC real, HTTPS válido/health/ready200,18 verificações HTTP de auth/CSRF/SSR/isolamento/PDF-Celery-S3 aprovadas e dois usuários fictícios excluídos. `varal`/main permanece parado, gatefalse/autodeployfalse e workflow porpushskipped. CI ainda registra falhas e bloqueia publicação automática; nenhuma IA ativada, CA encerrada ou produção iniciada. [Runbook](../../arquitetura/coolify-varal.md), [evidência](evidencias/coolify-hmg-2026-11-17.json), [smoke](evidencias/coolify-hmg-smoke-2026-11-17.json). Limites e recuperação integrada pendentes estão nesses registros; os adendos históricos abaixo precedem essa publicação de HMG.

**Adendo posterior de backup do Silo (16/11/2026):** por pedido expresso, agenda diária03h Fortaleza e dois arquivos reais locais confirmados, um deles restaurado em volume novo isolado. PDF/PNG e metadados/hash, IAM/runtime e anônimo403 passaram; origem preservada, somente as duas fixtures próprias removidas. Diretório0700 e arquivos0600, fonte retomada após pausa de backup. Helpers de teste parados, primário saudável/HTTPS200. [Runbook](../../arquitetura/silo-backup-recuperacao.md) e [evidência](evidencias/silo-backup-recuperacao-2026-11-16.json). Arquivo gzip/tar local sem criptografia adicional, mesmo disco, sem PostgreSQL/journal: não aprova CA16/18 nem recuperação global do Varal. Atualiza a pendência de backup do storage registrada no adendo anterior abaixo; deploy do app permanece pendente.

**Adendo de armazenamento remoto autorizado (16/11/2026):** Silo instalado na VPS existente pelo Coolify/MCP por pedido expresso do dono, separado do laboratório e sem deploy do app. Console e API S3 HTTPS200/TLS válido, bucket privado, chave restrita, I/O/hash/anônimo403, expiração real60s e persistência após reinício passaram; objetos sintéticos removidos. A correção do503 ficou nas rotas Traefik do recurso Silo, com volume externo preservado e sem reinício do proxy global. [Runbook](../../arquitetura/silo-coolify.md), [Compose](../../../infra/silo/compose.coolify.yml) e [evidência](evidencias/silo-coolify-2026-11-16.json). Credenciais inventariadas em `SILO_PROD_*`, sem troca do desenvolvimento. Backup/restauração remotos e implantação da aplicação pendentes; nenhuma aprovação de CA16/18 ou garantia contra perda da VPS.

API integra revisão transacional época/R e triggers, exportação privada paginada (formato interno 2, JSON externo v1), reauth/intenção/exclusão em fases, journal/cleanup, RN31 Redis e comandos de restore. Frontend integra Perfil Q11-11, reauth nativa, ticket Google T11-J, isolamento de identidade/abas/SSR/SW e PWA pública. Infra integra laboratório TLS, roles separadas, storage privado, backup físico/WAL/witness, gates de ledger/direitos/ACL e primário restaurado por ACTIVE_RESTORE.

[Spec](spec.md), [plano](plano.md), [tarefas](tarefas.md), [decisões](decisoes.md), [ADR0015](../../arquitetura/adr/0015-exportacao-exclusao-e-prova-local.md), [protocolo](../../arquitetura/protocolo-journal.md) e [runbook](../../arquitetura/operacao-local.md) registram o contrato. T11-L exige igualdade conservadora dos direitos e ACL/auth da fonte atual quiescente com clone pós-journal; T11-M delimita exclusão administrativa/ORM e limpeza parcial. Não são escolhas novas deste relatório.

## Evidências consolidadas

### Corte final da regressão e correção comprovada

A integral E2E F2-03 terminou **135 aprovados, 8 falhas e 3 skips em 146 casos**, exit 2 no make, fontes estáveis. As falhas envolveram seis cenários: login pós-logout por fixture que mantinha o bloqueio local; placeholder antigo do Perfil; seletores de espaço ambíguos; sincronização de cadastro/salvamento; medição de geometria. Corrigidos apenas os testes correspondentes, sem elevar timeouts. Foco agrupado: **10 aprovados, 1 falha e 1 skip**; a geometria ainda falhou. Reteste com espera pela geometria passou, mas seu log revelou um defeito real: servidor iniciava contador em zero e cliente com movimento reduzido iniciava no valor final, causando erro de hidratação.

`useContagem` agora inicia em zero nos dois lados; o efeito existente mostra o valor final no próximo quadro com movimento reduzido, preservando os 1200 ms/cúbica no movimento normal. Teste SSR→hydrate e animação passou 2/2, lint dirigido aprovado. Novo E2E de geometria exige ausência de erro de hidratação e passou **1/1**. Metadados dos retestes: [e2e-correcoes.json](evidencias/e2e-correcoes.json). Esses recortes não são somados para anunciar uma integral verde. A integral E2E inteira não foi repetida após as correções; CA18 continua aberto.

A imagem F2 do laboratório foi construída antes dessa correção pontual de hidratação; o laboratório está parado. Não atribuir o fix do código à imagem antiga. A suíte web do novo corte e a restauração do ambiente padrão são registradas no checkpoint final.


Prova focal final [RN30/RN31](evidencias/rn30-rn31-integracao.json) aprovada em laboratório real: onze POST HTTPS concorrentes resultaram em dez aceites e uma recusa 429, confirmados no PostgreSQL. Exportação idempotente incluiu categorias, NULL/centavos e arquivos pessoais, excluiu arquivos de grupo e recusou acesso alheio. PDF e comprovante tiveram bytes/hash corretos, negação anônima e expiração real de 60 s. DELETE 204 preservou os registros e arquivos do grupo, autorias NULL e ACL, com recibos reais PREPARE/COMMIT verificados. Não acrescenta prova de PUT físico tardio ou de todas as corridas RN32.

Laboratório ativo e antigos, browsers e clones próprios foram parados, preservando volumes. F2 é a seleção persistida do laboratório, com smoke aprovado; a fonte principal permanece inalterada.

| Prova / corte | Resultado e limite |
| --- | --- |
| `make test` supervisionado final 01 | **Exit 0: 546 pytest em 667,11 s e 149 Vitest/40 arquivos em 170,56 s**, um worker web; hashes das fontes antes/depois iguais. Artefatos `/tmp/varal11-final-test-supervised-01/{status.json,command.log}`. Corte anterior ao delta Providers D11-5 |
| Delta offline D11-5 | TanStack `mutations: {networkMode: "always", retry: false}` impede pausa/replay automático financeiro ao reconectar. Foco 3/3, lint dirigido/tsc passaram. Suíte posterior 01 terminou **151 aprovados/1 falha, 152 testes/41 arquivos, exit 2, 188,88 s**, `findByRole("Fechar detalhe")` em 1927 ms durante build concorrente; a causa não está comprovada. A mesma fonte, sem alterar timeout/assertivas/produto, passou na web supervisionada 02: **152/152, 41 arquivos, 153,82 s, exit 0**, hashes antes/depois iguais; `/tmp/varal11-final-web-supervised-02/{status.json,command.log}` |
| Lint e contrato | `make lint` final exit 0 em `/tmp/varal11-lint-final.log`. Tipos conferidos com os mesmos hashes da dupla execução determinística 01; não foram duas novas execuções |
| Fonte canônica F2 | Web integral **155/155, 43 arquivos, 160,11 s, exit 0**, hashes antes/depois iguais `7ea2412597c5f15bf58ba65c694b800808e7891f9997f6dc9e3aa6ae8e532eca`; `/tmp/varal11-final-web-f2-02/{status.json,command.log}`. F2-01 permaneceu reprovada 154/155; teste de gaveta passou a aguardar findByRole, sem mudar timeout/produto. `make lint` F2 também passou exit 0, `/tmp/varal11-lint-f2.log` |
| QA funcional/visual | **24/24**, oito cenários em 360/390/1440, axe e comparação com Doop/componentes atuais; Perfil não tem frame dedicado e canvas permaneceu somente leitura. Rodadas anteriores reprovadas não são somadas |
| PWA | Instalação técnica Chromium/CDP, estado instalado, launch HTTPS e uninstall aprovados; runner reproduzível `web/e2e/pwa11-install-final.mjs`. Não prova gesto físico de instalação ou entrega push externa |
| Reauth código CA06 | SMTP local e fluxo nativo aprovados: exportação 401 antes/após request de código e 202 só após confirm. Sessão inicial é fixture sintética force_login de conta sem senha/endereço verificado; não prova Google público. Sessões/códigos de teste foram removidos do browser |
| Identidade offline/BFCache | Logout offline entre abas e uso dos próprios dados/ações de B passaram. Chromium recusou BFCache por no-store; tentativa WebKit falhou antes do cenário por TLS. WebKit posterior validou TLS sem bypass, mas também não restaurou BFCache: skip de capacidade, nenhum primeiro frame persisted comprovado |
| CA08 real | Aceite10→DELETE204/journal→worker real→reserva/cópia S3/hash/ACL aprovados via DjangoClient em processo; sem proxy/browser e sem extrapolar a toda matriz de pagamento/undo |
| CA17 real | SMTP STARTTLS com uma captura `.invalid` aceita/1 e Push HTTPS/VAPID/AES por worker aceito/1 no receptor local. Sem provedor público/recepção push física; cenários de erro 09 mantêm evidência separada |
| Direitos aceitos CA16 | NEG rejeitou direitos pós-target ausentes apesar de PDF/objeto correto. POS passou ledger/rights/atestado/cutover e worker retomou PREPARANDO→ATIVA, origem NULL e SHA igual. Não equivale ao gate ACL/auth adicional |
| Gate ACL/auth T11-L | NEG de membro real removido passou por divergência de uma linha Membro; NEG específico opt-out passou com rollback da transação e uma linha Usuario divergente. POS final ACL/direitos/objetos e ledger passou, com HMACs válidos ligados à mesma operação/época/fence/watermark e acl_sha256. Backup CURRENT `snapshot.T1fmz1pV` e `lab11-active stop/up` passaram: TLS confiável em ready/entrar e relay 200, web b1c9. D ativo fez login nativo novo e recebeu 404 duas vezes. Segurança adendo 21:46 encerrou os bloqueantes específicos de ACL/direitos/opt-out; não é aprovação global CA16/18. |

Benchmark oficial de **80 amostras concluído e reprovado**, sem erros de carregamento; p95 pessoal frio/quente **5215,5/5710,2 ms**, grupo frio/quente **4612,1/4706,5 ms**, todos acima de 2000 ms. Evidência sanitizada versionada: [rnf05-baseline-01.json](evidencias/rnf05-baseline-01.json), SHA256 `fbadb5e103c2522341b03423ee5cd30ae712ba097a4146686ae0b717a8260228`. Nenhuma nova série de 80 amostras pós-otimização foi executada. **E2E integral01 não aprovado: interrompido intencionalmente**, SIGTERM/143 (-15 no comando), 516,884 s. Focos posteriores descritos abaixo; nenhum E2E integral verde. O smoke real do helper Redis validou limpeza só de chaves IP e guardas em container próprio; não substitui E2E ou teste HTTP da cota. API produtiva permanece no corte `42c84479…`; delta eager foi somente nos testes, corte API+testes `6a07c8da…`. Resultados não são somados entre cortes. API permanece sem mudança: sua evidência integral é válida, sem necessidade de repetir por delta só web. Hash agregado web/src histórico do delta offline, anterior a F2: `466fcafa99f066551d4ae036edd7f174f845c622ae6a3a1c993cf4b84f3c292d`.

## Restauração e segurança

Journal PREPARE/COMMIT/ABORT, DRAIN/SEALED, nonce/HMAC, checkpoint/WAL e atestado preservam a fronteira operacional ratificada. Collector aplica guardas ao conjunto; reaplicação não abre produto. INICIADA após restore fica incerta sem reenvio cego; ledger exige igualdade com fonte fechada, watermark/witness/fence/HMAC. Checkpoint separado não promete resistência a root que retroceda journal/checkpoint/chaves.

T11-L cobre ainda credenciais/ativo/permissões, sessões/prova allauth/tickets, EmailAddress/SocialAccount, vínculo/papel/reingresso/convites, audiência de contas/recorrências, arquivos, central/push e **prefs_notificacao**. Hashes privados não são dados anônimos. Gate autentica `acl_sha256` e o verificador recalcula estado no clone antes do cutover e no primário reiniciado. Recibo antigo sem esse campo não aprova ACL. Origem permaneceu fechada durante os gates; POS/restart final passaram sem dispensar exclusividade operacional e revalidação em nova recuperação.

Segurança adendo de 21:46 UTC não encontrou bloqueantes identificados nos caminhos específicos ACL/direitos/opt-out. O revisor conferiu diretamente fonte, vínculos e HMACs dos recibos privados, ACTIVE_RESTORE e logs sanitizados de backup/login; execução de consumo/prepare/finalize/readiness foi atribuída ao DevOps/root, sem alegar reexecução pelo revisor ou inspeção de logs individuais inexistentes. Isso não aprova globalmente CA16/18. Decisor mantém T11-L/M e D11-4–6; não houve edição dessas decisões por este checkpoint.

Cronômetro do exercício ACL novo: **1111,571 s**, de 21:10:28.245460Z (imediatamente antes de stage POS, depois de fence/cut) a 21:28:59.683389Z (após gates/cutover/restart/fresh-login404/TLS), em `acl-positive-timer.json`. Inclui NEG intercalado/esperas/aprovações e exclui preparação/backup/fence anteriores; distinto dos 1302,348 s e sem garantia de RTO geral.

Ferramenta RPO versionada foi executada exit 0 e reproduziu **26,280613 s / 13 COMMITs**, em `ca16-rpo-tool.json` no diretório LAB: refere-se ao exercício anterior delimitado, não ao cronômetro da restauração ACL nova, a garantia de RPO ou perda zero. RTO anterior **1302,348 s** incluiu NEG intercalado, não cronômetro puro. Backup CURRENT novo comprova backup da geração selecionada, sem autorização automática para restaurar/despachar novamente.

## Falhas preservadas e próximos passos

E2E01 foi interrompido intencionalmente após 516,884 s, SIGTERM do supervisor/143 e comando-15; wrapper não aprovado, fontes iguais. Artefatos privados em `/tmp/varal11-e2e-partial-01-artifacts`. Foco01 não executou casos: webServer 120 s timeout com Next próprio órfão na 3000, depois encerrado com seu pai; preparo Compose com cwd web inválido não é prova e foi corrigido em up-corrected. Foco02 com worker real1 passou 7/8 em 1,6 min; boleto/Pix passaram e signup ainda falhou em URL5 s. Diagnóstico UI separado mediu POST200 em780 ms, raiz1797 ms e heading1955 ms, sem reproduzir causa. CPU disputada foi observada e não houve locks PG na inspeção posterior; não atribuir causalidade às falhas.

Sincronização de teste auth passou 1/1 mobile em28,3 s: aguarda POST200 antes de URL, sem mudar timeout/produto. Storage usa dois UUIDs e Me401 mantém CSRF403. Worker do harness E2E/CI é1 (antes runtime4), sem mudar cota RN31. Esses ajustes são relatados como validação, sem nova decisão por este agente.

Integrais API 01/02 reprovadas por interferência eager e integral03 com API 546 aprovada/web148/149 reprovada permanecem históricas. Rastreio localizou a corrida eager em `test_rn21_pagamento_concorrente_com_saida`; isolamento do agendamento nos testes preservou produção/ping. Execução supervisionada interrompida exit143 também não virou aprovação. QA inicial teve falhas de harness e axe reais (main aninhado e texto acessível SideNav), corrigidas e revalidadas na 24/24. Web pós-Providers 01 reprovada continua preservada e a 02 posterior passou com fonte igual, sem relaxar timeout/assertivas.

## RNF05: baseline reprovado e otimização ainda sem aceite

O baseline oficial manteve carga/marco/critérios, sem descarte: 80 amostras, Chromium 158, quatro CPUs, CPU×4 e rede 9/1,5 Mbps/RTT150 ms, navegador direto sem relay, janela Varal exclusiva 21:57:02–22:07:57 UTC. Atividade de outros projetos não é controlada. Os quatro p95 reprovaram; ausência de erro HTTP não torna a navegação rápida.

Perf01 isola o contador, reutiliza Intl, remove ciclo de importação de Avisos e adia Folha/gaveta com fallback cancelável. Foco 26 e lint/tsc passaram; segurança delta 22:27 não encontrou novo bloqueante de privacidade no recorte. Imagem perf01 b0fa53… teve build 0; foi um corte anterior aos diagnósticos seguintes, sem meta/ganho demonstrado.

A calibração de quatro navegações perf01 **não é p95**: pessoal frio 14206 ms, quente 4892,5 ms, grupo frio 4181,1 ms, quente 5564 ms, todos acima de 2 s e sem erros HTTP. Possível custo de startup não foi estabelecido como causa. Diagnóstico separado: TTFB 508 ms, DCL 1058 ms, primeira alteração do contador 3717 ms, final 4538 ms e pronto 4605 ms. Perfil de uma navegação somou 524 ms em factory Turbopack e 2133 ms em program sem atribuição; não demonstra causa do compilador.

A regressão de foco BODY após Escape foi corrigida em F2. Focos 38/lint/tsc passaram e navegador confirmou foco no FAB mobile/desktop e sino, inclusive cancelamento durante carga do chunk. A integral canônica F2-02 aprovou 155/155 em 43 arquivos/160,11 s, fontes iguais antes/depois. F2-01 reprovada 154/155 foi preservada; sincronização findByRole da gaveta não alterou timeout ou produto. API 546/contrato/tipos continuam inalterados; não repetir pytest por esses deltas web.

### Diagnósticos privados E1–E4, sem promoção

E1, E2, E3 e E4 são snapshots diagnósticos privados, **não fonte canônica nem séries oficiais 80**. Cada calibração teve quatro navegações, não p95; nenhum atingiu 2000 ms. O baseline sanitizado versionado continua a única evidência oficial 80. HTTP/2 no edge teve configuração/TLS/ALPN válidos e TTFB de 70–200 ms em calibração, mas pronto ainda 4–9 s: TTFB não é navegação concluída.

E1 encontrou dados SSR/query presentes e commit→efeito de 1–2 ms, sem evidência para culpar efeito/fetch. Avaliação core próxima de 1 s não explica isoladamente todo atraso; program sem atribuição também não é prova do compilador. ABBA das leituras geométricas não explicou os 4 s e não mudou o driver oficial. E2 tentou referência cliente/promise antecipada; E3 moveu promise/guard para contexto servidor pai. E4 desabilitou cacheComponents/partialPrefetching/cachedNavigations e removeu 12 instant em cópia privada: build 0, checagem auth/SSR/no-store com 4040, mas calibração igualmente falhou. Não promover flags/remoções ou contar esses recortes como produto validado.

### Decisão de encerramento dos experimentos

F2 permanece a fonte canônica. E1–E4 e S1 não foram promovidos. A seleção durável do laboratório foi restaurada para F2 não instrumentado, com smoke HTTPS/identidade/no-store/404 aprovado. Após as provas focais, os laboratórios e clones próprios foram parados, preservando volumes.

S1 compilou e passou 16 testes focados, TypeScript, ESLint dirigido e revisão de segurança do delta. Esses resultados não provam ganho de desempenho. O teste de interação esperou a visibilidade do elemento, instalou o observador e só então executou o clique com auto-wait. Os cliques observados entre 4,9 e 11,7 s **não provam indisponibilidade antes de 2 s**; a interpretação anterior de reprovação dos controles foi retirada. Nenhum benchmark S1 foi concluído. O navegador headless também não emitiu a mudança real de visibilidade esperada na troca de abas; isso é limite do ensaio, não falha demonstrada do produto.

A decisão é preservar a versão funcional validada e concluir regressão, provas focais e documentação, sem adotar uma arquitetura maior sem ganho demonstrado. **RNF05/CA13 permanece não atendido pelo único baseline oficial; a meta não foi relaxada e a Etapa 11 não está concluída.** Os resultados supervisionados e hashes dos cortes estão preservados em [validacao-local.json](evidencias/validacao-local.json). A classificação individual de evidências está na [matriz](../../matriz-rastreabilidade.md); limitações específicas não invalidam automaticamente todos os demais testes.


## Pendências e autoridade

P10 resolvida por delegação expressa Q11-11; não pelo silêncio à pergunta específica. Ajustes sem pendentes atestados pelo dono no chat, sem conector/marcação remota/reexportação. **Itens a marcar remotamente: nenhum novo conhecido neste checkpoint.** P11 continua sem destino/domínio/condições para implantação remota; concluir trabalho local independente antes de obter essa definição concreta. P6 externa, P9 próximo push autorizado; P3/P4 exigem revisão conforme topologia real.

Sem conclusão CA16/18, push, deploy remoto, envio externo, limpar-dev, exclusão de conta real ou alteração dos volumes de desenvolvimento. Laboratório usa recursos sintéticos próprios.

## Publicação para teste do dono

Por pedido explícito posterior, o conteúdo da branch 11 foi integrado à `main` local com merge `--no-ff` e preparado para push. Isso disponibiliza a implementação para o dono testar sem alterar a classificação de aceite: RNF05/CA13 reprovado e CA18 sem integral E2E verde pós-correções. A aplicação ainda não foi implantada na VPS; apenas o Silo e seu backup isolado possuem a autorização e provas específicas descritas acima. Novos achados serão corrigidos em commits posteriores.
