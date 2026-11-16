# Spec — Etapa 04 (Contas, núcleo)

> **Contém:** escopo, requisitos, ajustes, telas, decisões resolvidas (Q1–Q23), critérios de aceite e fora de escopo da Etapa 04.
> **Origem:** [etapas](../README.md), RF10–RF13 (RF11 da origem rev 47, [ADR 0005](../../arquitetura/adr/0005-rf11-sem-categoria.md)), [CU05](../../casos-de-uso/CU05-cadastrar-conta.md) (só o manual), [CU06](../../casos-de-uso/CU06-consultar-contas.md), [CU07](../../casos-de-uso/CU07-editar-ou-cancelar-conta.md), RN01–RN02, RN05–RN07, RN11–RN13, RN21, RN22, RN30 ([ADR 0003](../../arquitetura/adr/0003-rn30-exportar-e-excluir-dados.md)), RN32 ([ADR 0006](../../arquitetura/adr/0006-rn32-conta-restrita-orfa.md)), exceção à RN05 ([ADR 0007](../../arquitetura/adr/0007-rn05-excecao-saida-rn32.md)), RN06 sobre RN07 ([ADR 0008](../../arquitetura/adr/0008-rn06-prevalece-sobre-rn07.md)), D2, [modelo](../../dados/modelo.md), [design](../../design/README.md), [relatório da Etapa 03](../03-espacos-grupos/relatorio.md), "Varal — Ajustes" rev 24 e Doop (guia `varal-ui`, frames abaixo) lidos em 15/11/2026; ok do dono com correções em 15/11/2026 e respostas às Q17–Q23 no mesmo dia; guia `varal-ui` relido no mesmo dia.

## Escopo

- **Conta manual** (lançamento) por espaço: criar, ver, editar, cancelar; histórico com autor e data. Sem código, PDF, pagamento, recorrência nem categoria.
- **Visibilidade no backend** em `api/apps/espacos/acesso.py`, ponto único: listas, detalhe, totais, contagens, chips, "Precisa de atenção", "Por casa"/HouseCard e opções de filtro saem só daí (RNF01). Conta que o usuário não vê = **404**, nunca 403.
- **Status:** gravados `aguardando|pendente|paga|confirmada|cancelada`; "vence em breve" e "vencida" calculados na consulta com `espaco.janela_alerta_dias` e hoje em America/Fortaleza.
- **Telas:** Início (02 ↔ D02), Contas (03 ↔ D03), Detalhe (07 ↔ painel do D03), formulário de conta (partes de 05/06 ↔ M01/M02), "Configurações" do grupo (D04/10, só admin). FAB "+" e "Nova conta" do SideNav ganham ação. `/` perde a linha do healthcheck.
- **Espaço atual** escolhido no seletor (SideNav e cabeçalho do Início mobile), guardado em cookie.
- **RN21** e **RN32** nas contas, em `espacos.servicos._desligar` (sair bloqueia; remoção pelo admin cancela), na guarda `pre_delete` de `Usuario`, em `alterar_papel` (ADR 0008) e na edição (Q19b). **RN13** editável pelo admin.

| Requisito | Entrega nesta etapa |
| --- | --- |
| RF10 / CU05 / RN11 | Conta manual: descrição, valor (centavos, > 0), vencimento; nasce `pendente` |
| RF11 / CU05 / RN01 / RN06 | Espaço (na criação, não muda depois), casa, pagador, visibilidade (`grupo` ou `restrita` com pessoas escolhidas). Sem categoria (ADR 0005) |
| RF12 / CU07 / RN22 | Editar (só quem tem `editar_conta`, conta não cancelada) e cancelar (só `aguardando`/`pendente`); nada é apagado; cada mudança vai ao histórico |
| RF13 / CU06 / RN12 / RN13 | Lista por mês com filtros status, casa, pagador; Início com total do mês (rótulo do mês) e "Precisa de atenção" |
| RN02 / RN06 / RN07 | Pessoal só o dono; restrita só criador, pagador e escolhidos (**admin não entra por ser admin**); pagador do grupo só as dele, **exceto restrita com acesso explícito** (ADR 0008) |
| RN05 / ADR 0007 | Criar/editar/cancelar: dono, admin, membro. Observador e pagador só veem; única exceção: resolver, na própria saída barrada pela RN32, a conta que só ele vê |
| RN21 | Quem sai deixa as contas que criou; as abertas em que era pagador ficam sem pagador; aviso ao admin na 09 (só das contas que ele vê, Q21) |
| RN32 / ADR 0006 | Sair ou excluir a própria conta de usuário: 409 se deixaria uma restrita aberta sem ninguém que a veja. Remoção pelo admin: nunca bloqueia; a conta órfã é cancelada automaticamente, sem sinal ao admin |
| RN30 / ADR 0003 | `criador` e autor do histórico `SET_NULL`; exibidos como "Ex-membro" quando nulos. Exclusão de conta na 11 |
| D2 | Cancelada fora do Início, das listas padrão, dos totais e das contagens; só no filtro "Canceladas" e no histórico; card com valor riscado e opacidade |

## O que "paga/confirmada" e boleto/Pix/PDF fazem aqui

- Nenhum fluxo cria `paga`/`confirmada` (Etapa 07). O código já os trata: entram no filtro "Pagas" e não podem ser canceladas (409). **Nenhuma barra de pagas aparece até a 07** (Q12).
- `aguardando` só nasce de recorrência variável (Etapa 08); é exibido se existir (seed), mas o formulário não o cria. As Etapas 05/06 passam a oferecer código/PDF, sem criar por isso uma conta `aguardando` avulsa. Sua leitura por prazo já segue Q04-26/Q04-35.
- Boleto, Pix e PDF (05–06): sem `instrumento` nesta etapa; conta sem instrumento = manual. O formulário tem só descrição, valor, vencimento, casa, quem paga e quem vê.

## Ajustes incluídos

"Varal — Ajustes" rev 24 lido ao vivo em 15/11/2026: nenhum item novo. D2 (conta cancelada) entra inteiro.

## Telas do Doop

Canvas `k0kB5dc-Vo`, frames achados por nome e lidos em HTML em 15/11/2026; M01 e M02 também por screenshot. **Todos `draft`**, implementados como alvo final (Q1). Canvas somente leitura.

| Mobile (390) | Desktop (1440) | Usado nesta etapa |
| --- | --- | --- |
| 02 · Início (`JJvrRugL0_`, 390×844) | D02 · Início (`SMDsrD8FGT`) | Seletor no cabeçalho (mobile), hero "Total de <mês>" com `count-up` e varal `swing`, "Precisa de atenção" com BillCard; D02: saudação, "Por casa" (HouseCard) |
| 03 · Contas (`bdiED7Q0I-`, 390×844) | D03 · Contas + Detalhe (`cWdVUX2y8H`) | Mês com setas, "Total de <mês>", Chips Todas/A pagar/Vencidas/Pagas (+ Casa no D03), grupos por prazo com soma, BillCard; D03: lista 540px + painel `slide-in` |
| 07 · Detalhe da conta (`efJzW9e5vx`, 390×1220) | painel do D03 | TopBar "Conta" com Editar; conta pendurada (`swing`), StatusBadge, valor herói, "Vence … · em N dias", Casa, Quem paga, Quem vê, Criada por, Histórico |
| 05 · Nova conta (`0PfC8pBVwF`, folha) | M01 · Nova conta (`oOhe6pYOzx`, 560×590) | Só "Onde fica esta conta?" (Chips de espaço) e o cabeçalho com fechar |
| 06 · Conferir conta (`tKY4nFTZ3-`, 390×1090) | M02 · Conferir conta (`Sre1zOcaE-`, 1040×660) | Campos Valor, Vencimento, Descrição; Chips Casa e Quem paga; linha "Quem vê"; "Salvar conta"/"Cancelar" |
| 10 · Grupo (`SfhuKVOQIF`) | D04 · Grupo (`5UzCB5yNaI`) | HouseCard com dados; "Configurações" (botão no D04, ícone no 10), só admin |

Componentes: BillCard (`Mwqabjlc2s`, novo, `web/src/components/bills/bill-card.tsx`), Chip, StatusBadge (com `cancelada`), Field, Button, TopBar, HouseCard, folha/modal da Etapa 03.

**Guia `varal-ui` relido em 15/11/2026.** Igual ao registrado ao fim da Etapa 03 ([movimento](../../design/movimento.md), tabela conferida em 14/11): nenhuma mudança desde então. O que vale para a 04: número-herói 48px no mobile e 64px no desktop, centavos na metade e opacidade .55; `cancelada` cinza com borda, só no filtro Canceladas e no histórico; StatusBadge sempre com ícone e texto; `rise` com intervalo 60–80ms, `slide-in` 24px→0 em .45s, `badge-pulse` no selo Vencida, `count-up` 1,2s, `grow` só quando a barra existir (07); folha < 1024px e modal ≥ 1024px; alvo 44px e botões 52px; "Nova conta" em âmbar. Peças sem frame seguem "Telas sem frame": montar com os componentes do guia; quando virarem frame, o frame manda.

**Diferenças esperadas** (lista final no CA29): sino e ponto de avisos, "Avisos recentes" (09); busca do D02 e do 03 (Q13); barra de pagas do hero e dos HouseCard, "X de N pagas" e a conta verde "pagas" do varal do hero (07, Q12, Q23); "Paga N contas" no MemberRow (07); cartão "aguardando boleto" com "Colar código"/"Enviar PDF" (05/06/08); no detalhe, código de barras, Copiar, PDF, Emissão, "Repete", "Já paguei" e o rodapé de lembrete (05–09); na nova conta, área do PDF, "Colar código", "Se repete", Código, Emissão, Beneficiário, "Repetir todo mês" e "+ Nova" casa.

**Sem frame** (pelo guia `varal-ui`): escolha de "Quem vê" (pessoas), aviso "Quem paga também vê esta conta", folha de filtros mobile e chip "Quem paga", "Cancelar conta" no editar, painel vazio do D03, folha/modal de "Configurações" do grupo, folha de saída barrada pela RN32 (contas que bloqueiam, com "Escolher quem vê" ou "Cancelar conta" em cada uma, e "Sair").

## Decisões de implementação

1. **Rotas:** `/` (Início), `/contas` (lista; filtros na query `?mes=AAAA-MM&status=&casa=&pagador=`), `/contas/[id]` (mobile: 07 sozinho; desktop: lista + painel). Mesmas rotas nas duas larguras; CSS decide.
2. **Espaço atual:** cookie `espaco` (id), lido no servidor e validado contra `/api/me/`; inválido ou ausente → pessoal. O seletor grava o cookie e fica na seção atual se for Início/Contas, senão vai ao Início. Grupo onde o usuário é pagador → `/grupos/[id]/simples` (não grava). Em `/contas/[id]` a lista é a do espaço da conta. A API não confia no cookie: toda rota recebe o espaço explícito e passa pelo `acesso.py`.
3. **`criador` e autor do histórico:** `on_delete=SET_NULL`; exibidos "Ex-membro" quando nulos. `pagador` também `SET_NULL`. `espaco`: `CASCADE`; `subgrupo`: `RESTRICT`.
4. **Hoje** = `timezone.localdate()` (America/Fortaleza). `vencimento` é `DateField`; `criado_em` e histórico em UTC, exibidos em Fortaleza.
5. **Status exibido calculado (só sobre `pendente`):** `vencida` se `vencimento < hoje`; `vence` se `hoje ≤ vencimento ≤ hoje + janela`; senão `pendente`. **Prazo em filtros e contagens:** aplica os mesmos limites às abertas `pendente` e `aguardando`, preservando o selo Aguardando; lista e resumo mantêm seus períodos próprios ([ADR 0009](../../arquitetura/adr/0009-filtro-temporal-contas-abertas.md)).
6. **Pessoal:** pagador = dono, visibilidade `grupo`, sem casa; o formulário esconde esses campos.
7. **Escolhidos em "Quem vê":** novos escolhidos só com papel admin, membro ou observador (pela RN07 o pagador só vê as contas em que é o pagador). Quem já está em "Quem vê" e passou a pagador continua lá e vendo a conta (ADR 0008).
8. **Ações automáticas no histórico** (`pagador_removido`, `cancelada_automaticamente`, `acesso_preservado`) não têm autor e não aparecem como "Ex-membro".

## Decisões resolvidas (ok do dono, 15/11/2026)

| # | Decisão |
| --- | --- |
| Q1 | Frames `draft` implementados como alvo final, como na Etapa 03 |
| Q2 | Categoria removida da origem (rev 47) e do MVP: sem campo, tabela ou modelo, nem para depois ([ADR 0005](../../arquitetura/adr/0005-rf11-sem-categoria.md)) |
| Q3 | FAB e "Nova conta" abrem direto o formulário (folha < 1024px, modal 560px ≥ 1024px) com "Onde fica" no topo; o seletor de tipos volta na 05/06 |
| Q4 | Espaço atual por cookie; pílula do seletor no cabeçalho do Início mobile, como no 02 |
| Q5 | `/grupos/[id]/simples` ganha a lista só leitura das contas do pagador (BillCard, detalhe sem Editar). Copiar e "Já paguei" na 10 |
| Q6 | **RN06 ao pé da letra.** Restrita só criador, pagador e escolhidos; admin não entra por ser admin. Sem vazamento indireto: nenhuma contagem, chip, total, "Precisa de atenção", "Por casa", HouseCard, opção de filtro, paginação ou histórico deixa perceber a conta. Conta não visível = 404, não 403. **O pagador vê pela própria RN06**, mesmo fora dos escolhidos: é regra, não efeito colateral |
| Q7 | RN21: só as abertas (`aguardando`, `pendente`) perdem o pagador; pagas e canceladas guardam quem pagava |
| Q8 | **Conta restrita órfã** (RN32, [ADR 0006](../../arquitetura/adr/0006-rn32-conta-restrita-orfa.md)). Calculada já com a RN21: se a pessoa é a pagadora e, sem ela, ninguém vê, conta como órfã. O que acontece depende de quem age (Q17) |
| Q9 | "Precisa de atenção": vencidas de qualquer mês + vence em breve. Total e números do mês: só o mês corrente, **sempre com rótulo explícito** ("Total de novembro"), porque "Precisa de atenção" mistura meses. Lista de Contas: mês do vencimento |
| Q10 | "Configurações" volta no D04 (ícone no 10), só para admin, com "Avisar N dias antes" (1–7). Substitui a parte da decisão 4 da Etapa 03 que a escondia (nota no [relatório da 03](../03-espacos-grupos/relatorio.md#diferenças-visuais-ca18)) |
| Q11 | HouseCard (10/D04) e "Por casa" (D02) com dados reais agora; MemberRow "Paga N contas" na 07 |
| Q12 | **Nada de barra de pagas zerada.** Até a 07 o HouseCard mostra o total real do mês e "N contas"; a barra e o "X de N pagas" entram com o status pago na 07. O mesmo vale para a barra do hero do Início |
| Q13 | Busca escondida |
| Q14 | Desktop: chips "Casa" e "Quem paga" (menu). Mobile: o botão "Filtros" do 03 abre folha com os dois |
| Q15 | P5 entra: taxa de cadastro do allauth por variável só no E2E/CI |
| Q16 | Pagador pode ser admin, membro ou pagador do grupo (observador não); opcional; "Eu" pré-selecionado quando o autor pode pagar |
| Novo | **Aviso de visibilidade:** numa conta restrita, ao escolher como pagador alguém que não é "Eu", o formulário mostra na hora, antes de salvar, "Quem paga também vê esta conta". Mobile e desktop |
| Q17 | **RN32 por quem age.** Sair e excluir a própria conta: 409 com a lista das contas (a pessoa as vê; nada vaza). **Remoção pelo admin nunca bloqueia:** cada restrita aberta que ficar sem ninguém vira `cancelada`, histórico "cancelada automaticamente: ficou sem ninguém que pudesse vê-la"; o admin recebe a mesma resposta de uma remoção sem órfãs (status, corpo, tempo aproximado), sem contagem, nome ou valor. O removido é avisado do que foi cancelado na **09**; a 04 grava no histórico quem foi removido. **Nunca** escalar a visibilidade para o admin |
| Q18 | **Exceção estreita à RN05** ([ADR 0007](../../arquitetura/adr/0007-rn05-excecao-saida-rn32.md)): quem é o último que vê uma restrita aberta pode, só dentro da própria saída barrada pela RN32, acrescentar alguém em "Quem vê" ou cancelá-la. Não é permissão permanente; sempre fica no histórico |
| Q19a | **Papel trocado para pagador preserva o acesso** ([ADR 0008](../../arquitetura/adr/0008-rn06-prevalece-sobre-rn07.md)): se a troca faria a pessoa perder a única visão de uma restrita aberta, ela entra em `lancamento_acesso` com histórico. A troca acontece, nada vaza. **Acesso explícito (RN06) vale mais que a perda por papel (RN07)** |
| Q19b | Editar tirando a si mesmo de "Quem vê" quando ninguém mais veria: 400 "Você é a única pessoa que vê esta conta. Escolha outra pessoa antes de sair da lista." |
| Q20 | Arquivar casa com contas pendentes (CU04 alternativo) fica fora da 04; contas de casa arquivada mantêm e mostram o nome da casa |
| Q21 | O admin só é avisado (RN19, RN21) e só desfaz pagamento (RN16) das contas que vê. Anotado nas Etapas 07 e 09 |
| Q22 | O dono tirou categoria da origem (rev 50: passo 3 do CU05, entidade `categoria`, `lancamento.categoria_id`). Reexportar na abertura da Etapa 05 (pendência no PROGRESSO) |
| Q23 | A conta "pagas" do varal do hero sai junto com a barra até a 07; o resumo não traz `pagas_qtd` |

## Critérios de aceite

### Precisões da revisão delegada (15/11/2026)

O dono informou no chat "no varal ajustes n tem nenhum pendente"; não houve leitura pelo conector. Sob sua delegação expressa de decisões e continuidade, o Codex ratificou os padrões e fechou as Q04 pendentes no [registro de decisões](decisoes.md#conferência-atual-e-decisões-delegadas-do-codex-15112026). Isto não equivale a implementar ou validar as correções abaixo.

- **CA10/CA15/CA16 — prazo:** Vencidas inclui pendente e aguardando vencidas; resumo e contagens aplicam o mesmo predicado temporal. Aguardando mantém selo, e o período de cada tela continua explícito. Cobrir também hoje e o limite inclusivo da janela (ADR 0009).
- **CA07/CA26 — privacidade:** uniformizar o caminho de consultas do 404 inexistente/invisível, sem prometer tempo constante. O admin do Django de lançamentos/históricos também respeita RN02/RN06, sem privilégio automático de visibilidade por superusuário; conferir relações, busca e contagens.
- **CA22/CA26 — pessoas:** preservar Q04-23: membro atual por nome ou e-mail; ex-membro nunca pelo e-mail, histórico sem e-mail gravado. O detalhe traz apenas pessoas relacionadas à conta autorizada, e o 409 da saída apenas candidatos elegíveis necessários à resolução, sem listagem geral nova ao pagador.
- **CA29/CA32 — identificação:** Quem vê tem um Nome por pessoa; cada nome em uma linha, com quebra entre pessoas. Nos seletores e em Onde fica, espaço/casa pode ocupar até duas linhas, com identificação completa disponível por toque/teclado quando ainda houver corte. Testar prefixos iguais antes de salvar, sem confirmação extra para o caso comum da Q04-30. Conferir o Doop antes da alteração e documentar a exceção sem editar o canvas.
- **Etapa 07:** uma opção Ex-membro agrupa identidades preservadas de antigos pagadores, sem fundir ids históricos; pagador nulo continua Sem pagador, inclusive após exclusão do usuário (Q04-37).
- **Infraestrutura:** M6 aceito somente no ambiente de desenvolvimento até `make dev`; produção permanece sem override de cadastro de E2E/CI. P6 continua exigindo reexportação externa, mas o ADR 0005 já rege o MVP sem categoria.

Testes planejados; nomes e resultados reais vão no relatório. Testes de regra com o ID no nome.

| CA | Dado / Quando / Então | Verificação planejada |
| --- | --- | --- |
| CA01 | **Dado** dono, admin ou membro, **quando** cria conta com descrição, valor e vencimento, **então** ela nasce `pendente` no espaço escolhido, com criador e uma linha "criou" no histórico. | `test_rf10_*`; E2E |
| CA02 | **Dado** valor 0, negativo, decimal ou ausente, **quando** cria ou edita, **então** 400 e nada grava; o banco recusa `valor_centavos ≤ 0`. | `test_rn11_*` |
| CA03 | **Dado** observador ou pagador, **quando** tenta criar, editar ou cancelar conta que vê, **então** 403; dono, admin e membro conseguem. | `test_rn05_contas_por_papel` parametrizado |
| CA04 | **Dado** casa de outro grupo ou arquivada, pagador que não é membro ou é observador, ou escolhido fora do grupo ou de papel pagador, **quando** salva, **então** 400; o contrato não tem categoria. | `test_rf11_*` |
| CA05 | **Dado** conta pessoal, **quando** qualquer outro usuário a lista, abre, edita ou soma, **então** ela não aparece e o id dá 404. | `test_rn02_*` |
| CA06 | **Dado** conta do grupo A, **quando** alguém de fora de A usa o id dela, inclusive em rota de outro espaço seu, **então** 404; a conta só aparece no espaço dela. | `test_rn01_rnf01_*` |
| CA07 | **Dado** conta restrita com escolhidos, **quando** admin, membro ou observador não escolhidos (e que não são criador nem pagador) listam, filtram, abrem, editam, cancelam ou veem o resumo, **então** detalhe, PATCH e cancelar dão **404** (não 403) e nenhum agregado a revela: total, contagens dos chips, "Precisa de atenção", "Por casa", HouseCard, opções de filtro e histórico de outras contas ficam iguais aos de um grupo sem ela; criador e escolhidos veem. | `test_rn06_admin_nao_escolhido_404_e_agregados_sem_a_conta`, `test_rn06_*` |
| CA08 | **Dado** conta restrita cujo pagador não está entre os escolhidos, **quando** o pagador lista, abre ou vê o resumo, **então** ele vê e a conta soma para ele (RN06). | `test_rn06_pagador_nao_escolhido_ve_a_conta` |
| CA09 | **Dado** pagador do grupo, **quando** lista, abre ou vê totais, **então** só as contas em que é pagador e as restritas em que tem acesso explícito (ADR 0008); outra conta, inclusive de visibilidade `grupo`, dá 404. | `test_rn07_*`, `test_rn06_rn07_acesso_explicito_prevalece` |
| CA10 | **Dado** conta `pendente` e janela 3, **quando** consulto em datas diferentes, **então** `vencimento > hoje+3` → `pendente`; `hoje ≤ vencimento ≤ hoje+3` → `vence`; `< hoje` → `vencida`; nada é gravado. Às 23h30 em Fortaleza (02h30 UTC do dia seguinte) a conta de hoje ainda é `vence`. | `test_rn12_*`, `test_rnf11_hoje_em_fortaleza` |
| CA11 | **Dado** admin, **quando** abre "Configurações" do grupo (D04/10) e muda "Avisar N dias antes" para 1–7, **então** o cálculo usa o novo valor; 0 ou 8 → 400; outro papel não vê o botão e a API dá 403; o pessoal fica em 3. | `test_rn13_*`; Vitest; E2E |
| CA12 | **Dado** membro, **quando** edita valor, vencimento, descrição, casa, pagador ou visibilidade, **então** o histórico registra autor, data e antes → depois só dos campos alterados; espaço não muda. | `test_rn22_edicao_*` |
| CA13 | **Dado** conta `pendente`, **quando** cancela, **então** vira `cancelada`, continua no banco e o histórico registra; editar ou cancelar de novo → 409; `paga`/`confirmada` não cancelam (409). | `test_rn22_cancelar_*` |
| CA14 | **Dado** contas canceladas, **quando** vejo Início, totais, "Todas", "A pagar", contagens e "Por casa", **então** não aparecem; aparecem só no filtro "Canceladas" (com contagem), com selo `cancelada`, valor riscado e opacidade reduzida. | `test_d2_*`; Vitest; E2E |
| CA15 | **Dado** contas em vários meses, casas e pagadores, **quando** filtro por mês, status (Todas, A pagar, Vencidas, Pagas, Canceladas), casa e pagador (inclusive "sem pagador"), **então** a lista e as contagens batem; os filtros ficam na URL e voltar no navegador os restaura. | `test_rf13_*`; Vitest; E2E |
| CA16 | **Dado** espaço com contas, **quando** abro o Início, **então** o hero mostra o total do mês, a contagem e o varal, **sem barra de pagas nem a conta "pagas" do varal** (Q23); "Precisa de atenção" lista vencidas de qualquer mês e as que vencem na janela, por vencimento; D02 mostra "Por casa" só em grupo; HouseCard (D02 e 10/D04) mostra total do mês e "N contas", sem barra nem "X de N pagas". | `test_rf13_resumo_*`; Vitest; E2E |
| CA17 | **Dado** hoje em novembro, **quando** vejo o hero, o total da lista e os HouseCard, **então** cada número do mês tem o rótulo do período ("Total de novembro", mês do filtro na lista); "Precisa de atenção" não usa rótulo do mês e uma vencida de outubro mostra a data ("Venceu 28/10"). | Vitest; E2E |
| CA18 | **Dado** membro pagador de contas abertas e pagas e criador de outras, **quando** sai ou é removido (sem cair na RN32), **então** as abertas ficam sem pagador com linha no histórico, as pagas mantêm o pagador, as que criou ficam no grupo e ele perde o acesso às restritas onde era escolhido. | `test_rn21_*` |
| CA19 | **Dado** conta restrita aberta que, sem a pessoa X, ninguém vê, **quando** X sai ou tem a própria conta de usuário excluída (ORM, queryset, admin do Django), **então** 409 `conta_restrita_orfa` com a lista dessas contas e nada muda (membro, pagador, escolhidos, histórico); vale também quando X é só o pagador e o criador já saiu; depois de X escolher outra pessoa para ver ou cancelar, a operação passa; conta paga, confirmada ou cancelada não bloqueia; as duas únicas pessoas que veem saindo ao mesmo tempo → uma sai e a outra recebe 409. | `test_rn32_sair_*`, `test_rn32_exclusao_*` (ORM/queryset/admin), `test_rn32_concorrencia_*` (threads) |
| CA20 | **Dado** conta restrita aberta que, sem X, ninguém vê, **quando** um admin remove X, **então** a remoção **nunca é bloqueada**; a conta vira `cancelada` com histórico `cancelada_automaticamente` ("cancelada automaticamente: ficou sem ninguém que pudesse vê-la") e o id de X nos dados (para o aviso da 09); contas que ainda têm quem veja só seguem a RN21; o admin continua sem ver a conta (404); dois admins removendo ao mesmo tempo as duas únicas pessoas que veem → a conta é cancelada uma vez. | `test_rn32_remocao_admin_cancela_orfa`, `test_rn32_remocao_admin_concorrencia` |
| CA21 | **Dado** duas remoções iguais, uma de quem deixa contas órfãs e outra de quem não deixa, **quando** o admin remove, **então** status HTTP, cabeçalhos relevantes e corpo são idênticos, o tempo é da mesma ordem e nada que o admin possa consultar (lista, contagens, total, "Precisa de atenção", "Por casa", HouseCard, histórico, página do grupo) muda por causa da conta cancelada. | `test_rn32_rn06_remocao_admin_sem_sinal` |
| CA22 | **Dado** o 409 da RN32 ao sair, **quando** a tela recebe a resposta, **então** a folha de saída diz em texto claro o que fazer e lista cada conta que bloqueia com "Escolher quem vê" e "Cancelar conta"; depois de resolver todas, "Sair" conclui; nada some da tela. A remoção pelo admin não tem mensagem nova. | Vitest; E2E |
| CA23 | **Dado** observador escolhido ou pagador (papel pagador) que é o último que vê uma restrita aberta, **quando** sai com a resolução da conta (acrescentar alguém em "Quem vê" ou cancelar), **então** a resolução e a saída acontecem na mesma transação e o histórico registra a ação com o autor e o motivo `saida_rn32`; resolução de conta que não bloqueia a saída → 400; se ainda sobrar conta órfã → 409 e nada muda (nem as resoluções); **fora da saída**, o mesmo observador recebe 403 ao editar ou cancelar uma conta que vê e 404 numa que não vê. | `test_rn05_rn32_excecao_so_na_saida`, `test_rn05_fora_da_saida_observador_403_404` |
| CA24 | **Dado** X criador e único que vê uma restrita aberta, **quando** o admin troca o papel de X para pagador, **então** a troca acontece, X entra em `lancamento_acesso` com histórico `acesso_preservado` e continua vendo a conta; o admin recebe a mesma resposta de uma troca sem esse efeito e segue com 404 na conta; restritas que outra pessoa ainda vê não ganham acesso novo. | `test_rn06_rn07_alterar_papel_preserva_acesso`, `test_rn06_rn07_acesso_explicito_prevalece` |
| CA25 | **Dado** membro que é o único que vê uma restrita (escolhido, não criador nem pagador), **quando** edita tirando a si mesmo de "Quem vê" (ou deixando a conta sem ninguém de outro jeito), **então** 400 com "Você é a única pessoa que vê esta conta. Escolha outra pessoa antes de sair da lista." e nada grava. | `test_rn32_editar_sem_quem_veja_400` |
| CA26 | **Dado** conta criada por um usuário excluído, **quando** alguém do grupo a abre, **então** "Criada por" e o histórico mostram "Ex-membro" e a conta segue no grupo; ações automáticas do histórico não aparecem como "Ex-membro". | `test_rn30_criador_excluido_ex_membro` |
| CA27 | **Dado** usuário em pessoal e grupos, **quando** troca o espaço no seletor (SideNav ou cabeçalho do Início), **então** Início e Contas passam a mostrar aquele espaço e ele persiste ao recarregar; cookie com espaço alheio cai no pessoal; grupo de pagador leva a `/grupos/<id>/simples` com as contas dele (Q5). | Vitest; E2E |
| CA28 | **Dado** o formulário com "Só algumas pessoas" em "Quem vê", **quando** escolho em "Quem paga" alguém que não é "Eu", **então** aparece na hora, antes de salvar, "Quem paga também vê esta conta" (anunciado ao leitor de tela); some com "Eu", sem pagador ou "Todo o grupo". Nas duas resoluções. | Vitest; E2E 390×844 e 1440×900 |
| CA29 | **Dado** Início, Contas, Detalhe, formulário e "Configurações" nos dois tamanhos, **quando** comparo com 02/D02, 03/D03, 07, 05/M01, 06/M02 e 10/D04, **então** composição, componentes, cores, fontes e espaçamentos correspondem, exceto as diferenças esperadas desta spec. | Playwright 390×844 e 1440×900; comparação com o Doop |
| CA30 | **Dado** ≥ 1024px, **quando** abro uma conta da lista, **então** a lista fica e o painel entra com `slide-in` (24px → 0, 0,45s), o card aberto ganha borda; fechar volta a `/contas`; < 1024px a mesma rota mostra só o 07. | E2E nas duas resoluções |
| CA31 | **Dado** FAB "+" (mobile) ou "Nova conta" (SideNav), **quando** toco, **então** abre o formulário (`sheet-up` / `modal-pop`) com o espaço atual marcado em "Onde fica" (só espaços onde posso criar), "Eu" pré-selecionado em "Quem paga" quando posso pagar e sem observadores nas opções; Esc fecha e devolve o foco; salvar mostra a conta na lista. | Vitest; E2E |
| CA32 | **Dado** teclado, leitor de tela ou 360px, **quando** uso as telas, **então** status sempre com ícone e texto, alvos ≥ 44px, sem rolagem horizontal, valores em R$ pt-BR, datas em Fortaleza, movimento reduzido desliga `swing`, `count-up`, `rise`, `slide-in` e `badge-pulse`. | Vitest + Playwright RNF08/RNF09/RNF11 |
| CA33 | **Dado** o contrato novo, **quando** rodo `make types`, **então** o schema valida e regenerar não produz diff. | `make types` |
| CA34 | **Dado** a etapa pronta, **quando** encerro, **então** `make test`, `make lint` e E2E passam, revisão de segurança sem bloqueantes (visibilidade, IDOR, agregados, cookie, RN32, exceção da RN05, sinal ao admin) e docs/matriz atualizadas. | QA, segurança, relatório |
| CA35 | **Dado** formulário aberto por membro autorizado, **quando** saída, remoção ou rebaixamento acontece junto à criação, **então** a autorização é revalidada sob travas compatíveis antes de gravar: ou a criação acontece primeiro com as guardas RN21/RN32 aplicadas à saída posterior, ou a criação é recusada sem conta/histórico parcial. | Regressões RN01/RN05/RN32 de autorização antiga e criação concorrente |
| CA36 | **Dada** conta aberta de visibilidade grupo, **quando** uma edição a torna restrita junto à saída/remoção da última pessoa que a veria, **então** a RN32 permanece válida: saída voluntária bloqueia ou remoção cancela, sem restrita aberta órfã. | Regressões RN32 de conversão grupo → restrita concorrente |
| CA37 | **Dada** leitura autorizada, **quando** outra operação revoga o acesso e grava novos dados antes da serialização, **então** GET não entrega esses novos dados restritos, inclusive pelo histórico; respostas de mutação preservam o resultado da própria operação, sem reler edições alheias posteriores pela exceção da própria perda de acesso. | Regressões RN06/RNF01 de detalhe concorrente e resposta de mutação |

## Fora de escopo

Categoria (ADR 0005, nem para depois); código de boleto/Pix, copiar código e `instrumento` (05); PDF, emissão, beneficiário e o seletor de tipos de 05/M01 (06); marcar paga, comprovante, desfazer, barra de pagas e "Paga N contas" (07); recorrência, `aguardando` gerado e "só este mês ou os próximos" do CU07 (08); lembretes, reagendar ao mudar vencimento, aviso ao admin da RN21 e aviso ao removido das contas canceladas pela RN32 (09); solicitação e modo simples completo (10); arquivar casa com contas pendentes, CU04 alternativo (Q20); busca; reativar conta cancelada; mudar uma conta de espaço; tipo `receita` (v3); endpoint de excluir conta de usuário (11; aqui só as guardas no domínio); reexportar a origem rev 50 (abertura da 05, Q22).
