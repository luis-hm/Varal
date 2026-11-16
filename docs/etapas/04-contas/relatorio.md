# Relatório — Etapa 04 (Contas, núcleo)

> **Contém:** entregas, CAs e testes, comparação com o Doop, segurança, ajustes, revisão do dono e decisões delegadas da Etapa 04.
> **Origem:** branch `etapa/04-contas` (entrega inicial e revisão do dono até f78a878), revisão delegada do Codex em 15–16/11/2026, QA, revisão `varal-seguranca`, [decisoes.md](decisoes.md) e conferência atual dos Ajustes fornecida pelo dono no chat; a revisão 24 pertence ao fechamento anterior.

**Estado: entrega inicial concluída em 15/11/2026; revisão delegada concluída em 16/11/2026, pronta para merge local.** O dono delegou ao Codex resolver as decisões e executar as etapas restantes, e confirmou no chat que não há ajustes pendentes. As decisões estão fechadas em [decisoes.md](decisoes.md); correções, testes, lint, tipos, inspeção visual e segurança estão validados. A tabela histórica da entrega anterior está separada das evidências pós-correção. Sem push.

## Entregas

- **Modelo (RF10, RF11, RN11, RN12, RN22, RN30):** `apps/lancamentos` com `Lancamento` (centavos > 0 e status válidos no banco, índice `(espaco, vencimento)`, `acesso` em `lancamento_acesso`) e `Historico`; sem categoria (ADR 0005). `criador`, `pagador` e autor do histórico `SET_NULL` ("Ex-membro"). Migrações `lancamentos.0001` e `espacos.0006` (janela 1–7, valores fora do intervalo ajustados sem perda); revisão delegada sem migração adicional. Admin do Django só leitura e filtrado pelo acesso efetivo. Detalhes em [modelo](../../dados/modelo.md#implementação-da-etapa-04).
- **Visibilidade (RN02, RN06, RN07, RNF01, ADR 0008):** `acesso.py` com `lancamentos_visiveis`, `lancamentos_do_usuario`, `lancamento_ou_404` (404 para quem não vê, 403 só para quem vê sem `editar_conta`) e `quem_ve`. Lista, detalhe, totais, contagens, `atencao`, `por_casa` e `opcoes` saem só do acesso autorizado. Admin do grupo e superusuário do Django não ganham visão de restrita por privilégio.
- **Status calculado (RN12, RN13, RNF11):** `com_status` anota `vence`/`vencida` sobre `pendente` com hoje em Fortaleza e a janela editável pelo admin. Filtro/contagens temporais incluem `aguardando` vencida ou na janela sem mudar seu selo ([ADR 0009](../../arquitetura/adr/0009-filtro-temporal-contas-abertas.md)); data resolvida por requisição.
- **Serviços:** criar, editar (histórico só do que mudou; 400 da Q19b), cancelar (só abertas; nada é apagado). RN21 e RN32 em `_desligar`: a saída voluntária bloqueia com 409 `conta_restrita_orfa` e aceita `resolucoes` (ADR 0007); a remoção pelo admin cancela a órfã sem sinal ao admin; a troca para pagador preserva o acesso (ADR 0008); a guarda `pre_delete` em `Usuario` bloqueia a exclusão.
- **API:** contas, `resumo`, `opcoes` na lista, `sair` com `resolucoes` e `usuario` no MembroSerializer ([api/README](../../api/README.md#contas-etapa-04)). Seed com os casos de visibilidade.
- **P5:** `ACCOUNT_RATE_LIMIT_SIGNUP` só no `make e2e` e no job `e2e` (1c17132); saiu o retry em 429 do E2E.
- **Web:** Início (02 ↔ D02) com "Total de <mês>", `count-up`, varal `swing` e "Precisa de atenção"; Contas e Detalhe (03/07 ↔ D03) com filtros na URL, folha "Filtros" no mobile e painel `slide-in`; formulário em folha/modal com o aviso "Quem paga também vê esta conta"; espaço atual em cookie (seletor no SideNav e no cabeçalho do Início); "Configurações" do grupo (só admin); folha de saída barrada pela RN32; lista do pagador em `/grupos/[id]/simples`; HouseCard com total e "N contas". BillCard novo; vitrine atualizada; linha do healthcheck removida.
- **Variáveis fora do Doop:** `--tracking-hero`, `--text-tag`, `--text-tag-desktop`, `--leading-small`, `--shadow-selected`, `--opacity-cancelled`, `--list-width` e, na revisão do dono, `--hero-padding-y` e `--hero-varal-width` (D04-2). Nenhuma cor nova ([tokens](../../design/tokens.md#fora-do-doop)).

## Critérios e testes

**CA01–CA37 validados na revisão:** a entrega anterior cobriu CA01–CA34; a revisão acrescenta CA35–CA37 e suas regressões. `make test`, lint, tipos e reexecução E2E integral passaram. Nomes completos na [matriz](../../matriz-rastreabilidade.md). Testes em `api/tests/test_contas.py`, `web/src/**/*.test.ts(x)` e `web/e2e/contas.spec.ts` (API e PostgreSQL reais).

| CA | Evidência principal |
| --- | --- |
| CA01–CA04 | `test_rf10_*`, `test_rn11_*`, `test_rn05_contas_por_papel`, `test_rf11_casa_pagador_e_escolhidos_validados`, `test_rn01_rf11_editar_com_dados_de_outro_grupo_400_e_nada_grava`; E2E `ca01/ca16/ca17/ca31…` |
| CA05–CA09 | `test_rn02_*`, `test_rn01_rnf01_*`, `test_rn06_admin_nao_escolhido_404_e_agregados_sem_a_conta`, `test_rn06_pagador_nao_escolhido_ve_a_conta`, `test_rn07_*`, `test_rn06_rn07_acesso_explicito_prevalece`; E2E `ca07/ca08/ca09/ca28…` |
| CA10–CA11 | `test_rn12_*`, `test_rnf11_hoje_em_fortaleza`, `test_rn13_*` (inclui `test_rn13_atencao_inclui_aguardando_na_janela`); E2E `ca11 rn13 q10…` |
| CA12–CA17 | `test_rn22_*`, `test_d2_*`, `test_rf13_*`; Vitest `inicio.test.tsx`, `contas.test.ts`; E2E `ca12/ca13/ca14…`, `ca15…`, `dec27` |
| CA18–CA25 | `test_rn21_*`, `test_rn32_*` (inclui `concorrencia_editar_e_sair` e `concorrencia_excluir_conta_e_remocao_admin`, com threads), `test_rn05_rn32_*`, `test_rn06_rn07_alterar_papel_preserva_acesso`; E2E `ca19/ca22/ca23…`, `ca20/ca21/ca22…` |
| CA26 | `test_rn30_criador_excluido_ex_membro`, `test_rn30_historico_sem_email_ex_membro_apos_saida_ou_exclusao`, `test_rn30_nome_por_contexto_membro_sem_nome_ex_membro`; E2E `dec23` |
| CA27–CA32 | Vitest `nav.test.tsx`, `conta-folha.test.tsx`, `app-shell.test.tsx`, `nome.test.tsx`; E2E `ca27…`, `ca29…` (screenshots), `ca30…`, `ca32…` (360px, movimento reduzido), `dec28`–`dec30` |
| CA33 | `make types` sem diff |
| CA34 | Tabela abaixo; segurança sem bloqueantes; docs e matriz atualizadas |

| Verificação da entrega anterior (f78a878, Node 22, API fria) | Resultado histórico |
| --- | --- |
| `make test` | **207 pytest e 73 Vitest passaram** (no fechamento: 204 e 65) |
| `make lint` | **Passou** (ruff, ESLint, `tsc`) |
| `make types` | **Sem diff** |
| `make e2e` | **83 passaram, 3 ignorados de propósito** (360px só no mobile; `dec27` só no desktop); nenhum 429 |

### Validação da revisão delegada (16/11/2026)

O lote direcionado de 21 regressões passou; seis casos reproduziram falhas antes da correção. Cobertura inclui criação com autorização antiga, criação concorrente com desligamento/exclusão, conversão pública → restrita durante saída/remoção, snapshot do detalhe e resposta da própria mutação. Os testes de espera do GET após PATCH comprovam a espera real no PostgreSQL, não apenas uma ordem artificial de chamadas.

| Verificação pós-correção | Estado atual |
| --- | --- |
| `make test` integral | **235 pytest e 73 Vitest passaram** |
| `make lint` | Passou (ruff, ESLint e `tsc`) |
| `make types` | Regeneração final preservou os hashes do OpenAPI e dos tipos |
| `make e2e` integral | **87 passaram, 3 ignorados de propósito; nenhuma falha** (7,1 min) |
| Inspeção visual dos novos fluxos | `dec38`/`dec39` passaram e screenshots revisados em mobile e desktop |
| Segurança | Reauditoria final sem bloqueantes após as correções B1–B3 |

CA35: `test_rn01_rn05_criar_revalida_vinculo_apos_autorizacao` e `test_rn01_rn21_rn32_criacao_serializa_vinculos_com_desligamento`. CA36: `test_rn32_concorrencia_grupo_para_restrita_e_saida`. CA37: `test_rn06_detalhe_revalida_acesso_na_consulta_que_carrega_dados`, `test_rn06_detalhe_mantem_snapshot_ate_prefetch_e_historico`, `test_rn06_resposta_propria_edicao_nao_le_edicao_alheia_posterior` e `test_rn06_detalhe_espera_edicao_e_rele_acesso_em_snapshot_novo`.

Na primeira validação integral desta revisão, **85 E2E passaram, 3 foram ignorados e 2 falharam por timeout do `ca07`**, um em cada resolução. Esse teste longo, com quatro contas e três contextos, excedeu os 45 s sem falha de asserção de produto; nenhuma outra falha ocorreu. Após inspecionar o trace, o QA limitou a mudança ao timeout desse teste (75 s), preservando asserções. Na repetição integral verde, o caso passou em 42,4 s no mobile e 33,8 s no desktop.

**Registro honesto do E2E:** uma execução anterior teve um 429 isolado no primeiro cadastro, na partida a frio da API recriada pelo `make e2e` (o `cache_lock` do allauth espera 1 s no Redis), e duas medições feitas durante animações. Resolvido (P8, e39c115): o `globalSetup` do Playwright faz um cadastro sozinho antes dos workers, e as medições esperam `modal-pop`/`sheet-up` terminarem. Na revisão do dono, o Vitest `ca28` estourava o `findBy` de 1 s sob carga; a espera passou a 5 s, com justificativa no arquivo (f78a878).

**Correções do QA (19fb5fe):** Chip com rótulo longo trunca com reticências e `title`; a vitrine `/dev/componentes` não rola mais em 360px; E2E `grupos` e `auth` ajustados ao Início, ao HouseCard e ao seletor por cookie; helpers movidos para `web/e2e/fixtures.ts`.

## Comparação com o Doop (CA29)

Screenshots `web/e2e/__screens__/` (`inicio-*`, `contas-*`, `conta-detalhe-*`, `conta-form-*`, `grupo-*`) comparados com 02/D02, 03/D03, 07, 05/M01, 06/M02 e 10/D04 em 390×844 e 1440×900. Composição, componentes, cores, fontes e espaçamentos correspondem, exceto as diferenças esperadas da [spec](spec.md#telas-do-doop) e estas, que continuam:

1. **03 mobile:** "Total de novembro: R$ … · espaço" quebra em 2 linhas (efeito da Q9).
2. **D03:** os chips de filtro quebram em 2 linhas por causa de "Canceladas" e "Quem paga".
3. O campo de data aparece em mm/dd/yyyy no Chromium en-US do Playwright (o formato segue o idioma do navegador).

As diferenças 1 (vazio no hero do D02), 4 (TabBar no 07), 5 (nomes em várias linhas) e 6 (ordem de "Onde fica") do fechamento viraram as decisões 27–30, respondidas pelo dono e implementadas em 3d4ba32 ([revisão do dono](#revisão-do-dono)). Canvas não alterado.

Na revisão delegada, o frontend releu ao vivo guia, tokens, `varal-ui`, HTML e screenshots de 02/D02, 07/D03, 10/D04, 05/M01 e 06/M02. Q04-38 mostra cada pessoa efetiva da restrita, com quebra entre nomes e sem cortar a lista. Q04-39 permite duas linhas nos nomes de espaços/casas e revela o nome inteiro por toque/teclado antes de salvar. São exceções documentadas de apresentação; nenhuma aprovação ou alteração do canvas foi feita. Os novos E2E `dec38` e `dec39` passaram nas duas larguras, verificando lista completa/deduplicada e grupos com prefixos iguais. O QA revisou `dec38-quem-ve-{mobile,desktop}.png` e `dec39-espaco-identificado-{mobile,desktop}.png`: pessoas e destino completo visíveis, sem rolagem horizontal. A comparação com os frames confirmou estrutura e hierarquia adequadas ao escopo manual, com recursos futuros ausentes; usou fixtures sintéticas e inspeção visual, sem comparação pixel a pixel.

## Segurança

Revisão inicial `varal-seguranca`: **sem bloqueantes naquele fechamento**. A revisão delegada encontrou B1–B3 adicionais, corrigidos com regressões; a reauditoria final de segurança em 16/11/2026 ficou **sem bloqueantes**. O QA integral pós-correção também passou; a revisão está pronta para o merge local.

- **I1 (corrigido):** corrida entre editar a conta (tirando-se de "Quem vê" e pondo X) e a saída ou remoção de X deixava uma restrita aberta sem ninguém. A entrega inicial passou a travar todas as restritas abertas antes de calcular órfãs; a revisão B2 ampliou a trava a todas as abertas, inclusive públicas. A correção inicial revelou um segundo deadlock (`FOR UPDATE` do `Usuario` pelo `select_related` × FK deferida da edição), corrigido com `select_for_update(of=("self",))`. Teste `test_rn32_concorrencia_editar_e_sair` (sair e remover).
- **I2 (corrigido):** o histórico gravava e-mail ou nome. Agora `dados` guarda ids e a leitura resolve os nomes ("Pessoa sem nome"/"Ex-membro", nunca e-mail). Teste `test_rn30_historico_sem_email_ex_membro_apos_saida_ou_exclusao`.
- **M1 (corrigido):** deadlock entre excluir a conta de usuário e o admin remover. Ordem única de travas: admins → membro → contas. Teste `test_rn32_concorrencia_excluir_conta_e_remocao_admin`.
- **M3 (corrigido):** `resolucoes` sem limite; agora no máximo 50.
- **M7 (corrigido):** faltava teste de PATCH com casa, pagador ou escolhido de outro grupo. Teste `test_rn01_rf11_editar_com_dados_de_outro_grupo_400_e_nada_grava`.
- **M2 (Q04-31, corrigido nesta revisão):** consulta de conta visível centralizada; inexistente e invisível seguem o mesmo caminho estrutural, preservando 404 uniforme. Não há promessa de tempo constante nem dependência da aleatoriedade do UUID como controle.
- **M4 (Q04-32/Q04-36, ratificado por delegação):** nome/e-mail de membro atual continua pela regra por contexto já respondida; o detalhe contém pessoas da conta autorizada e o 409 da saída contém só candidatos elegíveis necessários à resolução. Não cria lista geral de membros ao pagador; ex-membro nunca aparece pelo e-mail.
- **M5 (Q04-33, corrigido nesta revisão):** admin do Django filtra lançamentos e históricos pelo acesso central, inclusive para superusuário. A confirmação de exclusão de usuário omite contas/históricos, contagens e descrições de restritas; mantém guardas RN04/RN32 e mensagem genérica de pendências. Isso não restringe o acesso direto do operador da infraestrutura ao banco.
- **M6 (Q04-34, aceito temporariamente por delegação):** o container `api` de desenvolvimento conserva `ACCOUNT_RATE_LIMIT_SIGNUP` do E2E até o próximo `make dev`; verificar isolamento antes de produção.
- **B1 (corrigido):** criar com autorização obtida antes de saída/remoção/rebaixamento podia gravar autor ou escolhidos já desligados. Criação trava admins/membro e revalida vínculo e permissão antes de gravar; exclusão de usuário serializa todos os grupos em que participa.
- **B2 (corrigido):** converter uma conta pública em restrita durante a saída/remoção podia contornar a RN32. O desligamento trava todas as abertas em ordem de chave, inclusive públicas, e avalia órfãs após a espera.
- **B3 (corrigido):** detalhe autorizado antes de uma revogação podia reler novos dados já restritos. GET adquire a trava, consulta acesso em novo comando e mantém a trava até carregar relações/histórico e serializar; mutações mantêm transação/travas até construir a resposta da própria operação, inclusive quando o autor retira seu acesso.

## Desvios em relação ao plano

- Ação nova `acesso_removido` no histórico (RN21 tirando alguém de "Quem vê"); o plano só previa `pagador_removido`.
- Opções dos filtros "Casa" e "Quem paga" vêm do campo `opcoes` da lista (`casas`, `pagadores`, `sem_pagador`), calculado só sobre o visível do mês. Não é endpoint próprio.
- `MembroSerializer` ganhou `usuario` (id do usuário), usado em "Quem paga" e "Quem vê".
- `Historico.dados` com ids de usuário em vez de nomes (I2).
- Revisão do dono: componente `<Nome>` (`web/src/components/ui/nome.tsx`), fora do Doop, para nomes e e-mails em uma linha (decisão 29).
- Revisão delegada: `quem_ve` somente leitura para audiência efetiva, separado de `acesso` editável; filtro temporal de abertas pelo ADR 0009; apresentação Q04-38/Q04-39 e reforço transacional dos CA35–CA37.

## Ajustes aplicados

Nenhum item novo do documento remoto. No fechamento anterior, a revisão 24 havia sido lida pelo Claude Code. Na execução atual, ao pedido de conferência, o dono respondeu no chat: **"no varal ajustes n tem nenhum pendente"**. O Codex não dispõe do conector Claude Docs: não houve leitura nem marcação remota nesta revisão, e a revisão 24 não foi tratada como atual.

## Ajustes pendentes

Nenhum, conforme a declaração atual do dono. **Itens a marcar como " — feito na etapa 04": nenhum.** P6 é pendência de reexportação da especificação, distinta do documento de Ajustes.

## Revisão do dono

Respostas de 15/11/2026 ("Etapa 04 aprovada"), nas palavras dele em [decisoes.md](decisoes.md#respostas-do-dono-15112026-mensagem-etapa-04-aprovada).

| Decisão | Resposta | O que foi feito |
| --- | --- | --- |
| 23 · nome de pessoa | Por contexto: membro atual pelo nome ou, sem nome, pelo e-mail; quem saiu ou excluiu a conta é "Ex-membro", nunca o e-mail; histórico com id e nome resolvido na hora | 4c9a1b2: `rotulo` por contexto no detalhe, na lista, nas opções e no 409. Histórico mostra "Pessoa sem nome" ou "Ex-membro", inclusive nas linhas automáticas; quem volta ao grupo volta pelo nome (D04-8, D04-9). Testes `test_rn30_*` e E2E `dec23` |
| 26 · `aguardando` em "Precisa de atenção" | Entra toda conta aberta, `pendente` ou `aguardando`, vencida ou dentro da janela da RN13; o selo mostra o status real | 4c9a1b2: atenção e hero pela data. Revisão delegada Q04-35/ADR 0009 aplica o mesmo critério ao chip/filtro Vencidas, preservando o selo; regressão `test_rn12_rf13_vencidas_abertas_por_data_sem_mudar_selo` |
| 27 · vazio no hero do D02 | Corrigir agora; o container encolhe sem a barra | 3d4ba32: hero em grade de 2 colunas sem altura fixa, varal de 560px à direita, pílula "N contas" mantida (D04-1 a D04-3); tokens `--hero-padding-y` e `--hero-varal-width`. E2E `dec27` |
| 28 · TabBar no detalhe mobile | Tirar; detalhe é tela empilhada, com TopBar e voltar | 3d4ba32: `/contas/[id]` abaixo de 1024px sem TabBar, com TopBar e voltar também em carregando, erro e "Conta não encontrada" (D04-4). Vitest `app-shell.test.tsx`; E2E `dec28` |
| 29 · nomes e e-mails longos | Uma linha com reticências, valor inteiro no `title`/aria; testar com e-mail longo | 3d4ba32: `<Nome>` e corte equivalente no shell. Vitest `nome.test.tsx`; E2E `dec29` com e-mail longo. Revisão delegada Q04-38 permite quebra entre pessoas e Q04-39 distingue nomes de espaço/casa, com revelação completa ao escolher |
| 30 · ordem em "Onde fica" | Espaço atual primeiro e já selecionado | 3d4ba32: `espacosParaCriar` ordena pelo espaço atual; observador mantém a ordem e seleciona o primeiro; edição fica no espaço da conta (D04-7). Vitest `conta-folha.test.tsx`; E2E `dec30` |

Na mesma mensagem: Node 22 (D04-12), CI com `workflow_dispatch` (D04-13) e `make limpar-dev` (D04-11), em 612aa34. Fora da etapa: Codex com os mesmos comandos e agentes (d994907) e o agente `varal-decisor` (4539db0).

<a id="decisões-para-o-dono-confirmar"></a>

## Decisões delegadas e fechamento da revisão

O dono delegou a resolução das decisões e a continuidade de todas as etapas. O [registro de decisões](decisoes.md#conferência-atual-e-decisões-delegadas-do-codex-15112026) fecha Q04-1–22, Q04-24/25 e Q04-31–39; Q04-23 e Q04-26–30 preservam as respostas anteriores. Não há pergunta da 04 aguardando resposta do dono.

As correções de prazo (ADR 0009), consulta uniforme do 404, minimização do admin, audiência efetiva em `quem_ve` e apresentação de nomes/espaços estão implementadas e validadas pelo QA integral e pela inspeção visual. Q04-37 entra na 07 e P7 permanece na 09.

A revisão de segurança encontrou os três bloqueantes de concorrência B1–B3, corrigidos e reauditados sem bloqueantes. O lote direcionado e a validação integral do código atual passaram, com resultados próprios registrados acima. Merge local e abertura da 05 seguem a autorização vigente do dono; não houve push.

## Pendências

- **P6 (externa):** Claude Code reexporta a origem rev 50 sem categoria e confere derivados/ADR 0005; Codex não edita a origem. O ADR 0005 já autoriza continuar a implementação sem categoria, mesmo com a cópia local defasada.
- **P7 (Etapa 09):** aviso ao removido das contas canceladas pela RN32 (decisão 25).
- **P8:** aberta e resolvida nesta etapa (veja o registro do E2E).
- **P9:** confirmar no próximo push que o CI dispara (`gh run list`; se nada aparecer, `gh workflow run web.yml --ref main`). Causa e correção em [PROGRESSO](../../PROGRESSO.md#resolvidas).
- **P1 resolvida:** serviço S3 local iniciado com a tag prevista, saúde HTTP 200 e autenticação real verificada sem exibir credenciais. Upload/download e URLs assinadas serão validados na 06.
- **P3 e P4:** proxies confiáveis, HTTPS interno e logs de convite continuam para o deploy da 11.
- **Banco de dev:** `make limpar-dev` existe e não foi executado; o dono roda quando quiser. A prévia apagaria 5 grupos de teste, 302 grupos sem membros e 858 usuários de teste.
- **Sem push:** nada desta etapa foi enviado ao remoto.
