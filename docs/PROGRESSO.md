# Progresso

> **Contém:** o estado de cada etapa, as decisões (pendentes e resolvidas) e o log de mudanças (memória entre sessões).
> **Origem:** mantido pelo agente `varal-docs` ao fim de cada etapa; toda sessão nova começa lendo este arquivo.

## Etapas

| Nº | Etapa | Status | Branch | Concluída em | Relatório |
| --- | --- | --- | --- | --- | --- |
| 00 | Fundação | concluída | `etapa/00-fundacao` | 12/11/2026 | [relatorio](etapas/00-fundacao/relatorio.md) |
| 01 | Design system no código | concluída | `etapa/01-design-system` | 12/11/2026 | [relatorio](etapas/01-design-system/relatorio.md) |
| 02 | Autenticação | concluída | `etapa/02-autenticacao` | 13/11/2026 | [relatorio](etapas/02-autenticacao/relatorio.md) |
| 03 | Espaços e grupos | concluída | `etapa/03-espacos-grupos` | 15/11/2026 | [relatorio](etapas/03-espacos-grupos/relatorio.md) |
| 04 | Contas (núcleo) | concluída e integrada localmente à main (`fe48cbe`) | `etapa/04-contas` | 15/11/2026 (inicial); revisão 16/11/2026 | [relatorio](etapas/04-contas/relatorio.md) |
| 05 | Boleto e Pix | concluída e integrada localmente à main (`e5c94e3`) | `etapa/05-boleto-pix` | 16/11/2026 | [relatorio](etapas/05-boleto-pix/relatorio.md) |
| 06 | PDF do boleto | concluída e integrada localmente à main (`b21bd83`) | `etapa/06-pdf-boleto` | 16/11/2026 | [relatorio](etapas/06-pdf-boleto/relatorio.md) |
| 07 | Pagamento | concluída e integrada localmente à main (`2599655`) | `etapa/07-pagamento` | 16/11/2026 | [relatorio](etapas/07-pagamento/relatorio.md) |
| 08 | Recorrência e agendador | concluída e integrada localmente à main (`59e0cc5`) | `etapa/08-recorrencia-agendador` | 16/11/2026 | [relatorio](etapas/08-recorrencia-agendador/relatorio.md) |
| 09 | Notificações | concluída e integrada localmente à main (`56337ed`) | `etapa/09-notificacoes` | 16/11/2026 | [relatorio](etapas/09-notificacoes/relatorio.md) |
| 10 | Solicitação e modo simples | concluída e integrada localmente à main (`5cd29ba`) | `etapa/10-solicitacao-modo-simples` | 16/11/2026 | [relatório](etapas/10-solicitacao-modo-simples/relatorio.md) |
| 11 | Acabamento e deploy | HMG publicado; CA13/18 e implantação final em produção pendentes | `etapa/11-acabamento-deploy` | — | [relatório](etapas/11-acabamento-deploy/relatorio.md) |
| 12 | Correções do teste inicial | em andamento: COR-01–09/11/12 feitos; COR-10 aguarda ok do dono; resto no [handoff](etapas/12-correcoes-teste/handoff-codex.md) | `etapa/12-correcoes-teste` | — | [relatório parcial](etapas/12-correcoes-teste/relatorio.md) |

## Decisões

Divergências entre as fontes da verdade ou bloqueios. Não escolher sozinho: perguntar ao dono do projeto.
Respostas vêm do documento "Varal — Ajustes" (Claude Docs `ce521944-15d6-44a5-b70c-f0790e03de41`).

Na continuidade iniciada em 15/11/2026, o dono delegou expressamente ao Codex resolver as decisões e executar as etapas restantes. As escolhas dessa execução são registradas como **decisões delegadas**, sem inventar respostas literais do dono ou leituras pelo conector indisponível.

### Pendentes

| # | Assunto | Bloqueia |
| --- | --- | --- |
| P3 | Configurar a cadeia de proxies confiáveis e testar spoofing antes do deploy. Allauth mantém `trusted_proxy_count=0` enquanto a API 8000 está exposta; limite por IP vê o Next como origem. Ativar também o limite de aceite de convite por IP (RN31). | Deploy da Etapa 11 |
| P4 | Produção: com `DJANGO_DEBUG=0` a API liga `SECURE_SSL_REDIRECT`, e o Next consulta `/api/me/` pela rede interna em HTTP sem `X-Forwarded-Proto`; provável redirecionamento para https e falha das páginas protegidas. Definir como o Next fala com a API em produção (cabeçalho, exceção de rota ou proxy). Omitir também o token de convite do access log do proxy/servidor de produção (RN31). | Deploy da Etapa 11 |
| P6 | Claude Code deve reexportar a especificação da origem rev 50 (sem categoria no CU05 e no modelo) e conferir os derivados/ADR 0005. O Codex não faz essa reexportação nem edita a origem à mão; a cópia permanece defasada. O ADR 0005 já aprovado rege a implementação sem categoria. | Pendência administrativa externa; continuidade sem categoria pelo ADR 0005 |
| P9 | Confirmar que o CI dispara no próximo push: `gh run list`; se nada aparecer, `gh workflow run web.yml --ref main`. Causa provável e correção em "CI mudo" (Resolvidas). | Nada (verificação) |
| P11 | Silo instalado na VPS/Coolify, console `silo-admin.codehub.systems`, S3 `arquivos.codehub.systems`, backup local diário e recuperação isolada comprovados. HMG publicado em `hmgvaral.codehub.systems`/develop, com banco/volumes/bucket próprios e18 verificações HTTP aprovadas. Produção/main preparada e parada; implantação final e recuperação integrada de PostgreSQL/journal continuam pendentes. Cópia local sem criptografia adicional e disco único não aprovam CA16. Não solicitar segredos no chat. | Produção e recuperação integrada da aplicação na11; HMG autorizado está disponível para testes |

### Resolvidas

| # | Pergunta | Resposta | Onde |
| --- | --- | --- | --- |
| D1 | Altura do botão: 52 ou 48 px? | **52 px.** O CSS do Button no Doop já era 52 px; a descrição foi corrigida. | Etapa 01 |
| D2 | Como aparece uma conta cancelada? | StatusBadge ganhou `cancelada` (ícone `fechar`, texto "Cancelada", fundo branco, borda `--color-line`, texto `--color-ink-muted`). Sai do Início, das listas padrão, dos totais e dos lembretes; só no filtro "Canceladas" e no histórico; no card, valor riscado e opacidade reduzida. | Etapa 01 (selo), 04 (filtro e regras); [design](design/README.md#conta-cancelada-d2) |
| D3 | Desktop entra no MVP? | **Sim** (seção 12 da especificação reexportada). Shell responsivo (SideNav, NavItem, troca em 1024px) na Etapa 01; cada tela nas duas versões na mesma etapa da mobile. | [design](design/README.md#regra-responsiva), [etapas](etapas/README.md) |
| D4 | Qual armazenamento S3? | `pgsty/silo` com tag fixa, só local; código via `django-storages` com config no `.env`; produção na Etapa 11. Etapa 06 desbloqueada. | [ADR 0002](arquitetura/adr/0002-armazenamento-s3-local.md) |
| D5 | Onde entra o RNF04 (LGPD)? | Etapa 11, como regra nova **RN30** (exportar JSON; excluir conta com autor "Ex-membro" nos grupos). Tela Perfil não existe no Doop: parar e pedir. | [ADR 0003](arquitetura/adr/0003-rn30-exportar-e-excluir-dados.md) |
| D6 | Merge da Etapa 00 na main? | Merge local feito agora (`--no-ff`). Daqui em diante, rodar `/etapa` aprova a etapa anterior e faz o merge local dela antes da branch nova. Push só com pedido. | `.claude/commands/etapa.md` |
| P1 | Verificar execução do armazenamento local | Resolvida em 15/11/2026 pelo Codex: `pgsty/silo:RELEASE.2026-11-12T00-00-00Z` iniciado; healthcheck 200 pela API na rede Compose e autenticação `mc admin info` com as variáveis do ambiente, sem exibir credenciais. A Etapa 06 também comprovou upload/download, Celery, limpeza e URLs assinadas reais em 16/11/2026. | Pré-verificação da Etapa 06 |
| P2 | Validação completa da Etapa 01 | Resolvida em 13/11/2026: Docker disponível; credenciais do `.env` local alinhadas às já existentes no volume, sem alterar usuários nem dados do banco. `make test`: API 3/3 e web 29/29; `make lint` verde. | Etapa 01, CA17 |
| P5 | Limite de cadastro do allauth derrubava o E2E (~40 contas do mesmo IP contra 20/min) | Resolvida em 15/11/2026: `ACCOUNT_RATE_LIMIT_SIGNUP` vira `ACCOUNT_RATE_LIMITS["signup"]` só quando definida (o allauth mescla aos padrões; os outros limites seguem). `make e2e` e o job `e2e` do `web.yml` usam `1000/m/ip`; fora deles vale 20/m/ip. Saiu o retry em 429 do E2E. | Etapa 04; [stack](arquitetura/stack.md#variáveis-de-ambiente) |
| P8 | 429 do allauth no primeiro cadastro do `make e2e` com a API fria | Resolvida em 15/11/2026: os dois workers disputavam a trava do limite do allauth (espera de 1 s) enquanto o servidor de dev ainda importava módulos. O `globalSetup` do Playwright (`web/e2e/global-setup.ts`) faz um cadastro sozinho antes dos workers. Duas medições de geometria passam a esperar `modal-pop`/`sheet-up` terminarem. E2E final a frio: 74 verdes, sem 429. | Etapa 04 |
| Node local | Node local v20; o projeto pede 22+ | Resolvida em 15/11/2026: Node 22.23.5 local. `web/.nvmrc` (lido pelo CI) e `engines`; o `make` para com Node < 22 (612aa34). | [stack](arquitetura/stack.md) |
| P7 | Aviso ao removido das restritas canceladas pela RN32 | Resolvida na Etapa 09: central privada própria, snapshot novo mínimo e legado opaco/data/referência/motivo sem enriquecimento atual ou link à conta/PDF. Isolamento e entrega central comprovados por backend e E2E final; sem promessa de entrega externa física. | [Relatório 09](etapas/09-notificacoes/relatorio.md), ADR 0006/0013 |
| P10 | Definição da tela Perfil sem frame dedicado no Doop | Resolvida por delegação expressa do dono para tomar decisões e executar todas as etapas restantes. A pergunta específica continua sem resposta literal; a autorização vem da delegação posterior ao ADR 0003, não do silêncio. Na 11, compor dados próprios/preferências/exportar/excluir/sair com `varal-ui` e componentes existentes, nas duas larguras; registrar superação limitada do novo gate de tela, preservando RN30 e canvas somente leitura. Nenhuma tela Perfil implementada por esta decisão. | Reavaliação durante a 09; Q11-11/ADR0015 ratificados na abertura da 11 |
| CI mudo | O CI não disparou no GitHub no push inicial | Causa provável (inferência; o GitHub não mostra o motivo): o push inicial levou todas as branches a um repositório vazio, como branches novas com commit raiz sem pai, e o filtro `paths` não casou nada; o segundo push só mexia em LICENSE, fora do filtro. Correção: `workflow_dispatch` em `api.yml` e `web.yml` (612aa34). Verificação no próximo push: P9. | [stack](arquitetura/stack.md#decisões-de-implementação) |
| Banco de dev | Dados de teste antigos no banco de dev | Resolvida em 15/11/2026: `make limpar-dev` existe, com prévia e confirmação; não foi executado, o dono roda quando quiser (a prévia apagaria 5 grupos de teste, 302 grupos sem membros e 858 usuários de teste). | [stack](arquitetura/stack.md#decisões-de-implementação) |

## Log

Ordem cronológica inversa.

### 18/11/2026 — Etapa 12: correções do teste inicial (parcial)

- Casa vira categoria com ícone ([ADR 0016](arquitetura/adr/0016-categorias-com-icone.md)); Contas sem mês obrigatório e pessoal por padrão; "Sem categoria" visível; tela da categoria; Nova conta no destino da tela; Perfil redesenhado; sessão não pede login ao voltar à aba; referrer do login Google corrigido.
- Commits `c806774`, `7aa9ad1`, `1f7e9ba`, `905a43a`. API e web verdes; E2E não rodado.
- Permissões por categoria propostas no [ADR 0017](arquitetura/adr/0017-permissoes-por-categoria.md), aguardando o dono. Restante no [handoff ao Codex](etapas/12-correcoes-teste/handoff-codex.md).

### 17/11/2026 — COR-12: checklist Google Cloud documentado

- Acrescentado ao [item de correções do login Google](produto/correcoes-teste-inicial-2026-11-16.md#configuração-google-cloud-a-executar-pelo-dono) o preenchimento de Branding, público-alvo, escopos mínimos e cliente OAuth, com callbacks exatos HMG/local/produção, responsabilidades do dono e validação futura.
- Capturas do Console registradas como contexto, sem comprovar configuração salva. Checklist pendente, correção CSRF ainda necessária e produção parada; atualização documental sem alterar código, credenciais, Console ou deploy.

### 17/11/2026 — COR-12: dois bloqueios do login Google reproduzidos

- Captura do dono incorporada ao [backlog](produto/correcoes-teste-inicial-2026-11-16.md#11-cor-12--login-google-bloqueado-por-csrf). Browser anônimo HMG reproduziu403 com cookie/campo CSRF iguais, `Origin:null` e semReferer; entrada recebe `no-referrer` de Next e edge. Matriz HTTP confirma origem própria302/nula403; nove asserts de middleware isolado aprovados. [Evidências e probes](produto/evidencias/google-csrf-2026-11-17/README.md).
- Contrafactual alterando somente a meta referrer do DOM para `strict-origin` removeu403 e levou à página Google com `redirect_uri_mismatch`. Não foi medido302 intermediário pelo browser nem inspecionado o Console. URI esperada HMG: `https://hmgvaral.codehub.systems/accounts/google/login/callback/`.
- Correção futura: alinhar política escopada de entrada/cadastro nas duas camadas, preservar proteção de URLs sensíveis e validar cadastro do retorno no cliente OAuth correto. Não aceitar origem nula/desligarCSRF. Acrescentar regressão do formulário real; os testes atuais não cobrem esse caminho sob os headers produtivos.
- Entrega somente de análise/documentação, sem autenticar conta Google, alterar código/configuração/deploy, push ou encerrar CA. COR-01–11 e alterações paralelas preservadas. Fluxo completo segue sem validação.

### 17/11/2026 — HMG publicado no Coolify; produção preparada e parada

- Projeto Varal com `hmgvaral`/develop e `varal`/main configurados; branchdevelop criada via gh e infraestrutura publicada nas duas branches. Deploy HMG `hpdxo0th1prppjqtkdcekijy` terminou no SHA `3395d75` pelo webhook HMAC real, com commit explícito. HTTPS válido em entrar/health/ready200 e HTTP redirecionando paraHTTPS. [Runbook](arquitetura/coolify-varal.md), [evidência](etapas/11-acabamento-deploy/evidencias/coolify-hmg-2026-11-17.json).
- [Smoke HTTP real](etapas/11-acabamento-deploy/evidencias/coolify-hmg-smoke-2026-11-17.json):18 verificações aprovadas; cadastro/login/CSRF/cookies/SSR/isolamento; PDF1433bytes enviado, processado pelo Celery e baixado com SHA idêntico por assinatura, anônimo403/alheio404; dois usuários sintéticos excluídos204/sessão401. Sem browser visual, Google real, SMTP/push, medição de desempenho ou expiração cronometrada. Limpeza física S3 assíncrona não foi polled.
- Corrigidas colisão de IPs baixos e temporários Nginx fora de/tmp; filesystem somente leitura preservado. Aliases privados por stack evitaram ambiguidade de nomes; não foi capturada resolução DNS antiga para afirmar causa conclusiva do503 anterior. Sete imagens,11 verificações init, cinco grupos de proxy/DNS e cinco grupos HTTP locais aprovados. Coolify raw agregado observado `running:unknown`; saúde funcional comprovada pelas rotas/operações, sem alegar agregadohealthy.
- Workflows com CI antes do webhook, segredos HMAC exclusivos, ambientes GitHub restritos às próprias branches. Produção: gatefalse, auto-deployfalse, execução porpush44007795245skipped e histórico de implantação vazio. Tokens de API fornecidos tinham leitura cruzada entre recursos e ficaram fora doActions. IA não ativada. SMTP indisponível/push desativado; Google requer origem/callback HMG no Console do provedor.
- CI não integralmente verde: API inicial aprovada; web/CI reutilizado apresentaram falhas em verificações de navegador/HTTP produtivo e o deploy automático foi bloqueado. Não afrouxar testes nem declarar CA13/16/18 ou etapa11 concluídas. Produção não iniciada. Alterações paralelas de backlog/documentação preservadas.

### 17/11/2026 — Categorias com permissões e navegação de contas solicitadas

- Dono esclareceu que **categoria substitui a atual casa dentro do grupo**, e pediu que o admin configure quem pode fazer cada ação por categoria. DEC-01 do [backlog](produto/correcoes-teste-inicial-2026-11-16.md) deixa de estar aberta; a proposta inicial de eliminar o segundo nível foi superada.
- Acrescentadas COR-10 (permissões por categoria) e COR-11 (Grupos → grupo → categoria → contas → detalhe/pagamento), com telas de consulta/administração, revisão das telas existentes, impacto backend/frontend e aceites futuros. Matriz, defaults, precedência com restritas/papéis e tratamento de sem categoria ainda precisam ser detalhados.
- Atualização documental, sem implementar permissões/telas, migrar dados, alterar o Doop ou executar novos testes de produto. Evidências anteriores de COR-07 preservadas; nenhuma CA da Etapa 11 encerrada. Nova política exige ADR e conciliação das fontes na preparação da implementação.

### 17/11/2026 — Diagnóstico de “Sem casa” e ampliação do backlog visual

- Complementado o [documento de correções](produto/correcoes-teste-inicial-2026-11-16.md) com COR-07 (contas sem casa/filtros), COR-08 (design e código do frontend) e COR-09 (redesenho de Perfil funcional). Incorporada a correção do dono: consultar suas contas a pagar nos grupos já existe; preservar e melhorar o acesso.
- Reprodução real dos endpoints com fixtures sintéticas e rollback: conta sem casa grava com 201 e aparece no grupo/filtro do próprio pagador. Resumo `por_casa` omite a parcela sem casa; filtro explícito de casa nula não existe; mês vazio retorna opções vazias. Modo simples inclui abertas de outros meses. Nenhuma conta real inspecionada ou modificada.
- Componentes reais em Vitest reproduziram três lacunas duas vezes: grupo sem caminho local para Contas, card que abre edição em vez de listagem e filtro ativo cujos controles desaparecem no vazio. **3 falhas esperadas, exit 1**, sem correção de produto. Script, fixture fora da suíte e resultados em [evidências](produto/evidencias/sem-casa-2026-11-17/README.md).
- Apenas documentação/artefatos de diagnóstico; nenhum novo layout implementado, teste integral, alteração do Doop ou leitura/marcação remota de Ajustes. Estado e aceites da Etapa 11 preservados. Próximo trabalho deve corrigir as causas registradas e entregar revisão visual/código em conjunto; retorno à aba ainda exige reprodução própria.

### 16/11/2026 — Relato de teste: sessão, contas e organização em grupos

- A pedido do dono, criado [documento de correções do teste inicial](produto/correcoes-teste-inicial-2026-11-16.md), com COR-01–06, comportamento atual verificado no código, direção solicitada, propostas, decisões abertas e aceites futuros.
- Capturas mostram carregamento/verificação de sessão após voltar à aba. Guarda atual oculta conteúdo, revalida identidade e recarrega; causa completa do travamento ainda não reproduzida. Contas impõe mês atual na tela e na API. Cadastro já condiciona pagador/visibilidade ao grupo, mas prioriza o espaço atual.
- Pedido registrado: todos os períodos com filtros combináveis; Contas pessoal por padrão; grupos livres inclusive individuais; destino do cadastro explícito. Relação grupo/categoria/casa, dados existentes e alcance de visibilidade/pagamento permanecem decisões abertas. ADR 0005 e permissões atuais não foram revogados.
- Trabalho somente documental, sem execução de testes, mudança de produto, leitura/marcação remota de Ajustes ou alteração do Doop. Próxima preparação de implementação deve obter o texto atual de Ajustes e conciliar as fontes. Etapa 11 e seus aceites permanecem no estado anterior; alterações de HMG/deploy já presentes foram preservadas.

### 16/11/2026 — Preparação de HMG/develop e produção/main no Coolify

- Novo pedido explícito do dono autoriza criar branch `develop` via `gh`, configurar projeto Varal com dois recursos e iniciar **somente homologação**. Domínios confirmados: `hmgvaral.codehub.systems` e `varal.codehub.systems`. `develop` criada da main `7eb3e56`; projeto e aplicações criados, sem deploy neste checkpoint.
- Recursos `hmgvaral`/develop e `varal`/main têm segredos, roles de banco e volumes separados. Bucket privado HMG `varal-hmg-arquivos` com credencial exclusiva testada em PUT/GET/DELETE sintético e negações403 de ACL/bucket de produção. Silo existente preservado.
- [Runbook](arquitetura/coolify-varal.md), [Compose raw](../infra/deploy/compose.coolify.yml) e workflows foram preparados. Webhooks HMAC exclusivos por aplicação/ambiente GitHub, SHA explícito e CI API/web antes do disparo. Produção: auto-deploy falso, `VARAL_PROD_DEPLOY_ENABLED=false`, nenhum deploy. Nenhum token administrativo no GitHub Actions, nenhuma IA ativada.
- Raw Compose confirmado no Coolify para impedir injeção global de env_file; build serial por aplicação, image scanning preservado. Sete testes offline do assinador, sete builds seriais e11 testes isolados de inicialização passaram. Confiança no proxy via hostname Docker literal evita acesso ao Docker socket; Docker deve recusar colisões de rede sem remover recursos existentes. Aguardam teste final desse DNS, primeira implantação e smoke. Sem SMTP configurado, e-mail falha controladamente; push desativado. CI integral/CA13/18 continuam pendentes.

### 16/11/2026 — Planejamento de IA para leitura de boletos

- A pedido do dono, documentados [plano de IA para boletos](arquitetura/ia-boletos.md) e [pesquisa Gemini em fontes oficiais](arquitetura/pesquisa-gemini-boletos.md). Proposta híbrida: parser local como autoridade, IA como complemento de extração, conferência humana e melhoria por erros revisados convertidos em fixtures sintéticas/regressões.
- Dono informou `API_KEY_GOOGLE` no ambiente; valor não foi inspecionado nem enviado. Nenhuma integração ativada, alteração de configuração ou envio de PDF ao provedor. Gratuito proposto somente com documentos fictícios; regime para dados reais, extensão visual da RN28, feedback/retenção e orçamento precisam de decisão antes da implementação. Não há aprendizado automático entre chamadas.
- Planejamento não modifica a spec original ou as regras05/06 e não fecha a11; CA13/18 e implantação do app continuam pendentes. Nenhum teste de IA foi declarado executado.

### 16/11/2026 — Publicação da implementação na `main` para testes do dono

- Pedido explícito posterior do dono autorizou integrar e enviar todo o trabalho local à `main`, mesmo com os aceites finais da Etapa 11 ainda abertos. Merge `--no-ff` feito após commits locais da implementação e do Silo. A implementação está disponível para novo teste; bug futuro será tratado em correção posterior.
- Resultados conhecidos antes do envio: API546, web156/44, lint e tipos verdes; E2E integral135 aprovados/8 falhas/3 skips, seguido de retestes direcionados dos cenários corrigidos; benchmark oficial RNF05 reprovado. Não declarar CA13/18 ou implantação do app concluídos. CI do novo push será verificado conforme P9.

### 16/11/2026 — Backup local do Silo e recuperação isolada comprovados

- A pedido expresso do dono, configurado backup nativo do volume `varal-silo-data` no Coolify: diariamente às03h de Fortaleza (`0 6 * * *`/UTC), com pausa/retomada dos containers que usam o volume, retenção de até7 cópias/7dias e limite configurado10GiB, timeout600s. Application `silo-backups-nao-implantar` é somente referência administrativa, nunca implantada; não excluir seu volume/storage/schedule para organizar o painel.
- Arquivo real `volume-varal-silo-data-1794878142.tar.gz` (15772B/SHA256c292039be0166505f1ebc6349b6cdd39290f4302f7665f69858f4e6d807c9b21) restaurado no volume NOVO `varal-silo-restore-20261116-6923a0e5`. Init validou hash/CRC/paths/destino vazio; clone mesma imagem iniciou sem rede ou portas públicas. Fonte não foi substituída. Logs confirmaram parada/retomada do primário no primeiro backup; não são garantia de RTO.
- PDF/PNG sintéticos recuperados com SHA/tamanho/MIME/cache/metadados iguais; runtime key recuperada autenticou, anônimo403 e ACL/outro bucket403. Oito execuções de tarefas de validação tiveram sucesso pela API; não confundir com status interno do backup de volume, cuja consulta pública não existe. Origem manteve os hashes; removidos somente os dois objetos próprios, bucket ativo0=baseline0.
- Segundo arquivo atual sem objetos de teste confirmado (17587B/SHA256b33ce1dad73a810708bfbab2d728e3ccf5296bcdecfadb7a7de43dc3dbb03b5b), preservando o primeiro. Diretório0700 permaneceu privado na segunda execução; os dois arquivos foram restritos a0600. Backups nativos futuros podem ser0644 dentro desse diretório0700: verificar novamente se a pasta for recriada. Arquivos não têm criptografia adicional.
- [Runbook](arquitetura/silo-backup-recuperacao.md), [agenda](../infra/silo/backup-schedule.json), [template](../infra/silo/compose.restore.yml) e [evidência sanitizada](etapas/11-acabamento-deploy/evidencias/silo-backup-recuperacao-2026-11-16.json). Credenciais administrativas de recuperação guardadas somente no `.env` privado como `SILO_BACKUP_ADMIN_*`, separadas de runtime. Helpers temporários confirmados `exited`, primário `running:healthy` e HTTPS200; volume original e arquivos de backup preservados. Sem deploy da aplicação, alteração do desenvolvimento, push ou encerramento de CA16/18. Disco/VPS únicos e integração futura PostgreSQL/journal permanecem limites.

### 16/11/2026 — Etapa 11: estabilização registrada, aceite integral ainda pendente

- Corrigido defeito real de hidratação em movimento reduzido: contador tinha valor inicial diferente no servidor e navegador. Agora ambos começam em zero; próximo RAF conclui sem animação quando solicitado. Teste SSR/hidratação e E2E com detecção de erro passaram. Integral web final **156/156 em 44 arquivos, 156 s, exit 0**, fontes estáveis; API **546** permanece válida sem delta.
- Integral E2E **135 aprovados/8 falhas/3 skips** preservada. Corrigidos seis cenários de teste (login real pós-logout, Perfil implementado, seletores e sincronização). Foco agrupado **10 aprovados/1 falha/1 skip**; geometria posterior levou à descoberta e correção da hidratação; reteste final **1/1 sem erro de hidratação**. Não houve nova integral E2E após essas correções; não chamar o wrapper de verde.
- Provas reais RN30/RN31 aprovadas: exportação idempotente/categorias/NULL/centavos, PDF/comprovante pessoal com hash e expiração real, arquivos de grupo excluídos da exportação, DELETE204 preservando grupo/ACL e journal verificado; onze HTTP concorrentes de convite produziram dez aceites e um429. Evidências sanitizadas em `etapas/11-acabamento-deploy/evidencias/`.
- LAB/QA/clones próprios parados com volumes preservados. Ambiente padrão restaurado: API/worker/beat ativos, Redis normal, health200; Redis E2E parado. Imagem F2 do LAB antecede o fix final do contador e não equivale à fonte final.
- **Etapa 11 continua aberta:** RNF05/CA13 não atendido pelo baseline, CA18 sem integral E2E final verde e implantação da aplicação ainda pendente. Nenhum experimento E1–E4/S1 foi promovido, nenhum alvo relaxado. Commit local de progresso, sem merge/push. Alterações paralelas de Silo preservadas fora deste commit.

### 16/11/2026 — Silo remoto no Coolify autorizado e instalado

- Dono escolheu explicitamente Silo no disco da VPS atual e autorizou o Codex a concluir a instalação pelo MCP com o token de `infra/.env`. A autorização é específica do armazenamento: não houve deploy do app Varal, mudança do S3 de desenvolvimento, push ou acesso aos dados do dono.
- Projeto Silo/production, serviço `wtowjxrirnltc2qcfwrlr5zp`; imagem fixada `pgsty/silo:RELEASE.2026-11-12T00-00-00Z`, volume externo `varal-silo-data:/data` preservado. Ambos os hosts reproduziram503/certificado padrão com container saudável. API de URLs/reparse não gerou rotas; labels Traefik explícitos e rede `coolify` corrigiram o acesso, sem alterar/reiniciar o proxy global ou outros serviços. Configuração exclui access logs/tracing apenas dos quatro routers Silo.
- Console/ready HTTPS200 com TLS válido; login204/session200 e cookie Secure/HttpOnly aprovados. Bucket privado `varal-arquivos`; chave restrita lista somente esse bucket e recebe403 para ACL/política e objeto fora dele. Valores efetivos salvos sob `SILO_PROD_*` no `.env` não versionado; nomes novos não são consumidos automaticamente pelo Django e não mudam o desenvolvimento.
- I/O real com arquivos sintéticos nos prefixos boleto/comprovante passou: PUT/GET/SHA256, anônimo403, assinatura60s válida e rejeitada403 após prazo, SHA preservado após reinício confirmado nos logs MCP. Somente os dois objetos próprios de teste foram removidos. [Evidência sanitizada](etapas/11-acabamento-deploy/evidencias/silo-coolify-2026-11-16.json), [runbook](arquitetura/silo-coolify.md) e [Compose](../infra/silo/compose.coolify.yml) registram o recorte.
- Revisão de segurança somente leitura sem bloqueantes identificados para esta instalação inicial; não é aprovação global da etapa. Disco/VPS únicos, backup automático/restauração remotos ausentes e `preparar_storage` administrativo separado continuam limites explícitos. Nenhum CA da11 foi encerrado por esta instalação; P11 foi refinada, P6/P9 preservadas.

### 16/11/2026 — Etapa 11: encerramento dos experimentos e regressão final

- Após nova orientação do dono para encerrar o ciclo, a fonte F2 foi mantida. S1 não foi promovido: os cliques tardios do driver não demonstram que os controles estavam indisponíveis antes de 2 s; a inferência foi retirada. Não houve benchmark S1. Nenhuma meta foi reduzida.
- Laboratório restaurado para F2 não instrumentado, imagem `326229fbc146bd1ed717a32c77524ecf434389b2ecaa11b66c65826be26e0eb5`, seleção ativa persistida. Smoke HTTPS/h2, login/identidade, resumo, SSR privado sem cache e 404 passou. Volumes e primário restaurado preservados.
- Regressão final `make e2e` iniciada sobre fonte F2; provas focais RN30/RN31 usam apenas o laboratório sintético separado. O resultado final será registrado ao concluir. Testes API 546, web 155 e lint já aprovados nos cortes documentados; metadados e hashes duráveis em `etapas/11-acabamento-deploy/evidencias/validacao-local.json`.
- RNF05/CA13 continua não atendido pelo baseline oficial. A Etapa 11 não será apresentada como concluída com esse requisito pendente. P11 exige destino concreto para implantação; P6/P9 continuam externos. Sem push ou merge da etapa incompleta.

### 16/11/2026 — Etapa 11: S1 congelado para prova no navegador

- Fonte canônica F2 preservada: integral web 155/155 e `make lint` exit 0 (`/tmp/varal11-lint-f2.log`). API e contrato não mudaram; continua válida a integral de 546 pytest e a geração determinística de tipos.
- S1 privado congelado passou 16 testes focados, TypeScript e ESLint dirigido. Segurança não identificou bloqueantes no delta, incluindo o reforço final de owner/cookie/visibilidade antes de refresh. Os symlinks temporários de dependências/build foram removidos do contexto.
- Build separado em andamento, com configuração F2 e sem instrumentação E1–E4; não há ainda resultado de navegador, calibração ou promoção S1. QA verificará texto efetivamente visível do contador Shadow DOM, ações reais, atualizações e isolamento. Mantidos carga, animação de 1200 ms, marco completo e limite de 2000 ms. Baseline oficial reprovado permanece preservado; CA13/18 e E2E integral seguem abertos.
- Ajustes sem pendentes conforme atestado do dono; sem acesso/marcação remota ou reexportação. P11/P6/P9 preservados. Sem push, deploy remoto ou limpeza de dados de desenvolvimento.

### 16/11/2026 — Etapa 11: F2 integral aprovada; S1 arquitetural privado em implementação

- F2 canônica web02 passou **155/155, 43 arquivos, 160,11 s, exit 0**, fonte antes/depois igual 7ea2412597c5f15bf58ba65c694b800808e7891f9997f6dc9e3aa6ae8e532eca, artefatos `/tmp/varal11-final-web-f2-02/{status.json,log}`. F2-01failed 154/155 preservada; sincronização findByRole na gaveta sem mudar timeout/produto. API 546/tipos permanecem sem alteração, lint geral pré-F2 e focos 38/lint/tsc aprovados.
- E1/E2/E3/E4 são snapshots privados diagnósticos, não canônicos/nem 80: nenhuma calibração 4 atingiu 2 s, não são p95. HTTP/2/TLS válido e TTFB 70–200 ms não evitaram pronto 4–9 s. Dados SSR/query presentes, commit→efeito 1–2 ms/coreeval próximo 1 s/ABBA geometria não explicaram sozinhos atraso. E2 promise cedo, E3 contexto/promise servidor e E4 flags cache/prefetch off+12 instant removidos build 0/authSSRNoStore4040 falharam calibração. Baseline80 versionado permanece único oficial e reprovado.
- Runtime LAB atual **E4 instrumentado diagnóstico**: restaurar não instrumentado/candidato validado antes do aceite, sem promover flags/remoções por inferência. Workers/default pausados; E2E final e nova 80 não executados.
- S1 é o único candidato arquitetural novo em implementação privada sobre F2 (`/tmp/varal11-performance-architecture.md`, Terra só/tmp): Home 100/99 atenção completas SSR/anchors nativos/pequenas ilhas, Counter ShadowDOM progressivo 1200 ms reais sem reset React, marco exige controles+avisos+final+2RAF e refresh após mutação. Sem build/calibração/ganho/promoção alegados. Manter no-store/owner/carga/target/motion/guards; se controles>2 s, rejeitar snapshot, não manipular marco.
- Próxima ferramenta retoma pelo blueprint, congela snapshot coordenado QA/DevOps e valida antes de nova 80. CA13/18/E2E final abertos, P11 remoto/P6/P9 preservados. Sem push/deploy/limpar-dev; somente relatório e este checkpoint atualizados.


### 16/11/2026 — Etapa 11: foco corrigido; carregamento inicial ainda em diagnóstico

- F2 passou 38 testes focados/lint/tsc; navegador confirmou retorno de foco no FAB mobile/desktop e sino, inclusive cancelamento enquanto o chunk carrega. A fonte canônica F2 permanece congelada; API e contrato não mudaram. A revisão de segurança não identificou bloqueantes no delta de apresentação.
- A variante Webpack F2 compilou sem dependências novas, mas sua calibração continuou acima de 2 s; não houve nova série oficial de 80. O A/B do observador de geometria não demonstrou causa única: não alteramos o driver oficial nem descartamos o baseline.
- Snapshot diagnóstico E1 separou módulo/render/commit/efeito/RAF: dados SSR e queries já presentes, commit→efeito de 1–2 ms. Não trocar `useEffect` por `useLayoutEffect` com essa evidência. Recursos mostraram descoberta de JS em ondas; os intervalos de avaliação/layout observados não atribuem toda a demora ao compilador.
- HTTP/2 no edge local foi validado por ALPN, TLS e Chromium; reduziu TTFB em calibração, mas o marco ainda excede 2 s. Sem alteração de carga/rede/CPU, contador de 1200 ms, dados, autorizações ou upstreams. Configuração HTTP/1.1 anterior preservada para comparação.
- E2 é cópia diagnóstica privada de E1 com apenas Home e cliente pequeno alterados: inicia a promise de dados no servidor e usa React `use()` sob Suspense para tentar anunciar a referência cliente cedo. Foco 2/2 e tsc aprovados; build separado em andamento, ainda sem medida ou promoção à fonte canônica. Relatórios privados `/tmp/varal-frontend11-perf.md` e `/tmp/varal11-performance-architecture.md` delimitam hipóteses e evidências. CA13/18 e E2E integral permanecem abertos.

### 16/11/2026 — Etapa 11: perf01 não atingiu meta; F2 em preparação

- Baseline oficial 80 continua reprovado: p95 pessoal frio/quente 5215,5/5710,2 ms e grupo frio/quente 4612,1/4706,5 ms, todos>2000 ms. Raw sanitizado versionado [rnf05-baseline-01.json](etapas/11-acabamento-deploy/evidencias/rnf05-baseline-01.json), SHA256 fbadb5e103c2522341b03423ee5cd30ae712ba097a4146686ae0b717a8260228. Nenhuma nova 80 pós-otimização.
- Perf01 build 0/imagem b0fa53… ativa: contador isolado/Intl cache/imports Avisos/lazy Folha-gaveta e fallback cancelável, foco 26/lint/tsc0. Segurança delta 22:27 sem novo bloqueante de privacidade no recorte. Calibração 4 não é p95: pessoal 14206/4892,5 ms, grupo 4181,1/5564 ms, HTTP 0 erros, todos>2 s; startup não demonstrado como causa. Timeline e perfil CPU são diagnósticos, sem causa atribuída ao Turbopack.
- QA reproduziu BODY após Escape 3x; fix frontend passou 38 focos/nove arquivos, lint/tsc em execução e sem novo browser. F2 aguarda congelamento frontend. DevOps prepara experimento Webpack do Next sem dependência nova, build/compatibilidade ainda não testados; não declarar ganho. API sem alteração preserva 546; integral web 152 era pré-otimização, nova integral final pendente.
- QA5 parado/análise offline, sem E2E/pytest/80 ativos; worker/beat LAB e API/worker/beat padrão pausados. Mesma carga/target/dados/guards, contador 1200 ms e limite 2000 ms mantidos. E2E final aguarda desempenho/foco. CA13/18 abertos, sem fechamento/push/deploy/limpar-dev.
- Timer ACL confirmado 1111,571 s, 21:10:28.245460Z–21:28:59.683389Z: stage POS até gates/cutover/restart/fresh-login404/TLS; inclui NEG/esperas, exclui preparação/backup/fence. Distinto do exercício direitos 1302,348 s e sem garantia de RTO geral.


### 16/11/2026 — Etapa 11: RNF05 não atendido no baseline completo

- As 80 amostras oficiais terminaram sem erros de carregamento, mas reprovaram CA13: p95 pessoal frio/quente **5215,5/5710,2 ms**, grupo frio/quente **4612,1/4706,5 ms**, limite 2000 ms em cada série. Todas as amostras sanitizadas estão em `etapas/11-acabamento-deploy/evidencias/rnf05-baseline-01.json`. Sem descarte de amostras ou alteração de carga/critério.
- Janela exclusiva dos trabalhos Varal: 21:57:02–22:07:57 UTC, Chromium158, quatro CPUs, CPU×4/rede9Mbps/1,5Mbps/RTT150ms. Worker/beat do laboratório e API/worker/beat padrão pausados; navegador direto na rede interna, sem relay. Atividades de outros projetos não são controladas.
- Regressão RNF10 no navegador aprovada: salvamento offline falha visivelmente e não repete após reconectar. WebKit validou TLS sem bypass, mas não restaurou BFCache: skip, sem comprovação de primeiro quadro persistido. O foco de autenticação passou após aguardar confirmação HTTP200 antes da navegação, mantendo timeouts.
- Fonte de privacidade/restauração sem bloqueantes remanescentes identificados pela segurança. Novo cronômetro ACL mede **1111,571 s** de stage POS até gates/cutover/restart/login404/TLS, incluindo NEG/esperas e excluindo preparação/backup/fence; distinto dos 1302,348 s anteriores. Ferramenta RPO reproduziu 26,280613 s/13 COMMITs do ensaio anterior.
- Frontend/QA iniciam diagnóstico do trabalho inicial e otimização antes de nova imagem/medições. Preservar contador Doop1200ms, dados/autorização/SSR e marco real; CA13/18 abertos e E2E integral ainda não aprovado. Sem push/deploy/limpar-dev.

### 16/11/2026 — Etapa 11: restauração ACL comprovada; janela exclusiva QA/desempenho

- POS final ACL/direitos/bytes/ledger, HMACs com mesma operação/fence/watermark/aclhash, snapshot CURRENT T1fmz1pV e lab-active stop/up passaram; TLS ready/entrar e relay200 com web b1c9. D ativo fez fresh native login e recebeu404 duas vezes. Adendo segurança21:46 encerrou bloqueantes específicos de ACL/direitos/opt-out, distinguindo recibos/logs inspecionados das execuções atribuídas ao DevOps; sem aprovação geral CA16/18.
- Ferramenta RPO versionada executou0 e reproduziu26,280613 s/13 COMMITs do exercício anterior delimitado (ca16-rpo-tool.json); não reutilizar como RTO ACL novo ou garantia. Fonte app API/websrc preservada, integrais546 API/149 web pré-delta e152/152 web pós-delta/lint/build continuam seus cortes.
- E2E01 interrompido intencionalmente143/-15 após516,884 s, sem wrapper aprovado. Foco01 nenhum caso por webServer120 s/Next próprio órfão encerrado; preparo Compose cwd errado corrigido, sem atribuir prova ao comando inválido. Foco02 worker1 passou7/8 (boleto/Pix verdes, signup URL5 s falhou). Diagnóstico UI POST200780 ms/raiz1797 ms/heading1955 ms não reproduziu causa; contenção CPU observada sem causalidade provada. Syncauth teste aguardando POST200 antes URL passou1/1 mobile28,3 s sem mudar timeout/produto. Worker harness/CI1, sem mudar cota.
- QA recebeu GO exclusivo RNF10/WebKit, calibração e benchmark80; sem E2E/build/backup/teste concorrente. Worker/beat LAB e API/worker/beat padrão pausados. Nenhum resultado antecipado ou fechamento CA13/18; E2E final virá após avaliação de performance. Documentos correntes reconciliados. P11/P6/P9 preservados; sem push/deploy/limpar-dev.


### 16/11/2026 — Etapa 11: checkpoint pós-delta offline e gate ACL/auth

- Make test supervisionado01 aprovado com fontes estáveis: 546 API/667,11 s +149 web/170,56 s. API segue sem alteração e a evidência permanece válida. Delta Providers D11-5 always/retry false tem foco3/3; web posterior01 reprovada151/152, 41 arquivos/188,88 s, exit2, findByRole Fechar detalhe em1927 ms; causa não comprovada. Mesma fonte web/src466fcafa… passou152/152, 41 arquivos/153,82 s, exit0 em supervised02, hashes antes/depois iguais, sem mudança de produto/timeout/assertivas. Lint final0/build produtivo0; tipos herdados da dupla determinística01. Falhas anteriores preservadas.
- QA24/24/axe/Doop, PWA técnico CDP e reauth código SMTP passaram; sessão inicial sintética não prova Google. Offline B/abas passou; primeiro frame BFCache persisted não comprovado (Chromium no-store, WebKit TLS; imagem CA preparada aguarda LAB). Benchmark80 ainda não executado; E2E integral iniciou supervisor final-e2e-supervised-01/sessão26550 sem resultado.
- Direitos10 NEG/POS/worker PREPARANDO→ATIVA origemNULL/SHA passaram; T11-L exige também ACL/auth atual da fonte quiescente igual ao clone pós-journal, recibo autenticado e recálculo antes/restart cutover. NEG membro real e opt-out específico passaram; POS final/restart/backup CURRENT/relay/RPO em execução. Revisão candidata de segurança/decisões sem outro bloqueante de fonte no recorte, sem aprovação CA16/18. T11-M delimita entradas administrativas; não autoriza limpar-dev.
- [Relatório](etapas/11-acabamento-deploy/relatorio.md), plano/tarefas/spec e protocolo/runbook reconciliados. CA01–18 continuam sem fechamento integrado. P10 delegada/P11 destino ausente/P6 externa/P9 próximo push preservados; Ajustes sem pendentes atestados pelo dono, sem conector/reexportação. Sem push/deploy/envio externo/limpar-dev.


### 16/11/2026 — Etapa 11: integral aprovada e provas de navegador consolidadas

- `make test` supervisionado passou exit 0: **546 pytest** em 667,11 s e **149 Vitest/40 arquivos** em 170,56 s, com um worker web. Artefatos privados `/tmp/varal11-final-test-supervised-01/{status.json,command.log}`; hashes das fontes antes/depois iguais. As integrais anteriores reprovadas e a execução interrompida exit 143 permanecem históricas, sem conversão em aprovação.
- LAB24 final passou **24/24** nas três larguras. Axe desktop aprovado após separadores de texto reais no seletor de espaço; instalação técnica PWA via Chromium/CDP e reautenticação nativa por código SMTP local aprovadas. Sessão inicial desta última é fixture sintética; não prova Google real. Logout offline entre abas e ações próprias de B aprovados.
- Primeiro frame de BFCache continua sem comprovação: Chromium recusou armazenamento por `no-store`; tentativa WebKit parou por confiança TLS. Não tratar skip como aprovação. Revisão identificou fila padrão de mutações TanStack offline; frontend prepara correção e teste de não reprodução ao reconectar antes do E2E final.
- Restore de direitos aceitos/pins passou NEG/POS, inclusive retomada de cópia aceita depois da exclusão. Novo bloqueante concreto: ACL/auth revogados após o alvo de restore poderiam reaparecer. Gate compara fonte atual quiescente com clone; DevOps executa novo NEG/POS antes de reabrir. Backup cifrado da geração restaurada passou após correção do ACK de WAL vazio. Segurança final, benchmark de 80 amostras e E2E integral ainda pendentes. Sem push/deploy/limpar-dev.

### 16/11/2026 — Etapa 11: API integral aprovada; aceites protegidos no restore ainda em correção

- Integral03 aprovou **546/546 pytest** em 736,00 s, com ping original e helper corrigido. `make test` terminou reprovado no web: **148/149**, um timeout de 5 s em `refetch-privacidade`, execução paralela; lint/E2E não iniciaram. Evidências `/tmp/varal-qa11-integral-03.*`. Não converter a aprovação da API em aprovação do wrapper.
- QA LAB24 terminou **18 aprovados/6 falhas**: cinco de seletores/coleta de resposta após navegação e uma axe desktop. Nó comprovado no seletor SideNav, texto visível fora do nome acessível. Correção inclui texto completo/ação, e Vitest passou a um worker sem elevar timeout; foco 14/14, ESLint e tsc aprovados. Novo build web `sha256:ec954fad805bdde5090e2c82ea0919568016af117ddfc060dbf25faa67be9800` concluído; repetir axe/24/CA11/PWA ainda necessário. Sem benchmark.
- CA08 isolado executou aceite 10/pin, DELETE nativo 204/journal, conclusão pelo worker, hash do PDF S3 e ACL. Usa Django Client in-process, sem alegar proxy/browser. CA17 comprovou fila/worker SMTP STARTTLS com uma captura `.invalid`, aceita/1; Push HTTPS com worker/broker isolados aceitou/1 após validação de Host/SNI/VAPID/AES128GCM pelo receptor. Sem provedores externos ou recepção push física.
- Cutover sintético passou TLS/readiness/witness/ledger conservador, mas auditoria específica encontrou **bloqueante CA16**: inventário só do clone não detectava reserva/pin aceito após target. Cleanup poderia apagar bytes sem reconhecer esse direito. Serviços do laboratório estão fechados; gate novo compara direitos protegidos da fonte autoritativa quiescente com o clone, e ensaio NEG/POS ainda está em preparação. A prova positiva anterior continua parcial.
- ACTIVE_RESTORE e guards impedem `up/down/backup` base de reabrirem a origem. Primário atual foi migrado ao Compose persistente em modo core, com volumes restaurados explícitos; origem antiga preservada parada, API/edge/workers bloqueados por `CA08_GATE_PENDING`. Backup atual/restart completo e RPO/RTO cronometrados ainda precisam prova. Todos os CAs continuam sem fechamento integrado; sem push/deploy/limpar-dev.

### 16/11/2026 — Etapa 11: interferência Celery localizada e restore APP em validação

- Integral 02 terminou reprovada: 545 pytest aprovados e o mesmo ping falhou, 546 casos em 479,57 s; `make test` exit 2, sem avançar a Vitest/lint/E2E. Tipos herdados da integral01 seguem com hashes iguais. Rodadas 01/02 reprovadas preservadas em `/tmp/varal-qa11-integral-01.*` e `-02.*`.
- Rastreio por caso localizou a causa em `test_rn21_pagamento_concorrente_com_saida`: duas tarefas eager em threads diferentes restauraram a trava global Celery na ordem True/True/False/True, deixando-a ativa fora de uma tarefa. Rastreio 25470 terminou exit 1 intencional no teardown, após 248 aprovados. O helper de testes agora isola o agendamento durante as threads, preservando produção e o ping; foco 74483 passou 11/11 em 55,37 s. Integral03 iniciou sessão 64474, `/tmp/varal-qa11-integral-03.*`; ainda sem resultado. Corte agregado API+testes `6a07c8da33a378895fc32abd4468569de00f77bc6b4f07087bfdbb642b0ce39f`; API de produção continua a mesma do snapshot42c84479.
- Perfil corrigido passou 5/5/ESLint/tsc e novo build `varal11-web-perfil-final:local` terminou exit 0, imagem `sha256:be31168ec32fd2d7c7a2bde6031eec827b2b43dd3645ad0b7029200160dcac49`. Novo axe/24 casos/CA11/PWA/benchmark ainda pendentes.
- LAB4 restaurou banco/objetos em volumes novos, autenticou prova e reaplicou journal real: usuário removido, conta do grupo e pin preservados, estado INICIADA mantido. Gate posterior comparou integralmente os dois ledgers da origem parada com o clone e validou watermark WAL/selo; conversão INICIADA→INCERTA e cutover permanecem em execução. Não abrir origem e clone juntos. Fixtures pin direto/INICIADA manual não provam aceite 10 ou SMTP/Push reais; scripts separados preparados, sem execução.
- Segurança candidata não encontrou novo bloqueante comprovado no corte revisado, mas não aprovou CA16/18. Todos os CAs seguem sem fechamento integrado. Sem push, destino remoto, limpeza de dev ou exclusão de conta real.

### 16/11/2026 — Checkpoint da Etapa 11, sem fechamento

- API/Perfil/PWA/isolamento/SSR, journal/WAL e laboratório integrados em validação. T11-A–K ratificadas, atestado E/K e D11-3 Redis E2E registrados; [relatório](etapas/11-acabamento-deploy/relatorio.md) contém cortes e limites. Todos os 18 CAs permanecem abertos.
- Integral 01 runner 89956: tipos duas vezes determinísticos/exit 0; test exit 2 com 544 pytest aprovados/1 falha em 545 casos (587,29 s), ping Celery. Mecanismo eager global demonstrado como hipótese, sem atribuição comprovada ao teste causador; delta apenas em testes isolou Task.apply_async nas seis corridas e foco nativo 299/300 s/multi-sessão/CSRF passou 10/10 (38,53 s), diagnóstico 128/128 sem leak. Rodada antiga 530/4 permanece reprovada em outro corte. Web serial 149/149, 40 arquivos, 167,46 s, Node22/um worker; não é corte posterior ao patch Perfil. Integral 02 iniciada sessão 46822 (test→lint→e2e), sem resultado; tipos herdados da 01 após hashcheck, sem duas execuções novas. Corte API+testes a9473580…, API produtiva preservada 42c84479…; sem lint/E2E integral aprovados.
- QA LAB4 primeiro foco 1/2 falhas de harness; segundo 1/1 com três violações axe reais por main aninhado. Patch div passou 5/5/ESLint/tsc; exige rebuild e novo axe/browser. Sem execução completa 8×3 ou benchmark. Helper Redis real validou sentinelas/recusas, sem FLUSHDB/Redis dev; não prova cota HTTP. Guarda Node20 antes de Docker comprovada isoladamente.
- LAB4 clone PostgreSQL subiu, usuário presente/INICIADA antes de reaplicar journal, corte autenticado/journal SEALED; emissor real/atestado/cutover APP positivo ainda ausentes. Pin direto/INICIADA manual não provam CA08 aceite real ou CA17 fila/transporte real. Segurança parcial releu correções S11-1/2/3 e fronteira E/K; sem aprovação final ou CA09/16. Matriz pertence ao QA. P10 delegada/P11 destino ausente/P6 externa/P9 próximo push preservadas; Ajustes sem pendentes atestados pelo dono, sem conector/reexportação. Sem push/deploy/envio externo/limpar-dev.


### 16/11/2026 — Etapa 11: exportação limitada e recuperação física isolada

- Continuidade autorizada pelo pedido “continue”. Download de exportação usa artefato privado verificado e lotes de até 500 documentos; dirigidos 8/8 e 3/3 aprovados, incluindo 501 contas/documentos, parte ausente, duas ordens concorrentes RN32 e recibo de fence adulterado. São recortes, com storage/journal simulados em parte; não substituem a integral ou os CAs de concorrência/restore.
- Integral intermediária da API: 530 aprovados e quatro falhas em 534 casos. Os contratos de log/401 e o teste concorrente foram corrigidos e passaram no dirigido; falta repetir a integral sobre o código final. Web final passou 149/149 Vitest em 40 arquivos, Node 22.23.5 e um worker, em 167,46 s (`/tmp/varal11-web-final-serial.log`, exit 0). Os 144/144 anteriores eram um corte anterior ao último ajuste de isolamento.
- Build produtivo web candidato `c6364428a83e9a80766f457e8e75685a455d064b5f034013511c96fd09020ba2` concluído. Ainda sem aceite de navegador/acessibilidade/PWA/desempenho. QA preparou oito cenários em três larguras e as 80 medições RNF05; nenhuma executada neste checkpoint.
- Laboratório isolado comprovou backup físico e objetos cifrados, WAL autenticado contínuo e recuperação em três volumes novos até LSN alvo, incluindo commit posterior à base. Objeto sintético recuperado com bytes iguais, acesso anônimo e admin negados. Ainda faltam fixture do aplicativo, exclusões/journal/ledger, caminho positivo de reconciliação e RPO/RTO medidos; serviços/dispatch restaurados permanecem fechados.
- Laboratórios antigos foram parados para reduzir carga, preservando volumes e serviços de desenvolvimento. Sem push, deploy remoto ou limpeza do banco de desenvolvimento. CA01–18 continuam sem fechamento integrado; P11/P6/P9 preservadas.

### 16/11/2026 — Etapa 11 em implementação; retomada da execução

- Etapa 10 concluída no commit `062258c`, merge local `5cd29ba`; branch atual `etapa/11-acabamento-deploy`. Resultado integral10: 506 pytest, 127 Vitest, tipos determinísticos, lint e `make e2e` 143 aprovados/3 skips previstos. Esses números não são resultados da 11.
- Backend implementa revisão transacional/triggers, jobs/staging de exportação, download e exclusão com PREPARE/COMMIT. Ainda faltam fechamento das entradas Model/QuerySet/admin, revalidação integral, recuperação/restore e provas de concorrência; contratos novos não liberados como completos nem schema final gerado. Última rodada dirigida comunicada antes da retomada: 7 testes, com transporte/storage simulados em parte; não é integral ou prova de todos os CAs.
- Frontend implementa manifesto/SW único, isolamento por identidade/geração, hint opaco para SSR, conferência de requisições/respostas privadas e logout offline. T11-I está registrado em decisões11: cabeçalhos são precondições, nunca autenticação. Perfil/exportação/exclusão aguardam tipos reais; nenhuma prova de navegador/desempenho concluída. Checkpoint: `/tmp/varal-frontend11.md`.
- DevOps comprovou testes do journal, HTTP real cliente/writer, container não root com reinício e proxy TLS com upstreams sintéticos. NGINX atualizado para 1.30.6 com digest verificado e smoke repetido. Faltam stack real, backup/restore completo, transportes, testes integrados e métricas; detalhes/limites em `/tmp/varal-devops11.md`.
- Propriedade: backend possui API, exceto OpenAPI do orquestrador; DevOps possui infra/Makefile/CI e, pontualmente, `api/pyproject.toml`/`api/uv.lock` para Gunicorn; frontend possui web exceto tipos gerados/e2e. Agentes retomados após o pedido “continue”; testes/serviços comuns seguem coordenados. Runner integral11 preparado em `/tmp/varal-qa11-runner.py`, ainda não iniciado.
- 18 CAs da 11 continuam pendentes de integração/QA/segurança. P10 resolvida por delegação; P11 depende do destino remoto, P6 é externa e P9 aguarda push autorizado. Ajustes sem pendentes atestados pelo dono no chat, sem conector/marcação remota. Sem push, implantação remota ou limpeza de dados de desenvolvimento.

### 16/11/2026 — Merge local da Etapa 10 e abertura da Etapa 11

- Etapa 10 concluída no commit `062258c`, merge local `--no-ff` na main `5cd29ba`; aberta `etapa/11-acabamento-deploy`. Etapas 04–10 concluídas e integradas. Validação final 10 preservada: tipos duas vezes determinísticos, 506 pytest/127 Vitest em 33 arquivos, lint verde e `make e2e` 143 aprovados/3 skips previstos (146 casos, 11,0 min), runner 82968 passed/exit 0; QA/cleanup/segurança/decisor sem bloqueantes. Esses resultados não aprovam nenhum CA da 11.
- Integrados [spec/plano/tarefas/decisões 11](etapas/11-acabamento-deploy/spec.md), [ADR0015](arquitetura/adr/0015-exportacao-exclusao-e-prova-local.md) e [protocolo journal](arquitetura/protocolo-journal.md). Q11-1–11 e T11-A–H ratificadas por delegação; implementação local liberada; frontend inicia PWA/isolamento/SSR estáveis após leitura Doop, novos contratos aguardam tipos reais. Nenhum código/teste/CA11 concluído nesta abertura.
- Guardas RN04/RN32 precedem efeitos pessoais; conflito após PREPARE pode deixar ABORT opaco, sem consumo da intenção. Última checagem R autoriza emissão do download antes de liberar barreira/rede, sem atomicidade até byte físico. Checkpoint independente prova fronteira operacional local, sem promessa anti-root/novo gate de hardware. SSR restrito aos três GETs T11-G. B autenticado usa seus dados/ações; apenas rebind push aguarda reconciliação, nonces10 preservados por dono.
- Dono atestou Ajustes sem pendentes no chat e delegou decidir/executar o restante; sem conector, marcação remota ou reexportação. P10 resolvida por Q11-11 para Perfil com componentes atuais/canvas somente leitura, sem resposta literal à pergunta específica ou frame inventado. P11 é dependência concreta de destino/condições remotas; P6 externa, P3/P4 locais da 11 e P9 próximo push preservadas. Sem novo ok genérico, push, envio externo, deploy real ou alteração dos volumes existentes.



### 16/11/2026 — Etapa 10 concluída, pronta para commit/merge local

- `make types` passou duas vezes com hashes idênticos; `make test` passou com **506 pytest e 127 Vitest em 33 arquivos**; `make lint` passou. Runner único da orquestração: `/tmp/varal-qa10-integral.json`. `make e2e` passou integralmente: **143 aprovados e três skips previstos, 146 casos, em 11,0 min**. Runner 82968 `passed`, todas as etapas com exit 0; wrapper e build aprovados nesta etapa. Os 483 pytest/111 Vitest são da etapa 09; 122 Vitest era uma fotografia intermediária da etapa 10.
- Solicitações, cópia privada de PDF, sincronização das marcas e modo simples integrados e congelados. Nonce/hash, recuperação/abandono por origem própria e projeções autorizadas documentados no [relatório 10](etapas/10-solicitacao-modo-simples/relatorio.md). Marca e undo derivados no pessoal usam Sistema/autor NULL; comprovante permanece no grupo.
- Prova real isolada em Silo/Postgres/Redis/Celery confirmou pin após CASCADE, cópia por fila, bytes/tamanho/SHA, acesso anônimo negado e limpeza dos recursos próprios. Não prova PUT físico tardio ou entrega LGPD da etapa 11. Cleanup de PDF/comprovante usa geração/CAS e tombstone incerto, sem trava de domínio durante S3; SDK sem retry oculto.
- QA comparou pedido topo/fundo e modo simples em 390×844 e 1440×900 aos frames 12/M06 e 13/D05. Correções de keys React, alvo de 44 px, chips longos e ações Pix verificadas; retorno ao recorte de pagas aprovado em focos desktop/mobile separados. Processos próprios encerrados e matriz atualizada pelo QA. Focos anteriores reprovados permanecem no relatório e não são somados à integral.
- Saída reutiliza RF06/CU03/RN04/RN21/RN32; detalhe e retorno seguem RF13/CU06/RF25, sem conceder RF07 ou RF12. Q04-23/Q10-15 restringe nome/e-mail a candidatos atuais elegíveis; Q04-29/Q10-17 mantém linha única, reticências e texto integral acessível. Segurança integrada/delta e auditoria Q10-15–18/D10-1–2 sem bloqueantes por leitura; os 14 CAs foram consolidados com testes e limites no relatório.
- Ajustes sem pendentes atestados no chat, sem conector ou marcação remota. P10 resolvida por delegação para Perfil na etapa 11; P6 externa, P11/destino, P3/P4 produção e P9 próximo push preservados. Etapa concluída, aguardando commit/merge local sem hashes antecipados. Sem push ou deploy.

### 16/11/2026 — Merge local da Etapa09 e abertura da Etapa10

- Etapa09 no commit `4e04ddf`, merge local `--no-ff` na main em `56337ed`; aberta `etapa/10-solicitacao-modo-simples`. Resultado final09 preservado: 483 pytest, 111 Vitest, tipos duas vezes determinísticos e lint verdes; Playwright integral via `npm run e2e` sobre runtime local validado: 131 aprovados/3 skips previstos. O wrapper `make e2e` permaneceu failed por GHCR/MIME antes do navegador, conforme relatório09; nenhum resultado operacional foi convertido em aprovação do wrapper.
- [Spec/plano/tarefas/decisões10](etapas/10-solicitacao-modo-simples/spec.md) e [ADR0014](arquitetura/adr/0014-solicitacao-e-sincronizacao-privada.md) integrados. Q10-1–14 triadas por delegação e T10-A–E ratificados: coordenação de domínio única/curta, pin antes202, cópia/cleanup fora de locks de domínio, causa canônica09 e recuperação por nonce/tombstone. Backend possui coordenador/demaisAPI; especialistaPDF somente boletos/helpers/migrações/testesPDF; execução em paralelo, frontend aguarda tipos reais. Nenhum CA ou teste10 declarado concluído.
- Dono atestou Ajustes sem pendentes no chat, sem conector, marcação remota ou reexportação. Delegação existente autoriza continuidade sem novo ok genérico. P10 resolvida para composiçãoPerfil11 com componentes existentes, sem frame inventado; P6 externa, P11/destino, P3/P4 produção11 e P9 próximo push preservados. Sem push/deploy.

### 16/11/2026 — Etapa 09 concluída, pronta para commit/merge local

- Validação final: 483 pytest, 111 Vitest, tipos duas vezes determinísticos e lint verdes. Suíte Playwright COMPLETA por `cd web && npm run e2e`, Node 22.23.5, passou 131 testes/3 skips previstos (134 casos) em 9,4 min, runner 52177 passed/exit 0. API/worker locais existentes foram verificados (API 200, pywebpush 2.3.0), sem rebuild externo ou mudança de produto/runtime/lock.
- `make e2e` da revalidação não passou: falhou antes do navegador no HEAD ao GHCR/uv 0.13.7 por resposta MIME/proxy malformada. A integral 129/3/2 também permanece failed; seletor legado corrigido só no teste, foco 360 px 2/2 verde. Focos/direcionados não são somados à aprovação final. Sem mudança de Makefile/TLS/proxy para contornar o problema operacional.
- QA confirmou matriz estável, runner/Next próprios encerrados e comparação de capturas 02/D02/04/D06 nas duas larguras (sino/indicador/recentes/central/gaveta branca). Segurança e decisões sem bloqueantes. Provas DevOps reais locais mantêm limites: sem provedor público, push real no navegador, SMTP TLS externo ou espera real às 07:00. [Relatório](etapas/09-notificacoes/relatorio.md) concluído, sem hashes de commit/merge antecipados.
- P7 resolvida pela central RN32 privada e legado seguro com critérios verdes; P10 resolvida por delegação expressa. P6 externa, P11/destino pendente, P3/P4 produção na 11 e P9 próximo push preservadas. Dono atestou Ajustes sem pendentes no chat, sem leitura/marcação remota/reexportação. Próximo passo: commit/merge local da 09 e abertura da 10, sem push/deploy.

### 16/11/2026 — Etapa 09: suíte verde, E2E final ainda sem aprovação

- Integral: 483 pytest, 111 Vitest, tipos duas vezes determinísticos e lint verdes; E2E terminou failed com 129 passes/3 skips/2 falhas de seletor legado H1 oculto em 360 px. Correção somente do seletor e foco 360 px 2/2 verdes, produto intacto. Revalidação runner 51372 consultada com lint0/E2E2/status failed; sem conclusão final ou causa inferida nesta atualização.
- Backend 53 direcionados (35 notificações+18 pagamentos), Ruff e migrações 0001–0005 verdes. Foco QA inicial 3/5 failed preservado; corrigido 8/8, visual 6/6 e sino 2/2 verdes, sem somar focos/direcionados à integral. Fundo branco D06 e sino D02 circular/borda/ponto vermelho corrigidos antes da integral. Capturas 02/D02/04/D06 comparadas pelo QA; alvo/overflow medidos na central, não no sino do Início.
- Segurança final em leitura sem bloqueantes após B09-final1 e rechecagem do snapshot; decisões auditadas sem escolhas pendentes. Revisores leram snapshots anteriores às últimas verificações; resultado recente atribuído à orquestração/QA. D09-2/3 realizam Q09-6/Q09-9 sob delegação, sem autorização autônoma por mera reversibilidade.
- [Relatório](etapas/09-notificacoes/relatorio.md) em validação; faltam E2E integral verde, matriz/cleanup QA e Ajustes finais. P7 não resolvida até fechamento; P10 resolvida por delegação expressa, P11/destino pendente e P6 externa. Sem push/deploy ou abertura da 10.

### 16/11/2026 — Etapa 09 integrada, em validação

- Central/API/tipos/transportes/preferências/push integrados. DELETE por id de inscrição removido: UUID de instalação, tombstone causal, sessão HMAC terminal e logout nativo impedem POST atrasado/troca de conta; aliases de origem partilham fingerprint sem transferir vínculo. D09-2/D09-3 registrados. P7 snapshot novo mínimo; legado opaco sem enriquecimento, central-only antes da ativação persistida. Todos EventosPagamento da 07 sem corte, revogação terminal, leases/três tentativas/incerta e rotina ordenada 08→09 preservados.
- Frontend congelado informa 110 Vitest/lint/tsc verdes; QA escreveu E2E, ainda não executado. Backend termina testes e segurança fecha parecer; sem contagem integral ou aprovação final. Desktop mantém tela/filtros/history pelo mesmo URL, direto `/avisos` fundo Início; Doop relido em leitura, frames draft. Prova de browser/visual ainda pendente.
- DevOps comprovou transporte local real criptografado HTTPS/TLS/SNI/pin/VAPID e SMTP, beat/worker/dispatcher em rede interna com DB/broker efêmeros; rotina gerou ocorrência/aviso únicos, e e-mail local ficou aceito com uma tentativa. Configuração 07:00 e recuperação 300 s/dispatcher 60 s verificadas separadamente; não houve espera real às 07:00, provedor público, push em navegador ou entrega física garantida. Recursos temporários removidos, volumes/banco normais preservados.
- [Relatório](etapas/09-notificacoes/relatorio.md) em validação, matriz do QA. P7 não resolvido até QA integral. P10 resolvida pela delegação expressa para composição Perfil na 11 (sem resposta literal/silêncio e sem implementação da 11 agora); P11/destino pendente e P6 externa. Ajustes atestados sem pendentes no chat, sem conector/remarcação/reexportação; sem push/deploy.

### 16/11/2026 — Merge local da Etapa 08 e abertura da Etapa 09

- Etapa 08 concluída nos commits `b5d516d` e `eadb1c2`; merge local `--no-ff` na main em `59e0cc5`. Resultado final: 448 pytest, 101 Vitest, tipos duas vezes determinísticos, lint e E2E 123 aprovados/3 skips; segurança B08-1–4 e decisões sem bloqueantes, QA/visual/cleanup confirmados. Sem push.
- Aberta `etapa/09-notificacoes`; Q09-1–9/D09-1/ADR 0013 e spec/plano/tarefas integrados. Backend/DevOps em execução, relatório em construção sem testes/envios declarados. Central privada/revogação terminal; três tentativas totais e incerteza sem retry cego; todos EventosPagamento da 07 sem corte, legados RN21/P7 só central. Fluxo diário único gera/recupera 08 antes de avaliar avisos 09; leitura em lote alcança somente avisos próprios autorizados.
- Dono delegou continuidade e atestou Ajustes sem pendentes no chat, sem conector ou reexportação. P7 é escopo em execução da 09, ainda não resolvido; P6 externa, P10/Perfil e P11/implantação preservadas. Próximos passos: schema/tipos, frontend nos frames existentes, provas reais/QA/segurança e consolidação, sem antecipar a 10 ou deploy.

### 16/11/2026 — Etapa 08 concluída, pronta para commit/merge local

- Validação final: 448 pytest pós-B08-4, 101 Vitest após correção apenas de espera do teste Clipboard, tipos duas vezes determinísticos, lint integral verde e E2E final 123 aprovados/3 skips previstos (126 casos), runner passed/exit 0. Rodadas com falha ou interrompidas permanecem no relatório como resolvidas, sem serem contabilizadas como aprovação; direcionados não são somados à suíte.
- Segurança B08-1–4 encerrados e decisões auditadas sem bloqueantes. Agendador real/catch-up/pausa/reinício/unicidade comprovados em recursos isolados removidos; agenda 07:00 Fortaleza verificada separadamente. QA confirmou matriz estável, capturas Pix/PDF de topo/fundo nas duas larguras, foco/clique/alvos de 44 px e ausência de overflow; runner/Next próprios encerrados. Datas curtas/catch-up/concorrência/fallback Sem casa comprovados no backend; sem alegar captura dedicada final de 07/D03 e 10/D04 ou espera real às 07:00. [Relatório](etapas/08-recorrencia-agendador/relatorio.md) concluído; commit/merge local ainda por executar, sem hash antecipado e sem push.
- Dono atestou no chat ausência de Ajustes pendentes no fechamento; sem conector, marcação remota ou reexportação. P6 externa, P10/Perfil e P11/implantação preservadas. Continuidade autorizada: commit/merge local da 08 e abertura da 09; nenhuma implantação autorizada por silêncio.

### 16/11/2026 — Etapa 08 após correção de autoria, rodada final em curso

- B08-4 corrigido: geração automática é ação do sistema; criação manual cujo autor foi excluído continua Ex-membro. Propriedade central/serializer/formatter alinhados, duas regressões API verdes; sem schema/migração/ACL/reescrita. Segurança do delta sem bloqueante; B08-3 fechado e auditoria decisória anterior válida.
- Pipeline posterior ao delta: 448 pytest e tipos duas vezes verdes; web parou em 100/101 num teste antigo assíncrono de foco Clipboard. Apenas o teste foi corrigido com espera mantendo foco/seleção; 2/2 focados, 101/101 web e lint/tsc verdes. Produto intacto após os 448. Os 446 anteriores não são o total atual; direcionados não são somados.
- Rodada final atual: lint verde, E2E integral ainda executando, sem aprovação antecipada. Rodada anterior interrompida para B08-4 teve exit -15 solicitado e processos encerrados; a rodada com 118 passes/3 skips/3 falhas também não foi aprovação. QA confirmará resumo final, visual/foco/autoria, cleanup e matriz. Consolidação/revisão de Ajustes/commit/merge locais seguem pendentes; P6/P10/P11 preservadas, sem push.

### 16/11/2026 — Etapa 08 em pré-fechamento, E2E integral ainda pendente

- Recorrência/agenda/revisões/competências/idempotência, primeira cobrança com código/PDF, escopo e arquivamento autorizados integrados; schema/tipos e gestão pessoal/grupo conectados. Q08-1–10/D08-1/ADR 0012 preservam positivos legados em aguardando, autoria por UUID/papel atuais e revogação de pagador/escolhidos. Migrações aplicadas; coluna experimental removida por nova `recorrencias.0003`, sem reescrever as aplicadas.
- Suíte: 446 pytest e 101 Vitest verdes, tipos duas vezes sem diferenças; runner parou em Ruff do arquivo QA. Após ajuste de fixture/import/formatação, Ruff e os 12 QA repetidos passaram; lint final verde. Backend direcionado 25 e QA 12 são evidências separadas, sem somar aos 446. Frontend 101/101 pós-B08-3, tsc/lint verdes substituem o resultado anterior de 99.
- Beat/worker reais em banco/fila isolados comprovaram catch-up, meses pausados, reinício e unicidade. Agenda normal 07:00 Fortaleza validada separadamente com relógio Celery; intervalo curto de prova não equivale a espera real às 07:00. Recursos temporários removidos; serviços normais saudáveis, sem produção/transporte.
- B08-3 fechado por reauditoria em leitura após base de edição por sessão e regressões; nenhum novo bloqueante. E2E integral terminou com 118 aprovados, 3 skips previstos e 3 falhas de testes (duas expectativas de Ver todas e helper de checkbox). Os 14 novos passaram juntos, mas a rodada está reprovada. QA corrige só testes com prova real de rótulo/foco; produto/API congelados e repetição integral pendente. O foco interrompido anterior de oito passes parciais não conta como aprovação. Faltam repetição final, confirmação visual/recursos encerrados, auditoria decisória e matriz QA. [Relatório](etapas/08-recorrencia-agendador/relatorio.md) em validação, sem conclusão antecipada. P6/P10/P11 preservadas; Ajustes finais ainda por conferir conforme delegação vigente, sem conector ou reexportação. Commit/merge local ainda dependem do fechamento; sem push.

### 16/11/2026 — Merge local da Etapa 07 e início da Etapa 08

- Etapa 07 concluída em `098b934`, merge local `--no-ff` na main em `2599655`. API 413 pytest e tipos determinísticos verdes; frontend 93 Vitest após correção do estado vazio, lint e E2E final 107 aprovados/3 skips previstos. Provas reais de PNG/PDF/S3/Celery, capturas mobile/desktop e segurança/auditoria sem bloqueantes. Nenhum processo Next da suíte permaneceu. Sem push.
- Aberta `etapa/08-recorrencia-agendador`. Spec/plano/tarefas e Q08-1–9/ADR 0012 integrados por docs/decisor; abertura e triagem concluídas. Backend/frontend em implementação, relatório em construção e sem validação final declarada. NULL representa valor a definir; geração mensal é única por competência e não copia arquivo/código de outro mês. Primeira competência pode receber conferência atual na mesma transação, sem criar conta extra. Gestão pessoal e de grupo usa os componentes existentes; arquivamento atua só no que o admin já vê.
- Ajustes: declaração vigente do dono no chat de que não há pendentes, sem conector ou reexportação. P6 externa, P10/Perfil e P11/deploy seguem específicos da etapa 11 e sem resposta. Continuidade autorizada: backend, tipos, frontend, provas do agendador, QA/segurança/docs e commits locais.


### 16/11/2026 — Etapa 07 concluída, pronta para commit/merge local

- Pagamento integral, comprovantes privados/históricos, undo, progresso e Ex-membro integrados; Q07-1–11/ADR0011 e D07-1 consolidados. Estado vazio preserva “0 contas em mês”, sem fração0/0; evento durável07→09 não equivale a aviso entregue.
- `make test`:413 pytest/91 Vitest verdes; após ajuste mínimo de estado vazio, suíte web93/93 verde. Tipos2x determinísticos e lint verdes. S3/Celery real com PNG/PDF originais, bytes/MIME, assinatura e cleanup verdes. Foco pagamento10/10 e regressões de legenda6/6 verdes.
- Segurança Astra integrada sem bloqueantes; B07-1 corrigido com teste concorrente paga/confirmada verde. Capturas/fluxo comparados ao Doop nas duas larguras; capturas finais com animações desativadas confirmam o check completo, substituindo a imagem mobile anterior durante animação.
- E2E integral final:107 passaram/3 skips previstos em6,9min, status passed/exit0; lint final exit0. Rodada anterior101 aprovados/3 skips/6 falhas corrigidas não conta como aprovação. Backend413/tipos2x são da rodada anterior; web93 e lint/E2E verificaram as correções posteriores. QA confirmou capturas finais, matriz atualizada e runner/Next encerrados. Definição de pronto cumprida; [relatório](etapas/07-pagamento/relatorio.md) pronto para commit/merge local, sem push. P6 externa; P10/P11 específicos da11 preservados.

### 16/11/2026 — Merge local da Etapa 06 e início da Etapa 07

- PDF concluído em `4391b3d`, merge local `--no-ff` na main em `b21bd83`. Validação final: 390 pytest, 89 Vitest, 97 E2E e 3 skips previstos; tipos determinísticos, lint, storage/Celery real, inspeção headed e segurança sem bloqueantes. Processos de teste próprios encerrados. Sem push.
- Criada `etapa/07-pagamento`; spec/plano/tarefas/decisões integrados. Q07-1–10 e ADR 0011 fecham pagamento integral, autoria, evidência original privada e histórica, métricas, reabertura e evento durável para notificações na 09. Doop consultado em leitura, incluindo frames draft usados por delegação sem alterar o canvas; barras seguem dados reais e confirmação não promete aviso entregue.
- Ajustes: dono confirmou no chat que não há pendentes, sem alegar conector ou reexportação. P6 continua externa; P10/P11 específicos da 11 aguardam resposta. Próximo passo: backend, tipos e frontend da 07, depois QA/segurança/docs e continuidade autorizada.

### 16/11/2026 — Etapa 06 concluída (commit/merge local realizados na sequência)

- Documento/PDF manual, spool privado, Celery e processo dedicado integrados; I/O real por django-storages. Tentativa UUID, mutex e intenção persistida protegem execução antiga, limpeza e rollback. No-op de metadados corrigido com regressões.
- **390 pytest, 89 Vitest e 97 E2E passaram, com 3 skips previstos; lint e tipos determinísticos verdes.** Provas reais de S3/Celery/assinatura/cleanup e inspeção headed do PDF/fallback em mobile/desktop passaram. Ajustes preliminares de popup/controle de arquivo foram conferidos com Tab real; repetição integral final com exit 0 e sem servidor Next próprio remanescente.
- Segurança Astra sem bloqueantes por leitura; auditoria sem perguntas/decisões pendentes. Resultado final e matriz no [relatório](etapas/06-pdf-boleto/relatorio.md). Definição de pronto alcançada; commit `4391b3d` e merge local `b21bd83` realizados na sequência. Sem push.
- Ajustes: dono declarou ausência de pendentes pelo chat; sem conector/marcação remota. P6 continua externa. Perfil/deploy P10/P11 permanecem sem resposta, específicos da 11; não bloqueiam 06–10 nem autorizam VPS por silêncio.

### 16/11/2026 — Merge local da Etapa 05 e início da Etapa 06

- Etapa 05 em `7dc6a8e`, merge local `--no-ff` na `main` em `e5c94e3`; 354 pytest, 83 Vitest e 91 E2E verdes (3 skips previstos), lint, tipos determinísticos, comparação visual e segurança sem bloqueantes. Execuções interrompidas anteriores não contaram como resultado final. Sem push.
- Criada `etapa/06-pdf-boleto`; spec/plano/tarefas/decisões aprovados sob a delegação vigente. Extrator isolado preparado com 17 testes sintéticos e revisão de segurança sem bloqueantes; worker/storage/interface ainda não implementados.
- ADR 0010 detalha RNF06: recepção faz spool local privado; envio ao S3 e extração ficam fora da requisição, no worker. Extração em processo dedicado com limites e logs protegidos. Documento tem destino de edição separado do vínculo confirmado e nunca reabre acesso de draft depois de vinculado.
- Limites definidos: PDF 5 MiB, extração 20 páginas/200 mil caracteres, URL assinada 60 s, draft 24 h. P1 resolvida quanto ao serviço/autenticação; esta etapa valida objeto e assinatura reais. Ajustes: dono informou que não há pendentes; P6 permanece externa, sem categoria pelo ADR 0005.

### 16/11/2026 — Etapa 05 concluída

- Parser bancário/arrecadação e Pix integrado a Instrumento (`boletos.0001_initial`), preview autenticado e criar/editar/detalhe da conta. Save revalida valor/data e conteúdo mesmo quando PATCH preserva instrumento; histórico registra só tipo e ocorrência de troca. Manual legado permanece sem relação.
- Política de fator bancário explícita: sugestão do ciclo atual e alternativa legada, sem heurística por data atual; usuário escolhe uma data codificada. Pix preserva payload, não busca URL dinâmica/DICT nem executa pagamento. Valor estático zero é inválido; valor de QR dinâmico é ignorado e preenchido manualmente.
- Interface entregue: entrada/conferência, campos codificados protegidos, data ambígua explícita e cópia com confirmação/fallback acessível. Backend direcionado: **143 verdes (54 API + 89 contas)**; parser puro atual: **65 verdes**, incluindo aviso RNF11; frontend pertinente: **27 verdes**. Essas contagens não são somadas à suíte integral.
- **Validação integral final: 354 pytest, 83 Vitest e 91 E2E passaram; 3 skips previstos; lint verde e duas gerações de tipos sem diferenças.** Todos os comandos terminaram com exit 0 e estado final comprovado `passed`. Resultados parciais de tentativas anteriores sem resumo final, com causa indeterminada, não foram contabilizados como rodada verde.
- Dois achados funcionais (controles/reset durante gravação e refetch substituindo conferência local) encerrados com três regressões e CA15/CA16; reauditoria de segurança sem bloqueantes. Aviso RNF11 corrigido para dd/mm/aaaa sem mudar datas do DTO; quatro novos E2E e capturas finais conferidos em mobile/desktop, com fixtures sintéticas e comparação visual sem pixel a pixel. Next da suíte encerrou sem processo próprio remanescente. [Relatório](etapas/05-boleto-pix/relatorio.md).
- Conferência vigente de Ajustes: dono declarou no chat que não há pendentes; sem leitura/marcação pelo conector. P6 continua administrativa externa. Na 06, validar NUL/Unicode inválido no worker, pois a biblioteca pura poderá receber texto fora da proteção atual do DRF; saúde/autenticação S3 já verificadas, objeto e URL assinada ainda não.
- Próximo passo autorizado: commit/merge local da 05 e abertura da 06; planejamento preparatório em `/tmp/varal-06/` não é implementação entregue. Sem push.

### 16/11/2026 — Merge local da Etapa 04 e início da Etapa 05

- Revisão 04 em `8a0ca04`; merge local `--no-ff` na `main` em `fe48cbe`, após 235 pytest, 73 Vitest e 87 E2E verdes (3 skips previstos), lint, tipos determinísticos, comparação visual e segurança sem bloqueantes. Sem push.
- Criada `etapa/05-boleto-pix`. Spec, plano, tarefas, decisões e fontes em `docs/etapas/05-boleto-pix/`; execução autorizada pela delegação do dono para todas as etapas restantes. Conferência atual de Ajustes: declaração do dono de que não há pendentes, sem alegar leitura pelo conector.
- Parser preparado isoladamente por `varal-boletos` (GPT-6.1 Terra), com 59 testes puros verdes e revisão `varal-seguranca` (GPT-6 Astra) sem bloqueantes no parser; persistência, permissões e interface ainda precisam de integração e validação na 05.
- Política explícita de vencimentos antigo/atual e de Pix dinâmico em `decisoes.md`/`fontes.md`. P6 continua externa, sem categoria pelo ADR 0005. Próximo passo: integrar parser, instrumento e API, gerar tipos, integrar a interface e validar a fatia completa.

### 16/11/2026 — Revisão delegada da Etapa 04 concluída

- Decisões Q04-1–22, Q04-24/25 e Q04-31–39 fechadas sob delegação; Q04-23 e Q04-26–30 preservam as respostas anteriores. Nenhuma pergunta da 04 aguarda o dono. Q04-37 fica na 07 e P7 na 09.
- ADR 0009 separa prazo de selo: filtro/contagem de Vencidas inclui abertas `pendente` e `aguardando` vencidas; Aguardando conserva estado e selo. Detalhe inclui `quem_ve` efetivos, além de `acesso` editável; nomes individuais não ocultam a lista e espaços/casas revelam nome completo ao escolher.
- M2 corrigido com consulta central de contas visíveis sem caminho escolhido pela existência; M5 corrigido no Django admin de contas/históricos e na prévia de exclusão. M4 mantém a regra por contexto já respondida, sem lista geral nova ao pagador; M6 aceito só no ambiente de desenvolvimento até `make dev`.
- Revisão de segurança encontrou e corrigiu B1–B3: autorização antiga na criação, conversão pública → restrita concorrente à saída e releitura de dados após revogação de acesso. Criação serializa vínculos; RN32 trava todas as abertas; detalhe revalida após adquirir a trava e a mantém até serializar. Reauditoria final de segurança: sem bloqueantes.
- Lote direcionado de 21 regressões validado; seis reproduziram falha antes da correção. **`make test`: 235 pytest e 73 Vitest; lint verde; `make types` preservou hashes; E2E final: 87 passaram, 3 ignorados de propósito e nenhuma falha** (7,1 min). Na rodada anterior, 85 passaram e os dois `ca07` excederam 45 s; após análise do trace, só esse timeout passou a 75 s, sem retirar asserções. Na repetição, passou em 42,4 s mobile/33,8 s desktop.
- Frontend releu guia/tokens/`varal-ui`, HTML e screenshots de 02/D02, 07/D03, 10/D04, 05/M01 e 06/M02. `dec38` e `dec39` passaram nas duas larguras; QA revisou capturas com pessoas e destino completo visíveis, sem rolagem horizontal. Comparação estrutural com fixtures sintéticas, sem pixel a pixel; canvas preservado. Revisão pronta para merge local e continuidade da 05. Sem push.

### 15/11/2026 — Codex: análise para continuidade até a Etapa 11

- O dono delegou analisar e resolver as decisões pendentes e executar todas as etapas restantes de forma coerente, com agentes especializados. Essa autorização permite avançar entre etapas e resolver escolhas sem repetir pedidos genéricos de ok; não dispensa as fontes atuais obrigatórias.
- Conferido: `etapa/04-contas`, 17 commits fora da `main`, árvore limpa antes deste registro. Os resultados de testes anteriores são os do relatório; nenhuma suíte foi reexecutada nesta análise.
- Triagem inicial somente leitura com `varal-decisor`, preservada em [decisoes.md](etapas/04-contas/decisoes.md#triagem-preparatória-do-codex-15112026). Evoluiu para decisões finais delegadas após a conferência atual dos Ajustes pelo dono.
- **Conferência atual dos Ajustes pelo dono:** ao pedido do texto atual, respondeu "no varal ajustes n tem nenhum pendente". Registrada essa declaração atual, sem atribuí-la a leitura pelo conector nem reutilizar a revisão 24 como atual. Continuidade retomada com decisões delegadas e correções finais da 04 em andamento.
- **P6 permanece externa:** a reexportação da especificação sem categoria cabe ao Claude Code; a implementação segue o ADR 0005 já aprovado, sem acrescentar categoria por causa da cópia antiga. Deploy na VPS e push continuam sujeitos às autorizações explícitas próprias; este registro não os executa nem os considera autorizados.
- Próximo passo: registrar decisões finais/ADRs, aplicar e validar as correções da 04, atualizar relatório e matriz e fazer o merge local; depois seguir as etapas 05–11 na ordem do fluxo.

### 15/11/2026 — Revisão do dono da Etapa 04

- Respostas 23 (nome por contexto: membro atual pelo nome ou e-mail, quem saiu "Ex-membro", histórico sem e-mail) e 26 ("Precisa de atenção" com `aguardando` pela data) na API (4c9a1b2); 27–30 na web (3d4ba32): hero do D02 sem vazio (tokens `--hero-padding-y`, `--hero-varal-width`), detalhe mobile sem TabBar, `<Nome>` em uma linha, espaço atual primeiro em "Onde fica".
- Node 22 obrigatório (`web/.nvmrc`, `engines`, checagem no `make`); CI com `workflow_dispatch`; `make limpar-dev` criado e não executado (612aa34). Pendências Node local, CI mudo e banco de dev resolvidas; nova P9 (confirmar CI no próximo push).
- Codex usa os mesmos comandos e agentes (`AGENTS.md`, `make codex-sync`, d994907); agente `varal-decisor` e a política de decisões por custo de desfazer (4539db0). [decisoes.md](etapas/04-contas/decisoes.md) com respostas, D04-1 a D04-13 e as perguntas Q04-35 a Q04-39.
- QA (f78a878): `make test` 207 pytest + 73 Vitest; lint verde; tipos sem diff; E2E 83 passaram e 3 ignorados de propósito, a frio e sem 429.
- Merge na `main` aguarda o dono confirmar as decisões 1–22, 24, 25, os achados M2/M5/M6 (Q04-31, 33, 34) e Q04-35 a Q04-39. Sem push.

### 15/11/2026 — Etapa 04 (Contas, núcleo) concluída

- `Lancamento` e `Historico` sem categoria; visibilidade só por `acesso.py` (RN06 ao pé da letra, 404 para quem não vê, agregados só sobre o visível); status calculado em Fortaleza com a janela 1–7 (RN13, só admin). RN21 e RN32 nos dois modos, exceção da saída (ADR 0007) e acesso preservado (ADR 0008).
- Web: Início, Contas e Detalhe (02/D02, 03/07/D03), formulário em folha/modal com aviso de visibilidade, espaço atual por cookie, "Configurações" do grupo, folha de saída barrada, lista do pagador. Sete variáveis fora do Doop, nenhuma cor nova. Canvas não alterado.
- Segurança sem bloqueantes: I1 (corrida editar × sair, e o deadlock que ela revelou), I2 (histórico só com ids), M1, M3 e M7 corrigidos com testes; M2, M4, M5 e M6 aceitos.
- `make test` 204 pytest + 65 Vitest; lint verde; tipos sincronizados; E2E 74 passaram e 2 ignorados de propósito. P5 e P8 resolvidas; E2E final a frio sem 429.
- Ajustes rev 24 relidos ao vivo: 18 itens marcados, nenhum novo. 30 decisões a confirmar no [relatório](etapas/04-contas/relatorio.md#decisões-para-o-dono-confirmar). Sem push.

### 15/11/2026 — Respostas do dono às Q17–Q04-23/Q10-15 da Etapa 04

- **Q17 / ADR 0006 (RN32) revisto:** sair e excluir a própria conta seguem com 409; remoção pelo admin nunca bloqueia, cancela a restrita órfã ("cancelada automaticamente: ficou sem ninguém que pudesse vê-la") e não dá sinal nenhum ao admin. Aviso ao removido na 09 (P7). Nunca escalar a visibilidade para o admin.
- **ADR 0007 (Q18):** exceção à RN05 só dentro da saída barrada pela RN32 (acrescentar em "Quem vê" ou cancelar), com histórico.
- **ADR 0008 (Q19a):** acesso explícito (RN06) prevalece sobre a RN07; trocar alguém para pagador preserva o acesso à restrita que só ele vê. **Q19b:** editar deixando a conta sem ninguém → 400.
- Q20 (CU04 alternativo fora da 04), Q21 (admin só avisado/desfaz no que vê; anotado em 07 e 09) e Q04-23/Q10-15 (sem conta "pagas" no varal até a 07) como propostos. Q22: origem rev 50 sem categoria; reexportar na abertura da 05 (P6).
- Spec (CA01–CA34, sete CAs novos ou reescritos), plano, tarefas, regras, matriz e etapas atualizados. Sem código nem commit.

### 15/11/2026 — Ok do dono à Etapa 04, com correções

- Especificação reexportada da origem rev 47 (Claude Docs, aba "Tab 1"): única diferença é o RF11, agora "Definir espaço, subgrupo, pagador e visibilidade". Derivados: `requisitos/funcionais.md`, CU05 (nota), `dados/modelo.md` (nota e ER sem categoria), matriz.
- **ADR 0005:** RF11 sem categoria; categoria é da v3, sem campo nem tabela agora ou para depois.
- **ADR 0006 / RN32** (nova regra): sair, ser removido ou excluir a conta é bloqueado (409) se deixaria uma conta restrita aberta sem ninguém que a veja; calculado já com a RN21. Guarda em `_desligar` e no `pre_delete` de `Usuario`.
- Decisões na [spec](etapas/04-contas/spec.md#decisões-resolvidas-ok-do-dono-15112026): RN06 ao pé da letra (admin não entra; sem vazamento indireto; 404, não 403; pagador vê pela RN06); aviso "Quem paga também vê esta conta"; rótulo do mês nos totais; "Configurações" volta no D04 só para admin (nota datada no relatório da 03); sem barra de pagas até a 07. CAs renumerados (CA01–CA29).
- Guia `varal-ui` relido: igual ao registrado na Etapa 03. Canvas não alterado.
- Sete perguntas novas (Q17–Q04-23/Q10-15): resposta ao admin no 409 da RN32, último que vê sem poder editar, RN32 em alterar papel e editar, CU04 alternativo adiado pela 03, admin × restrita nas RN16/RN19/RN21, categoria ainda na origem (CU05 e seção 8), conta "pagas" do varal. Sem código nem commit.

### 15/11/2026 — Merge da Etapa 03 e preparação da Etapa 04 (Contas, núcleo)

- A pedido do dono: merge local da `etapa/03-espacos-grupos` na `main` (`--no-ff`), LICENSE proprietário (todos os direitos reservados) e push inicial no GitHub `luis-hm/Varal`. Criada `etapa/04-contas` a partir da `main`.
- "Varal — Ajustes" rev 24 lido ao vivo: nenhum item novo; D2 (conta cancelada) entra nesta etapa.
- `spec.md`, `plano.md` e `tarefas.md` em `etapas/04-contas/`. Frames 02, D02, 03, D03, 07, 05, M01, 06 e M02 lidos, todos draft; canvas não alterado.
- Proposto: visibilidade em `acesso.py` (`lancamentos_visiveis`), RN21 em `_desligar`, `criador` `SET_NULL` ("Ex-membro"), espaço atual por cookie, formulário manual direto. Dezesseis perguntas (Q1–Q16) com padrão; Q2 é divergência especificação × Doop (categoria sem campo). Código só depois do ok do dono.

### 15/11/2026 — Etapa 03 (Espaços e grupos) concluída

- Grupo sem dono, `Membro`, `Convite`, `Subgrupo`; migrações 0003–0005 sem perda de dados. Filtro central `acesso.py` (404 fora, 403 sem papel) com a RN05 completa; invariante ≥ 1 admin com `select_for_update` e guarda na exclusão de `Usuario`.
- Convite RN31: só SHA-256 no banco, uso único, 7 dias, revogável, 410 uniforme, 10 aceites/h por usuário. `/api/me/` com grupos; seed com os quatro papéis.
- Web: `/grupos`, `/grupos/[id]` (10 ↔ D04) em três níveis, `/grupos/[id]/simples`, `/c/[token]`, folha/modal `<dialog>`, convite 11 ↔ M05, seletor de espaço. Dez variáveis fora do Doop, nenhuma cor nova. Canvas não alterado.
- Segurança: **B1** (DRF aceitava HTTP Basic desde a Etapa 02, contornando limite de login e CSRF) e **I1** (admin desligado voltava com convite próprio) corrigidos com testes; M1–M3 corrigidos; M4–M6 registrados.
- `make test` 143 pytest + 57 Vitest; lint verde; tipos sincronizados; E2E 51 passaram e 1 ignorado de propósito. Uma execução seguida de outra suíte teve 3 falhas pelo limite de cadastro do allauth; reexecução 51/51 (P5).
- Ajustes rev 24 relidos ao vivo: nenhum item novo. Decisões a confirmar no [relatório](etapas/03-espacos-grupos/relatorio.md#decisões-para-o-dono-confirmar). Sem push.

### 14/11/2026 — Ok do dono à Etapa 03, com correções

- Oito decisões resolvidas na [spec](etapas/03-espacos-grupos/spec.md#decisões-resolvidas-ok-do-dono-14112026): telas sem frame pelo guia `varal-ui`; convite sem nome; página do grupo em três níveis (pagador vai para `/grupos/[id]/simples`, "Em breve" até a Etapa 10); grupo sem dono com pelo menos um admin sempre, inclusive na exclusão de conta; dados futuros escondidos.
- Regra nova **RN31** (link de convite: token só como hash, uso único, 7 dias, revogável, limite de aceite, link encurtado) pelo [ADR 0004](arquitetura/adr/0004-rn31-link-de-convite.md). Limite de 10 aceites por usuário por hora agora; por IP depois da P3. A confirmar no relatório: limite por usuário e rota do pagador.
- Doop relido: D04 e M05 ready_for_dev; 11 e M05 sem o campo de nome e com o link encurtado; M05 agora 560×480. Canvas não alterado. Cinco perguntas (Q1–Q5) com padrão provisório na spec.

### 14/11/2026 — Merge da Etapa 02 e preparação da Etapa 03 (Espaços e grupos)

- Merge local da `etapa/02-autenticacao` na `main` (`--no-ff`); criada `etapa/03-espacos-grupos`. Sem push.
- "Varal — Ajustes" rev 24 lido ao vivo: nenhum item desmarcado; "Variáveis do Google" marcado no documento remoto como feito na etapa 02.
- `spec.md`, `plano.md` e `tarefas.md` em `etapas/03-espacos-grupos/`. Frames 10 (`SfhuKVOQIF`), D04 (`5UzCB5yNaI`), 11 (`bkv_O9ohNO`) e M05 (`8XSFrkwy2d`) lidos, todos draft; canvas não alterado.
- Proposto: grupo sem `dono` (admin só por `Membro`), filtro central em `api/apps/espacos/acesso.py`, convite só por link. Oito decisões aguardam o ok do dono antes do código. Nova pendência P4 (HTTPS interno em produção).

### 13/11/2026 — Etapa 02 (Autenticação) concluída

- Cadastro/login por e-mail ou Google, recuperação por link com envio Celery, saída e dados próprios. Espaço pessoal automático/único, migração dos usuários anteriores e username interno compatível com admin/seed.
- UI mobile/desktop do Doop, estados aprovados, shell com sessão/dados reais e saída em Perfil. Canvas somente leitura; senha vazia com placeholder em vez dos bullets preenchidos do exemplo.
- Allauth 65.22.0 integrado ao schema DRF validado; `make types` com exportação composta e tipos sincronizados. Regeneração final preservou os hashes dos dois arquivos.
- Revisão de segurança sem bloqueantes; URL Google malformada que provocava 500 foi reproduzida, corrigida e coberta por três casos do endpoint real.
- Google real conferido até a tela oficial de entrada para Varal; sem autenticar conta externa. Callback completo coberto com HTTP externo simulado. Retorno OAuth 8000 e origem 3000 preservados.
- Anexo de ajustes relido; único item Google implementado, registrado como feito no relatório local. Documento remoto permanece sem marcação por falta do conector.
- `make test`: API 31/31 e Vitest 39/39; lint verde; E2E integral 38/38. Build final passou (14 páginas). Smoke de produção 4/4, regressão HTTP 404 da vitrine 2/2, fluxo central após extração da guarda 2/2 e vitrine em desenvolvimento 12/12.
- Corrigidos também o HTTP 200 indevido da página 404 em streaming, a confirmação de recuperação sobrescrita pela chave consumida e a perda de e-mail antes da hidratação. O fluxo central final passou 2/2 com verificação permanente de controles desabilitados no SSR e habilitados após hidratar; logs sem erros `instant`/hidratação.
- Recuperação real conferida no build final com conta descartável: token válido gerado localmente, senha alterada, chave consumida rejeitada sem apagar confirmação e entrada com a nova senha. Sem envio de e-mail externo nem exposição do token.
- Relatório em `etapas/02-autenticacao/relatorio.md`; matriz atualizada com testes reais. Etapa 03 segue pendente; sem push.

### 13/11/2026 — Execução autorizada da Etapa 02

- Dono respondeu **ok** ao resumo da preparação. Aprovados cadastro/recuperação no layout de autenticação existente e animação mobile conforme o guia (`translateY(100%)`, `0,5s`), usando os frames apresentados sem alterar o Doop.
- Iniciada execução das tarefas da Etapa 02; backend e contratos antes da integração frontend.

### 13/11/2026 — Preparação da Etapa 02 (Autenticação)

- Merge local da `etapa/01-design-system` na `main` com `--no-ff`, autorizado pelo `/etapa`; criada `etapa/02-autenticacao` a partir da `main`. Sem push.
- Planejamento de RF01–RF03, CU01 e RN03, incluindo o ajuste Google recebido no chat. `spec.md`, `plano.md` e `tarefas.md` em `etapas/02-autenticacao/`; implementação aguarda o **ok** do dono, conforme passo 4 do comando.
- Doop consultado em leitura: canvas, guia `varal-ui`, HTML e screenshots de 01 · Entrar (`GJDSPaQbio`, 390×844) e D01 · Entrar (`7JTmWMAJup`, 1440×900). Ambos ainda `draft`; nenhum frame modificado.
- Propostas para aprovação: cadastro e recuperação como estados do formulário existente (não há frames próprios); resolver divergência da animação da folha mobile entre o frame (40px, 0,6s) e o guia (100%, 0,5s) antes de implementá-la.
- Callback OAuth Google preservado na proposta: `http://localhost:8000/accounts/google/login/callback/`; origem `http://localhost:3000`. Não houve alteração de código de autenticação nem marcação do ajuste como feito.

### 13/11/2026 — Desbloqueio da Etapa 01

- Causa da falha: `.env` local usava um usuário diferente do único usuário de aplicação existente no volume PostgreSQL (`varal`). Validado acesso TCP com as credenciais de desenvolvimento documentadas; corrigidas apenas `POSTGRES_USER` e `POSTGRES_PASSWORD` no `.env` não versionado. Sem alteração de usuários ou dados do banco.
- `make test` passou (API 3/3; web 29/29); `make lint` já validado nesta sessão. CA17 completo, P2 resolvida; merge da Etapa 01 desbloqueado.
- Dono forneceu o texto de "Varal — Ajustes" no chat como alternativa ao conector indisponível. Fonte lida do anexo `Texto colado.txt`; não houve leitura ao vivo nem alteração do documento remoto. Único item pendente: variáveis do Google na Etapa 02.

### 13/11/2026 — Pré-verificação da Etapa 02 (Autenticação)

- Próxima etapa identificada: 02 (RF01–RF03, CU01, RN03; telas 01 · Entrar e D01). Permanece pendente.
- Docker disponível nesta sessão; `make lint` passou (ruff, ESLint e TypeScript). `make test` executou a API: 1 teste passou e 2 tiveram erro de autenticação no PostgreSQL; não chegou aos testes web. `make test-web` executado separadamente: 29/29 passaram. P2 continua bloqueando o merge da Etapa 01.
- Leitura ao vivo de "Varal — Ajustes" não realizada: conector Claude Docs indisponível nesta sessão; busca de plugins sem acesso correspondente e nenhuma sessão de documento conectada. Necessário disponibilizar a fonte ou autorizar uma alternativa antes de preparar a etapa.
- Sem merge, branch nova ou código da Etapa 02.

### 12/11/2026 — Etapa 01 (Design system no código)

- Tokens do Doop em `tokens.css` (com bloco "fora do Doop": 4 medidas de texto e 5 sombras via `color-mix`), fontes por `next/font/google`, logo e favicon.
- Componentes: Icon (29), Button 52px (D1), Chip, Field, StatusBadge com `cancelada` (D2), TopBar, TabBar/TabItem, SideNav/NavItem; AppShell com troca em 1024px (D3); animações `press` e `badge-pulse` com reduced motion.
- Vitrine `/dev/componentes` (404 em produção) e páginas "Em breve" em `/`, `/contas`, `/grupos`, `/avisos`, `/perfil`.
- Playwright 1.65.0, `make e2e`, job `e2e` no `web.yml`. Vitest 29/29, ESLint e `tsc` limpos, Playwright 26/26.
- CA17 parcial: `make test`/`make lint` sem Docker no WSL (P2). Sete desvios deliberados aguardam confirmação do dono ([relatório](etapas/01-design-system/relatorio.md#desvios-deliberados-pedir-confirmação-ao-dono)).
- Ajuste pendente para a Etapa 02: variáveis do Google (allauth).

### 12/11/2026 — Etapa 00 (ajustes do documento "Varal — Ajustes")

- Aplicados os 11 itens e as decisões D1–D6: documento de ajustes como fonte mais forte (CLAUDE.md, docs/README.md); `/etapa` lê os ajustes, faz a revisão de ajustes antes do relatório e o merge local da etapa anterior; especificação reexportada (seção 12 ganhou as telas desktop); páginas e frames desktop do Doop, regra responsiva, componentes NavItem/SideNav e animações modal-pop, slide-in e scan em `docs/design/`; agentes de frontend e QA nas duas resoluções; matriz com frame mobile ↔ desktop.
- Regras: **RN30** (LGPD) criada pelo [ADR 0003](arquitetura/adr/0003-rn30-exportar-e-excluir-dados.md); armazenamento S3 local pelo [ADR 0002](arquitetura/adr/0002-armazenamento-s3-local.md).
- Etapa 01 passa a incluir NavItem, SideNav, o shell responsivo e o StatusBadge `cancelada`; Etapa 11 inclui RNF04/RN30 e o armazenamento de produção.
- Merge local de `etapa/00-fundacao` na `main` (`--no-ff`), sem push.

### 12/11/2026 — Etapa 00 (Fundação)

- Criados: estrutura do monorepo, docs quebrados da especificação (cópia literal, diagramas em Mermaid), matriz de rastreabilidade, 7 subagentes, comandos `/etapa` e `/status`, `CLAUDE.md`.
- Esqueleto: Django 6.1 + DRF + drf-spectacular (`/api/health/`, `/api/schema/`, `/api/docs/`), Celery com tarefa `ping`, Next.js 16 chamando o healthcheck via proxy `/api`, Compose, Makefile, CI.
- Decisões: usuário próprio (`contas_usuario.Usuario`, UUID) desde já; DRF autenticado por padrão; proxy same-origin `/api` no Next; MinIO opcional (profile `storage`) até D4; nginx adiado para a Etapa 11 (deploy).
- Conectores: Claude Docs não foi necessário (a especificação já existia em `docs/`); Doop funcionando (canvas, guia `varal-ui`, tokens e componentes lidos).
- Verificação local ok (`make dev`, `make test`, `make lint`, `make types`, `make seed`); CI não rodou no GitHub (sem remoto). Relatório escrito em `etapas/00-fundacao/relatorio.md`; etapa concluída.
