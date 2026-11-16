# Relatório — Etapa 09 (Notificações)

> **Contém:** entrega concluída, validação final e limites das provas.
> **Origem:** [spec](spec.md), [tarefas](tarefas.md), [Q09-1–9/D09-1–3](decisoes.md), código e relatos frontend/DevOps/QA de 16/11/2026.

**Concluída em 16/11/2026, pronta para commit e merge locais.** Branch `etapa/09-notificacoes`, após commits `b5d516d`/`eadb1c2` e merge local `59e0cc5` da 08. Produto congelado. Suíte API/web, tipos e lint passaram; E2E integral teve duas falhas de seletor legado, corrigido somente nos testes. Suíte Playwright completa final passou sobre serviços locais verificados; QA confirmou cleanup e matriz estáveis. Commit/merge da 09 ainda não executados neste relatório.

## Implementação

Central paginada, resumo, leitura individual/em lote, preferências, transporte e instalação push integrados com tipos gerados. Revogação de aviso comum é terminal e todo acesso/contador/leitura/envio revalida contexto. Todos os EventosPagamento da 07 são consumidos sem corte temporal; RN21/P7 legados anteriores à ativação persistida ficam só na central. P7 novo captura descrição/data/referência mínima no cancelamento; legado sem snapshot usa referência/data/motivo opacos sem ler descrição atual. Sem acesso a conta/PDF pelo aviso P7; P7 resolvida pela central privada RN32 e tratamento seguro de legados, comprovados nos critérios backend/E2E.

Leases/tentativa iniciada são persistidos antes do I/O. Até três tentativas totais somente em falha recuperável comprovada; aceitação desconhecida termina incerta, sem retry cego. Canais e filhos por inscrição/geração são independentes. Rotina composta gera/recupera a 08 antes dos avisos da 09; dispatcher/recuperação mantêm idempotência.

DELETE por id de inscrição foi removido; revogação usa UUID da instalação e cria tombstone mesmo antes de POST atrasado. Sessão HMAC terminal e logout nativo protegem troca/logout; aliases de origem usam fingerprint normalizado, sem transferir vínculo entre usuários ou reescrever caminho/query opacos; o transporte canonicaliza a origem HTTPS/host minúsculo/porta 443 implícita. Novo ciclo exige UUID novo. Endpoint/chaves cifrados e SW sem cache privado; payload externo genérico com rota fixa `/avisos`.

Doop atual foi relido pelo frontend em leitura, mantendo frames draft. Desktop usa gaveta sobre tela corrente no mesmo path/query, com histórico/filtros/rolagem preservados; direto `/avisos` tem Início ao fundo. Mobile usa a rota de avisos. QA comprovou navegação/histórico/nova aba e comparou capturas a 02/D02/04/D06; corrigidos fundo branco D06 e sino D02 antes da integral. Preferências continuam composição delegada, sem alterar canvas.

## Validação final e limites

| Verificação | Resultado informado/comprovado | Limite |
| --- | --- | --- |
| Frontend e suíte web | 111 Vitest verdes na integral, lint e TypeScript verdes | Substitui contagem anterior de 110; não comprova push por provedor público |
| Backend direcionado | 53 verdes: 35 notificações e 18 pagamentos; Ruff e migrações 0001–0005 no desenvolvimento verdes | Não somar à integral |
| Suíte integral/API/contrato | 483 pytest, 111 Vitest, tipos duas vezes determinísticos e lint verdes | Runner integral terminou failed depois, no E2E |
| Focos QA | Inicial 3 passes/5 falhas corrigidas em roteiros/escopos/esperas; foco corrigido 8/8; visual 6/6 e sino 2/2 verdes | Rodadas separadas, não somar à integral; primeira rodada permanece failed |
| E2E integral | 129 passaram, 3 skips previstos, 2 falharam por seletor antigo de H1 oculto em 360 px | Rodada failed, não aprovação integral. Corrigido só seletor; foco 360 px 2/2 passou, sem produto novo |
| Wrapper de revalidação | Runner 51372: lint exit 0; `make e2e` falhou antes do Playwright no acesso HEAD ao GHCR, resposta MIME/proxy malformada de `ghcr.io/astral-sh/uv:0.13.7` | Falha operacional de rebuild, não falha de testes; wrapper permanece failed |
| Playwright completo final | `cd web && npm run e2e`, Node 22.23.5: 131 passaram, 3 skips previstos, 134 casos em 9,4 min; runner 52177 passed/exit 0 | Serviços locais já verificados: API 200 e pywebpush 2.3.0 em API/worker; código/runtime/lock inalterados. Sem rebuild externo, sem mudança de produto/Makefile/TLS/proxy |
| Segurança | Parecer final em leitura sem bloqueantes, após fechar B09-final1; rechecagem do snapshot da central não reabriu achado | Revisor leu snapshot anterior a QA/final visual; não executou suítes ou prova de transporte |
| Decisões | Auditoria sem escolhas pendentes; Q09-1–9/D09-1–3 coerentes com a delegação | Auditoria leu foco inicial reprovado; resultados posteriores são atribuídos à orquestração/QA |
| Segredos/infra | Compose com marcadores comprovou VAPID privada só no worker e Fernet só API/worker | Sem ler/exibir ambiente real; operador Compose ainda pode ler seus próprios segredos |
| Push real local | POST HTTPS real decifrado AES128GCM; JWT VAPID ES256, audience/subject, Host/SNI e pin de IP verificados; sem proxy herdado, segunda resolução ou redirect | Resolvedor/CA/porta locais injetados internamente em rede Docker sem saída externa; não comprova provedor público, navegador push, todas variantes DNS/IPv6 ou entrega física |
| Falhas de transporte | 302 não seguido, 410 descartado, 429 preservou Retry-After; 500/timeout incertos; CA inválida e resposta DNS mista recusadas antes de POST | Prova local dos casos exercitados, não exaustiva |
| E-mail/worker | SMTP local real recebeu conteúdo genérico; destinatário fora de `.invalid` recusado. Beat/dispatcher/worker reais concluíram entrega aceita com uma tentativa em banco isolado | Aceitação SMTP local, sem TLS/autenticação SMTP pública ou pessoa/provedor externo |
| Rotina ordenada | Beat acelerado gerou ocorrência novembro e aviso D−5 no mesmo fluxo; repetições mantiveram uma ocorrência/aviso/rodada | Django com relógio congelado às 08:00 Fortaleza; sem espera real até 07:00. Agenda real 06:59 não devida/07:00 devida, recuperação 300 s, dispatcher 60 s e comprovantes 300 s verificados separadamente |
| Cleanup da prova | Containers, rede, banco/broker e chaves temporários removidos | Serviços/volumes/banco normais não alterados pela fixture; imagem API rebuildada, sem recriar serviços normais |

Provas DevOps usaram rede Docker interna, PostgreSQL/Redis próprios e certificados/chaves efêmeros; não tocaram banco de testes/dev ou provedor externo. Contagens direcionadas/focos não são somadas à integral. Resultados mais recentes da suíte e correções visuais foram informados pelo orquestrador; relatórios de segurança/decisor registram snapshots anteriores sem aprovação integral presumida.

## Segurança, decisões e comparação visual

B09-final1 corrigiu a segunda fase do push: inscrição atual é travada e revalidada até o commit de INICIADA, serializando com revogação; teste concorrente PostgreSQL foi informado verde pelo backend e lido pela segurança. B09-pre1 (ordem de travas no logout), pre2 (aliases de origem) e pre3 (DELETE não causal) permanecem corrigidos. Janela após commit de início antes do I/O continua limitada por payload genérico, sem promessa impossível de recolher envio aceito. Nenhum bloqueante de segurança remanescente no código lido.

D09-2 realiza a causalidade já delegada em Q09-6; D09-3 registra composição/navegação visível sob Q09-9 e delegação vigente. Chamá-los reversíveis não concede autorização autônoma para mudar apresentação ou segurança no futuro. Auditoria decisória não identificou nova pergunta ou gate genérico.

QA comparou capturas Início/pagamento/P7 nas duas larguras a 02/D02/04/D06: gaveta branca e sino circular com borda/ponto vermelho foram corrigidos antes da integral. Histórico/URL/rolagem/foco/nova aba, lote além da página e privacidade RN21/P7 passaram no foco 8/8 com API/worker reais. CSS do sino mede 44 × 44 px; helper de alvo/overflow foi executado na central, não no Início. Não ampliar essa prova para medição de clique do sino em tela real sem evidência adicional.

## Fechamento e continuidade

Resultado final: **483 pytest, 111 Vitest, tipos duas vezes determinísticos, lint verde e suíte Playwright completa com 131 aprovados/3 skips previstos em 9,4 min**. A última execução foi `cd web && npm run e2e` com Node 22.23.5 e API/worker existentes verificados; não houve rebuild externo. O wrapper `make e2e` anterior continua failed por GHCR antes de iniciar navegador. A integral de 129/3/2 permanece failed, com seletor corrigido apenas nos testes e foco 360 px 2/2; resultados de focos não são somados ao final.

QA confirmou runner/processo E2E encerrados, nenhum `next dev` remanescente e matriz final estável. Capturas próprias comparadas a 02/D02/04/D06 cobrem sino/indicador, recentes desktop, central mobile e gaveta branca; eventos sintéticos não reproduzem todo conteúdo ilustrativo dos frames. Segurança final e auditoria decisória sem bloqueantes, com resultados recentes atribuídos ao QA/orquestrador e revisão estática identificada no histórico acima.

P7 resolvida: aviso RN32 privado para o removido, sem acesso à conta/PDF, novo snapshot mínimo e legado opaco sem enriquecimento atual; backend e E2E comprovaram isolamento/visibilidade. Provas de transporte local mantêm os limites descritos: não há homologação pública, recepção push real em navegador, SMTP TLS externo ou espera real até 07:00. Esses limites não são substituídos pelos passes de UI.

Próximo passo autorizado: commits e merge locais da 09 e abertura da 10, registrando hashes somente após execução. Nenhum hash de commit/merge da 09 é antecipado aqui. Sem push/deploy.

Dono atestou Ajustes sem pendentes no chat, sem conector/remarcação ou reexportação. P10 resolvida por delegação expressa para compor Perfil na 11 com guia/componentes e nas duas larguras; pergunta específica sem resposta literal e nenhuma tela 11 implementada aqui. P6 externa e P11/destino pendente permanecem no [PROGRESSO](../../PROGRESSO.md). P7 resolvida no fechamento da 09. Nenhum item a marcar como “ — feito na etapa 09” identificado pela declaração vigente de fechamento. Sem push/deploy. O resultado final não afirma que `make e2e` passou: a suíte completa foi executada diretamente em serviços existentes verificados após falha operacional do wrapper.
