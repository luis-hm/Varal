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
| 06 | PDF do boleto | concluída; definição de pronto alcançada, pronta para commit e merge local | `etapa/06-pdf-boleto` | — | [relatorio](etapas/06-pdf-boleto/relatorio.md) |
| 07 | Pagamento | pendente | — | — | — |
| 08 | Recorrência e agendador | pendente | — | — | — |
| 09 | Notificações | pendente | — | — | — |
| 10 | Solicitação e modo simples | pendente | — | — | — |
| 11 | Acabamento e deploy | pendente | — | — | — |

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
| P7 | Entregar ao removido o aviso das contas canceladas pela RN32 na remoção pelo admin ([ADR 0006](arquitetura/adr/0006-rn32-conta-restrita-orfa.md)). A Etapa 04 grava `cancelada_automaticamente` com `dados.removido`; entrega na 09 ratificada por delegação em Q04-25. | Etapa 09 |
| P9 | Confirmar que o CI dispara no próximo push: `gh run list`; se nada aparecer, `gh workflow run web.yml --ref main`. Causa provável e correção em "CI mudo" (Resolvidas). | Nada (verificação) |
| P10 | Perfil da Etapa 11: pergunta enviada ao dono sobre montar dados/preferências/exportar/excluir/sair com `varal-ui` ou receber frame Doop, conforme ADR 0003. Ainda sem resposta; não mudar o desenho por silêncio. | Definição da tela Perfil na 11; não bloqueia 06–10 |
| P11 | Destino da implantação: pergunta enviada ao dono entre validação local e VPS com domínio/alias SSH. Ainda sem resposta nem autorização de deploy na VPS; preparar/testar localmente não equivale a implantar. Não solicitar segredos no chat. | Implantação efetiva da 11; não bloqueia 06–10 ou preparação independente |

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
| CI mudo | O CI não disparou no GitHub no push inicial | Causa provável (inferência; o GitHub não mostra o motivo): o push inicial levou todas as branches a um repositório vazio, como branches novas com commit raiz sem pai, e o filtro `paths` não casou nada; o segundo push só mexia em LICENSE, fora do filtro. Correção: `workflow_dispatch` em `api.yml` e `web.yml` (612aa34). Verificação no próximo push: P9. | [stack](arquitetura/stack.md#decisões-de-implementação) |
| Banco de dev | Dados de teste antigos no banco de dev | Resolvida em 15/11/2026: `make limpar-dev` existe, com prévia e confirmação; não foi executado, o dono roda quando quiser (a prévia apagaria 5 grupos de teste, 302 grupos sem membros e 858 usuários de teste). | [stack](arquitetura/stack.md#decisões-de-implementação) |

## Log

Ordem cronológica inversa.

### 16/11/2026 — Etapa 06 concluída, pronta para commit e merge local

- Documento/PDF manual, spool privado, Celery e processo dedicado integrados; I/O real por django-storages. Tentativa UUID, mutex e intenção persistida protegem execução antiga, limpeza e rollback. No-op de metadados corrigido com regressões.
- **390 pytest, 89 Vitest e 97 E2E passaram, com 3 skips previstos; lint e tipos determinísticos verdes.** Provas reais de S3/Celery/assinatura/cleanup e inspeção headed do PDF/fallback em mobile/desktop passaram. Ajustes preliminares de popup/controle de arquivo foram conferidos com Tab real; repetição integral final com exit 0 e sem servidor Next próprio remanescente.
- Segurança Astra sem bloqueantes por leitura; auditoria sem perguntas/decisões pendentes. Resultado final e matriz no [relatório](etapas/06-pdf-boleto/relatorio.md). Definição de pronto alcançada; commit e merge local pendentes do orquestrador. Sem push.
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

### 15/11/2026 — Respostas do dono às Q17–Q23 da Etapa 04

- **Q17 / ADR 0006 (RN32) revisto:** sair e excluir a própria conta seguem com 409; remoção pelo admin nunca bloqueia, cancela a restrita órfã ("cancelada automaticamente: ficou sem ninguém que pudesse vê-la") e não dá sinal nenhum ao admin. Aviso ao removido na 09 (P7). Nunca escalar a visibilidade para o admin.
- **ADR 0007 (Q18):** exceção à RN05 só dentro da saída barrada pela RN32 (acrescentar em "Quem vê" ou cancelar), com histórico.
- **ADR 0008 (Q19a):** acesso explícito (RN06) prevalece sobre a RN07; trocar alguém para pagador preserva o acesso à restrita que só ele vê. **Q19b:** editar deixando a conta sem ninguém → 400.
- Q20 (CU04 alternativo fora da 04), Q21 (admin só avisado/desfaz no que vê; anotado em 07 e 09) e Q23 (sem conta "pagas" no varal até a 07) como propostos. Q22: origem rev 50 sem categoria; reexportar na abertura da 05 (P6).
- Spec (CA01–CA34, sete CAs novos ou reescritos), plano, tarefas, regras, matriz e etapas atualizados. Sem código nem commit.

### 15/11/2026 — Ok do dono à Etapa 04, com correções

- Especificação reexportada da origem rev 47 (Claude Docs, aba "Tab 1"): única diferença é o RF11, agora "Definir espaço, subgrupo, pagador e visibilidade". Derivados: `requisitos/funcionais.md`, CU05 (nota), `dados/modelo.md` (nota e ER sem categoria), matriz.
- **ADR 0005:** RF11 sem categoria; categoria é da v3, sem campo nem tabela agora ou para depois.
- **ADR 0006 / RN32** (nova regra): sair, ser removido ou excluir a conta é bloqueado (409) se deixaria uma conta restrita aberta sem ninguém que a veja; calculado já com a RN21. Guarda em `_desligar` e no `pre_delete` de `Usuario`.
- Decisões na [spec](etapas/04-contas/spec.md#decisões-resolvidas-ok-do-dono-15112026): RN06 ao pé da letra (admin não entra; sem vazamento indireto; 404, não 403; pagador vê pela RN06); aviso "Quem paga também vê esta conta"; rótulo do mês nos totais; "Configurações" volta no D04 só para admin (nota datada no relatório da 03); sem barra de pagas até a 07. CAs renumerados (CA01–CA29).
- Guia `varal-ui` relido: igual ao registrado na Etapa 03. Canvas não alterado.
- Sete perguntas novas (Q17–Q23): resposta ao admin no 409 da RN32, último que vê sem poder editar, RN32 em alterar papel e editar, CU04 alternativo adiado pela 03, admin × restrita nas RN16/RN19/RN21, categoria ainda na origem (CU05 e seção 8), conta "pagas" do varal. Sem código nem commit.

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
