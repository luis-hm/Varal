# Spec — Etapa 11: acabamento e deploy

> **Contém:** escopo e 18 critérios de aceite ainda pendentes.
> **Origem:** RN30/ADR0003, RN01–07/RN21/RN22/RN29/RN31/RN32, RNF02–05/08–10/12, contratos finais 04–10, Q11-1–11 e T11-A–M ratificadas.

Abertura em 16/11/2026 após commit 10 `062258c` e merge local `5cd29ba`, na branch `etapa/11-acabamento-deploy`. Etapas 04–10 concluídas e integradas; a abertura foi documental. O checkpoint posterior registra implementação e testes parciais, sem concluir nenhum CA da 11. O dono delegou decidir/executar as etapas restantes e atestou Ajustes sem pendentes no chat, sem leitura/marcação remota ou reexportação.

## Escopo

Exportação e exclusão RN30, cleanup durável e barreiras nos workers 08–10, preservação de evidências/pins/snapshots de grupo, reautenticação allauth nativa, Perfil Q11-11, PWA/isolamento entre usuários, acessibilidade/movimento/responsividade, RNF05 e laboratório produtivo local. [Decisões](decisoes.md), [plano](plano.md) e [ADR0015](../../arquitetura/adr/0015-exportacao-exclusao-e-prova-local.md) definem os contratos. T11-E está no [protocolo do journal](../../arquitetura/protocolo-journal.md).

Regressão: RF20/CU12 (avisos), RF21/CU10 (solicitações), RF22/CU11 (modo simples), RF23–25 (arquivos) e CU01–08 nas rotas existentes. RN30 não cria CU numerado novo. Mesmas rotas/componentes/dados nas duas larguras; shell muda em 1024 px. Perfil não tem frame dedicado; compor com varal-ui/componentes atuais após leitura real do canvas somente leitura, sem inventar aprovação ou referência.

## Critérios de aceite

Todos permanecem abertos para integração e aceite final; os testes/provas parciais existentes estão no [relatório](relatorio.md), sem equivaler à conclusão dos critérios.

| CA | Dado / Quando / Então | Evidência futura |
| --- | --- | --- |
| CA01 | **Dado** usuário com prova recente, **quando** solicita exportação, **então** 202 cria job próprio idempotente e JSON v1 inclui perfil/pessoal/participações/avisos autorizados, preserva NULL/centavos e exclui credenciais e segredos. | API/fixture final 08–10 |
| CA02 | **Dado** job alheio ou revogação concorrente, **quando** consulta/gera/baixa, **então** alheio recebe 404 e mudança relevante invalida geração; checagem final T11-B autoriza emissão sem snapshot já revogado. | corridas worker/publicação/download e inventário de revisão |
| CA03 | **Dado** documento pessoal válido e autorizado, **quando** baixa JSON pronto, **então** links são assinados nesse momento por 60 s, bucket privado e nenhum arquivo de grupo entra por autoria/upload. | S3 local real, ACL e relógio |
| CA04 | **Dado** mais de 500 itens, retry/falha/expiração, **quando** worker e cleanup retomam, **então** paginação estável não perde/duplica, fencing bloqueia tentativa antiga, TTL absoluto 24 h impede download e limpeza durável remove artefatos sem efeitos financeiros. | 501+ itens, leases/PUT tardio/TTL |
| CA05 | **Dado** único admin ou saída que cria restrita aberta órfã, **quando** confirma exclusão, **então** 409 seguro sem remover dados/sessões/arquivos nem consumir intenção; guardas RN04/RN32 serializam corridas e conjunto administrativo. Após PREPARE só bookkeeping opaco ABORT pode permanecer. | concorrência real e guard-before-effects |
| CA06 | **Dado** conta elegível com reauth nativa <300 s e intenção explícita, **quando** exclui, **então** identidade/pessoal/auth/preferências/sessões/push/exportações perdem capacidade no commit; retry não repete efeitos. Intenção é sessão/ação/CSRF e consumida só no sucesso. | senha/código, fronteira 299/300 s, multi-sessão e replay |
| CA07 | **Dado** contas/pagamentos/históricos/recorrências/evidências legítimos do grupo, **quando** autor exclui usuário, **então** grupo permanece, autoria estruturada NULL/Ex-membro sem snapshot de nome/e-mail, RN21/audiência/pausas preservadas e nenhum acesso novo; sem promessa sobre menções livres/PDF/EXIF. | ACL/grupos/Collector real |
| CA08 | **Dado** solicitação 10 ou reserva aceita com pin, **quando** exclusão disputa cópia/pagamento/undo, **então** origem é desacoplada sem recriação; snapshot/destino autorizado aceito pode concluir com autoria NULL/audiência atual, sem IDs pessoais expostos ou limpeza de fonte necessária. | Q10-8, pins e corridas reais |
| CA09 | **Dado** rollback/S3 indisponível/worker tardio ou restore, **quando** cleanup/reconciliação retomam, **então** limpeza só alcança objetos sem referência/pin/writer; barreiras e journal impedem ressurreição. PREPARE sem prova atual ou ledger de entrega incompleto mantém restore/dispatch bloqueados. | falhas, crashes, journal/checkpoint, restore isolado |
| CA10 | **Dado** navegador compatível em HTTPS local, **quando** instala/abre PWA e permite push por gesto, **então** manifesto/ícones/start_url/escopo funcionam e transporte segue 09; relatar suporte/instalação real e limites, sem inferir provedor externo. | browser/SW/instalação e protocolo local separados |
| CA11 | **Dado** A exibido e ações em voo, **quando** logout offline/troca para B/Voltar/reabre/push tardio, **então** nenhum dado A reaparece; sem cache privado/replay, abas/epoch/bfcache isolados. B autenticado usa seus próprios dados/ações; apenas rebind push aguarda reconciliação. Preservar nonce 10 opaco por dono. | primeiro frame bfcache, storage/SW e respostas/mutações tardias |
| CA12 | **Dado** telas existentes e Perfil Q11-11 em 360/390×844/1440×900, **quando** navega com toque/teclado/leitor, **então** alvos ≥44 px, sem overflow, foco/labels/erros acessíveis, contraste textual ≥4,5:1, ícone+texto e reduced-motion. Perfil usa dados/preferências existentes/exportar/excluir/reauth/sair sem novas funções de identidade. | axe/medição/teclado/capturas e referências Doop reais |
| CA13 | **Dado** build produtivo e fixture Q11-8, **quando** mede pessoal e grupo, 20 frio+20 quente por cenário, **então** p95 (19ª/20) ≤2000 ms em cada série até dados reais e controles prontos; publicar as 80 amostras, erros, LCP/TTFB/ambiente, sem skeleton como aceite. | trace e marco inicio_pronto |
| CA14 | **Dado** laboratório DEBUG=0/TLS/imagens produtivas, **quando** exercita login/SSR/CSRF/redirect/health/migração, **então** cookies seguros e SSR sem loop; só proxy exposto, migração única/falha bloqueante, imagens sem segredos/bindmount. SSR T11-G permite apenas três GETs exatos. | build/config/smoke TLS local; P4 |
| CA15 | **Dado** cadeia de proxy declarada, **quando** forja XFF/Forwarded/host e disputa 11 aceites simultâneos do mesmo IP, **então** só origem confiável conta, RN31 ≤10/IP/h além do usuário, falha 503 segura e logs/trace/artefatos não contêm tokens/URLs assinadas. | P3/P4, IPv4/IPv6 e sentinelas fictícias |
| CA16 | **Dado** storage privado e backups criptografados separados, **quando** restaura/ensaia rollback em volumes e bucket novos, **então** integridade/ACL/URLs 60 s/pins/jobs/journal/ledger são verificados antes de escrita/dispatch; nenhum dado existente é sobrescrito. Publicar retenção e RPO/RTO medidos, limites de checkpoint operacional explícitos. | restore isolado, truncamento/crash e guardas de volumes |
| CA17 | **Dado** SMTP/VAPID efêmeros e receptores locais sem egress, **quando** fila envia/falha/retenta, **então** SMTP TLS real capturado e POST WebPush local com assinatura/criptografia/payload conferidos, política 09/SSRF preservada; protocolo não substitui recepção em navegador. | receptores TLS reais e falhas de transporte |
| CA18 | **Dado** corte final da 11, **quando** avalia fechamento, **então** tipos/OpenAPI determinísticos, test/lint/E2E e CAs têm evidência real, QA/segurança sem bloqueantes; relatório/matriz preservam P10 delegada e P11/P6. Não declarar entrega integral só pela preparação local. | resultados/exit codes e matriz pelo QA |

## Fora de escopo e dependências

P10 resolvida por delegação Q11-11: sem novo ok genérico, sem novas funcionalidades de identidade ou escrita no Doop. P11 permanece dependência concreta de destino/domínio/condições para implantação remota; não escolher VPS/provedores por inferência. P6 é reexportação externa; origem nunca é editada manualmente. P3/P4 serão resolvidas/provadas localmente e revistas conforme topologia remota; P9 continua verificação no próximo push autorizado.

Sem push, envio externo, deploy real, exclusão de conta real do dono ou alteração/remoção/restauração dos volumes existentes. Laboratório não certifica disponibilidade, recepção externa, conformidade jurídica ou resistência a root que retroceda simultaneamente journal/checkpoint/chaves. Não impor novo gate de hardware. Não reintroduzir categoria ou recursos fora do MVP.

## Checkpoint vigente — prova operacional e janela QA

POS final ACL/direitos/objetos e ledger passou, com HMACs válidos ligados à mesma operação/época/fence/watermark e acl_sha256. Backup CURRENT `snapshot.T1fmz1pV` e `lab11-active stop/up` passaram: TLS confiável em ready/entrar e relay 200, web b1c9. D ativo fez login nativo novo e recebeu 404 duas vezes. Segurança adendo 21:46 encerrou os bloqueantes específicos de ACL/direitos/opt-out; não é aprovação global CA16/18.

Ferramenta RPO versionada passou exit 0, reproduzindo26,280613 s / 13 COMMITs do exercício anterior delimitado; não é RTO ACL novo, garantia de RPO ou perda zero. Make test546 API/149 web pré-Providers, web pós-delta152/152 e lint/build permanecem válidos nos seus cortes; app API/websrc não mudou.

E2E01 foi interrompido intencionalmente após 516,884 s, SIGTERM do supervisor/143 e comando-15; wrapper não aprovado, fontes iguais. Artefatos privados em `/tmp/varal11-e2e-partial-01-artifacts`. Foco01 não executou casos: webServer 120 s timeout com Next próprio órfão na 3000, depois encerrado com seu pai; preparo Compose com cwd web inválido não é prova e foi corrigido em up-corrected. Foco02 com worker real1 passou 7/8 em 1,6 min; boleto/Pix passaram e signup ainda falhou em URL5 s. Diagnóstico UI separado mediu POST200 em780 ms, raiz1797 ms e heading1955 ms, sem reproduzir causa. CPU disputada foi observada e não houve locks PG na inspeção posterior; não atribuir causalidade às falhas.

Sincronização auth de teste passou 1/1 mobile 28,3 s aguardando POST200 antes de URL; sem alteração de timeout/produto. Harness E2E/CI worker 1 apenas, sem mudar cota. Benchmark80, calibração e RNF10/WebKit têm GO/janela exclusiva agora, sem resultados antecipados. Worker/beat LAB e API/worker/beat padrão estão pausados; nenhum E2E/build/backup/teste disputa a janela. Desempenho vem antes do E2E final se houver necessidade de otimização.

CA01–18 seguem sem fechamento integrado, especialmente CA13/18; as provas específicas da restauração não aprovam todos os requisitos. [Relatório](relatorio.md) concentra cortes, limites e próximos resultados. Nenhum novo gate de autorização genérica; P11 destino remoto ausente, P6 externa e P9 próximo push autorizado. Sem push/deploy/limpar-dev.
