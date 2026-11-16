# Decisões — Etapa 04 (Contas, núcleo)

> **Contém:** as decisões da Etapa 04. Lista o que os agentes decidiram sozinhos (DNN), as perguntas ao dono (QNN) e as respostas dele, nas palavras dele.
> **Origem:** auditoria do `varal-decisor` (momento 3) em 15/11/2026: [relatório](relatorio.md#decisões-para-o-dono-confirmar) (decisões 1–30), mensagem do dono "Etapa 04 aprovada" (transcript da sessão), `git diff main...HEAD` até 3d4ba32 e "Varal — Ajustes" rev 24 relido ao vivo.

A coluna **Nº rel.** cruza com a tabela "Decisões para o dono confirmar" do relatório. Os IDs Q04-1 a Q04-30 seguem a mesma numeração.

## Precedentes (já resolvidos em outro lugar, só linkados)

| Fonte | O que resolve |
| --- | --- |
| "Varal — Ajustes" rev 24 | Os 18 itens já marcados. D2 (conta cancelada) e D5 ("Ex-membro" para quem excluiu a conta) valem aqui |
| [PROGRESSO, Resolvidas](../../PROGRESSO.md#resolvidas) | D1–D6, P2, P5, P8 |
| [Spec 04, Decisões resolvidas](spec.md#decisões-resolvidas-ok-do-dono-15112026) | Q1–Q23 e o aviso "Quem paga também vê esta conta" |
| [Spec 03, Decisões resolvidas](../03-espacos-grupos/spec.md#decisões-resolvidas-ok-do-dono-14112026) | As oito decisões do ok da Etapa 03 (pagador não vê a página do grupo, grupo sem dono etc.) |
| [ADRs 0001–0008](../../arquitetura/adr/) | Monorepo, S3 local, RN30, RN31, RF11 sem categoria, RN32, exceção da RN05, RN06 sobre RN07 |

## Tabela

| ID | Nº rel. | Decisão | Motivo (fonte do desempate) | Como desfazer | Quem | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Q04-1 | 1 | Limite de aceite (RN31): 10/h por usuário; por IP só com a P3 | Etapa 03, decisão 1 | Configuração do limite | Codex (delegação do dono) | decidida por delegação |
| Q04-2 | 2 | Token de convite com 256 bits (`token_urlsafe(32)`) | Etapa 03, Q1 | Tokens novos com outro tamanho; os emitidos expiram em 7 dias | Codex (delegação do dono) | decidida por delegação |
| Q04-3 | 3 | "Gerenciar papéis" (D04) escondido; o admin toca na linha do membro | Etapa 03, Q2 | Mostrar o botão | Codex (delegação do dono) | decidida por delegação |
| Q04-4 | 4 | Sair do grupo vale para todo papel, inclusive observador e pagador | Etapa 03, Q3 | Regra de permissão em `espacos` | Codex (delegação do dono) | decidida por delegação |
| Q04-5 | 5 | O único admin não pode sair, com mensagem | Etapa 03, Q4 | Regra RN04 em `_desligar` | Codex (delegação do dono) | decidida por delegação |
| Q04-6 | 6 | Telas sem frame montadas com os componentes do `varal-ui` | Etapa 03, Q5 | Refazer quando houver frame | Codex (delegação do dono) | decidida por delegação |
| Q04-7 | 7 | Fundo atrás da folha: `--scrim-sheet` ink 60% (o frame 11 pinta sólido) | Etapa 03, 3 | Trocar o token | Codex (delegação do dono) | decidida por delegação |
| Q04-8 | 8 | Detalhe do seletor: `Grupo · <papel>` | Etapa 03, 4 | Texto do seletor | Codex (delegação do dono) | decidida por delegação |
| Q04-9 | 9 | Confirmações por `window.confirm` nativo (agora também em "Cancelar conta") | Etapa 03, 5 | Trocar por folha/modal | Codex (delegação do dono) | decidida por delegação |
| Q04-10 | 10 | Foco no `<dialog>`: comportamento nativo | Etapa 03, 6 | Gestão de foco própria | Codex (delegação do dono) | decidida por delegação |
| Q04-11 | 11 | Nomes de casas podem quebrar, inclusive no meio de palavras longas no mobile; seletores de espaço/casa admitem até duas linhas e acesso ao valor completo quando houver corte (Q04-39) | Etapa 03, 7. Veja Q04-39 | CSS | Codex (delegação do dono) | decidida por delegação |
| Q04-12 | 12 | Membro sem nome aparece pelo e-mail na página do grupo | Etapa 03, 8. A resposta da Q04-23 cita esta regra ("igual à lista de membros") | `MembroSerializer.get_email` | Codex (delegação do dono) | decidida por delegação |
| Q04-13 | 13 | Rotas `/`, `/contas?mes=&status=&casa=&pagador=`, `/contas/[id]`; as mesmas nas duas larguras | Spec 04, decisão 1 | Rotas do Next | Codex (delegação do dono) | decidida por delegação |
| Q04-14 | 14 | Espaço atual no cookie `espaco`, validado contra `/api/me/`. Se for inválido, abre o pessoal. Grupo de pagador leva a `/grupos/[id]/simples` sem gravar o cookie | Spec 04, decisão 2 | `lib/espaco.ts` | Codex (delegação do dono) | decidida por delegação |
| Q04-15 | 15 | `on_delete`: `criador`, `pagador` e autor do histórico `SET_NULL`; `espaco` `CASCADE`; `subgrupo` `RESTRICT` | Spec 04, decisão 3 | Migração (a troca de `CASCADE` apaga dados) | Codex (delegação do dono) | decidida por delegação |
| Q04-16 | 16 | "Hoje" = `timezone.localdate()` (Fortaleza); `vencimento` é data civil | Spec 04, decisão 4; RNF11 | Código | Codex (delegação do dono) | decidida por delegação |
| Q04-17 | 17 | Status exibido: só `pendente` vira `vence`/`vencida`; filtros e contagens temporais de abertas incluem `aguardando`, sem mudar seu selo (Q04-35, ADR 0009) | Spec 04, decisão 5; RN12 | `com_status` | Codex (delegação do dono) | decidida por delegação |
| Q04-18 | 18 | Conta pessoal: pagador = dono, visibilidade `grupo`, sem casa; campos escondidos no formulário | Spec 04, decisão 6 | Formulário e validação | Codex (delegação do dono) | decidida por delegação |
| Q04-19 | 19 | "Quem vê": novos escolhidos só admin, membro ou observador; quem já estava e virou pagador continua | Spec 04, decisão 7; ADR 0008 | `validar` | Codex (delegação do dono) | decidida por delegação |
| Q04-20 | 20 | Ações automáticas do histórico sem autor; nunca aparecem como "Ex-membro" | Spec 04, decisão 8 | `HistoricoSerializer` | Codex (delegação do dono) | decidida por delegação |
| Q04-21 | 21 | Ação `acesso_removido` no histórico quando a RN21 tira alguém de "Quem vê" (`dados.pessoa`) | Desvio do plano (backend) | Nova ação; linhas gravadas ficam | Codex (delegação do dono) | decidida por delegação |
| Q04-22 | 22 | `opcoes` dos filtros no corpo da lista: casas, pagadores e `sem_pagador`, só das contas visíveis do mês | Desvio do plano (backend); Q6 | Endpoint próprio | Codex (delegação do dono) | decidida por delegação |
| Q04-23 | 23 | Nome de pessoa por contexto (veja as palavras do dono abaixo) | Dono, 15/11/2026 | — | dono | respondida |
| Q04-24 | 24 | Ordem das travas: admins → membro (`FOR UPDATE OF self`) → todas as contas abertas do grupo por `pk` → contas da RN21; `editar` e `cancelar` travam só a conta. Criação trava admins/membro e revalida autorização; exclusão trava admins de todos os grupos. Detalhe trava a conta antes de consultar autorização em novo comando e mantém a trava até serializar | Segurança I1/M1 e revisão B1–B3 (D04-15); incluir públicas cobre conversão concorrente para restrita | Código (`espacos.servicos`, `lancamentos.servicos/views`) | Codex (delegação do dono) | decidida por delegação |
| Q04-25 | 25 | O aviso ao removido fica para a Etapa 09 (P7); a 04 só grava `cancelada_automaticamente` com `dados.removido` | ADR 0006; Q17 | Antecipar o aviso | Codex (delegação do dono) | decidida por delegação |
| Q04-26 | 26 | "Precisa de atenção" com `aguardando`, pelo critério de data (veja as palavras do dono abaixo) | Dono, 15/11/2026 | — | dono | respondida |
| Q04-27 | 27 | Vazio no lugar da barra do D02: corrigir agora | Dono, 15/11/2026 | — | dono | respondida |
| Q04-28 | 28 | Sem TabBar no detalhe mobile | Dono, 15/11/2026 | — | dono | respondida |
| Q04-29 | 29 | Nomes e e-mails longos em uma linha, com reticências | Dono, 15/11/2026. Veja Q04-38 e Q04-39 | — | dono | respondida |
| Q04-30 | 30 | "Onde fica" começa pelo espaço atual, já selecionado | Dono, 15/11/2026 | — | dono | respondida |
| Q04-31 | — | M2: corrigir o caminho de consultas do 404 para não escolher consultas pela existência de conta invisível; preservar corpo/status uniformes, sem promessa de tempo constante | Aceito pelo `varal-seguranca`. O dono pediu para confirmar os quatro aceitos | Código | Codex (delegação do dono) | decidida por delegação |
| Q04-32 | — | M4: manter nome/e-mail de membro atual por contexto; 409 da própria saída só com candidatos elegíveis necessários à resolução (Q04-36) | Aceito pelo `varal-seguranca` (ADR 0007). Depois da resposta 23, o 409 também leva e-mails: veja Q04-36 | `pessoas_para_escolher` | Codex (delegação do dono) | decidida por delegação |
| Q04-33 | — | M5: aplicar RN02/RN06 ao Django admin de lançamentos e histórico agora, sem acesso automático por superusuário; cobrir relações, buscas e contagens indiretas | Aceito pelo `varal-seguranca` | Admin do Django | Codex (delegação do dono) | decidida por delegação |
| Q04-34 | — | M6: aceitar o override residual apenas em desenvolvimento até `make dev`; manter o padrão fora de E2E/CI e verificar isolamento na produção | Aceito pelo `varal-seguranca`. Só dev; reversível | `make dev` recria | Codex (delegação do dono) | decidida por delegação |
| Q04-35 | — | Filtro e contagem Vencidas incluem abertas `pendente`/`aguardando` vencidas pela data; `aguardando` mantém selo e estado gravado (ADR 0009) | Auditoria (4c9a1b2). Veja a pergunta | Código; nenhum dado gravado | Codex (delegação do dono) | decidida por delegação |
| Q04-36 | — | Preservar Q04-23: membro atual com nome ou e-mail; ex-membro nunca com e-mail. Detalhe só com pessoas da conta autorizada; 409 só com candidatos necessários; nenhuma lista geral nova ao pagador | Auditoria (4c9a1b2). Veja a pergunta | `rotulo` | Codex (delegação do dono) | decidida por delegação |
| Q04-37 | — | Na Etapa 07, uma opção Ex-membro agrupa pagadores de identidade preservada que saíram do grupo; sem fundir ids históricos. Pagador nulo continua Sem pagador, inclusive após exclusão do usuário | Auditoria (4c9a1b2). Veja a pergunta | `opcoes` | Codex (delegação do dono) | decidida por delegação |
| Q04-38 | — | Lista Quem vê com um Nome por pessoa: cada nome em uma linha com reticências, lista quebra entre pessoas e não depende de hover para revelar seus participantes | Auditoria (3d4ba32). Veja a pergunta | JSX/CSS | Codex (delegação do dono) | decidida por delegação |
| Q04-39 | — | Nomes de espaço/casa admitem até duas linhas nos seletores e em Onde fica; se ainda houver corte, identificação completa acessível por toque/teclado antes de salvar | Auditoria (3d4ba32, 19fb5fe). Veja a pergunta | CSS | Codex (delegação do dono) | decidida por delegação |
| D04-1 | — | O hero do D02 virou grade de 2 colunas sem altura fixa, com o varal de 560px à direita | Resposta 27 ("o container deve encolher") e as medidas do frame D02 | CSS de `inicio.module.css` | `varal-frontend` | decidida |
| D04-2 | — | Tokens `--hero-padding-y` (28px) e `--hero-varal-width` (560px), com valores do D02, sem mudança visual, já listados em [tokens](../../design/tokens.md#fora-do-doop) | Frame D02; padrão do bloco "fora do Doop" | Voltar aos valores no CSS | `varal-frontend` | decidida |
| D04-3 | — | A pílula "N contas" fica no hero; só sai o vazio | CA16 ("o hero mostra o total do mês, a contagem e o varal") e frame D02; a resposta 27 pediu só o fim do vazio | JSX | `varal-frontend` | decidida |
| D04-4 | — | No detalhe mobile, os estados "Carregando", erro e "Conta não encontrada" também têm TopBar com voltar. A TabBar some pela rota `/contas/[id]`, que o pagador também usa | Resposta 28 ("tela empilhada, com TopBar e voltar"); sem TabBar, esses estados ficariam sem saída | `app-shell.tsx`, `contas-pagina.tsx` | `varal-frontend` | decidida |
| D04-5 | — | Saudação do Início ("Boa noite, <primeiro nome>") em uma linha, com reticências e `title`. Sem nome, usa o começo do e-mail do próprio usuário | Resposta 29 | CSS | `varal-frontend` | decidida |
| D04-6 | — | O Chip corta rótulo maior que o espaço com reticências e `title` | Resposta 29 (feita antes dela, coerente). Só age quando o rótulo não cabe | CSS do Chip | `varal-qa` | decidida |
| D04-7 | — | "Onde fica": se o espaço atual não aceita conta (observador), mantém a ordem e seleciona o primeiro (Pessoal). Na edição, fica o espaço da conta | CA31 ("só espaços onde posso criar") e o comportamento anterior, que não mudou | `espacosParaCriar` | `varal-frontend` | decidida |
| D04-8 | — | Histórico: quem saiu do grupo aparece como "Ex-membro", também nas linhas automáticas ("Ficou sem pagador · Ex-membro saiu do grupo"). Quem volta ao grupo volta a aparecer pelo nome | Resposta 23 ("quem saiu ou excluiu a conta: 'Ex-membro'"; "histórico: sempre id + nome resolvido na hora") | `rotulo(..., historico=True)` | `varal-backend` | decidida |
| D04-9 | — | `Historico.dados` só com ids, com nomes resolvidos na leitura (f072ce5) | Resposta 23 ("nunca e-mail gravado, como você já corrigiu"); segurança I2 | — (formato aprovado) | `varal-backend` | decidida |
| D04-10 | — | E2E: o `globalSetup` faz um cadastro de aquecimento antes dos workers; as medições esperam `modal-pop`/`sheet-up` terminarem | P8; só teste | Tirar o `globalSetup` | `varal-qa` | decidida |
| D04-11 | — | `make limpar-dev`: além do que o dono listou, apaga `e2e-*@varal.test` e os grupos que ficam sem membros. Só roda com DEBUG, mostra a prévia e pede confirmação (`SIM=1` pula). Usuários de teste em grupos reais saem pelo caminho da remoção pelo admin (RN21/RN32: canceladas, nunca apagadas). Nunca apaga o `dev` | Pedido do dono ("crie um alvo make para limpar"). É o mesmo tipo de dado: contas `@varal.test` do QA | Tirar os padrões de `limpar_dev.py` | `varal-devops` | decidida |
| D04-12 | — | Node 22 por `web/.nvmrc` (lido pelo CI) e `engines`; o `make` para com Node < 22 | Pedido do dono ("alinhe o ambiente local") | Arquivos de build | `varal-devops` | decidida |
| D04-13 | — | CI com `workflow_dispatch` nos dois workflows | Pedido do dono ("CI que não dispara"). A causa não foi registrada: veja os achados | Tirar o gatilho | `varal-devops` | decidida |
| D04-14 | — | Detalhe restrito ganha `quem_ve` somente leitura com participantes atuais efetivos da RN06 (criador, pagador e escolhidos, deduplicados); `acesso` continua sendo só a seleção editável | Auditoria Q04-38: listar só os escolhidos omitia quem também via implicitamente; delegação atual do dono | Remover campo e apresentação, sem alterar dados gravados | Codex e agentes de backend/frontend | decidida por delegação |
| D04-15 | — | Criação revalida papel sob as travas comuns de saída; saídas/trocas/exclusão travam todas as abertas, inclusive ainda públicas; detalhe adquire trava em comando separado antes de ler dados autorizados e serializar. Respostas de mutação ficam na transação externa da própria operação | B1–B3 reproduzidos em regressões; em READ COMMITTED um comando que espera FOR UPDATE pode conservar snapshots antigos das outras relações. [PostgreSQL](https://www.postgresql.org/docs/current/transaction-iso.html) | Serviços/views e testes de concorrência, sem mudar dados persistidos | Codex, varal-backend e varal-seguranca | decidida |

## Respostas do dono (15/11/2026, mensagem "Etapa 04 aprovada")

Palavras do dono, sem edição.

**Q04-23 (nome no detalhe)**
> mantenha o e-mail, mas a regra completa é por contexto, não por tela:
> - membro atual com nome: o nome;
> - membro atual sem nome: o e-mail, igual à lista de membros. Em "Pessoa sem nome" ninguém sabe de quem se trata, e no detalhe você precisa saber quem paga;
> - quem saiu ou excluiu a conta: "Ex-membro", NUNCA o e-mail;
> - histórico: sempre id + nome resolvido na hora, nunca e-mail gravado, como você já corrigiu.
>
> Não é incoerência entre as telas: o detalhe é dado vivo de quem está no grupo, o histórico é registro permanente.

**Q04-26 ("aguardando" em "Precisa de atenção")**
> sim, deve entrar, com critério de data. A regra passa a ser: entra toda conta aberta (não paga, não confirmada, não cancelada) que esteja vencida ou dentro da janela de aviso (RN13), seja ela pendente ou aguardando. O selo continua mostrando o status real.
> Motivo: uma conta aguardando boleto a 3 dias do vencimento é o caso mais urgente que existe, porque ainda falta alguém providenciar o código. Deixar ela fora é exatamente o problema que o Varal resolve. Uma aguardando a 30 dias continua fora, pela data.
> Vale agora, mesmo que aguardando só apareça de verdade na 05/06.

**Q04-27 (vazio no lugar da barra)**
> corrija agora, não é diferença aceitável, é buraco de layout. O container deve encolher quando a barra não existe, não reservar o espaço dela.

**Q04-28 (TabBar no detalhe mobile)**
> tire. O frame 07 não tem TabBar, e no celular ela ainda come altura de uma tela que já é longa. Detalhe é tela empilhada, com TopBar e voltar.

**Q04-29 (nomes e e-mails longos)**
> nunca quebre em várias linhas. Corte com reticências em uma linha só, com o valor inteiro no title/aria para quem precisar ler. Teste com um e-mail bem longo.

**Q04-30 (ordem em "Onde fica")**
> melhor que a sua e que o frame. Ordene pelo espaço em que a pessoa está agora, e deixe ele já selecionado. Está no pessoal, Pessoal primeiro; está num grupo, aquele grupo primeiro. O caso comum vira zero toque, em vez de ordem fixa.

Na mesma mensagem, o dono pediu Node 22+, a causa do CI mudo e um alvo `make` de limpeza (D04-11 a D04-13). Disse também: "Me mande a seção de decisões do relatorio.md (1 a 24) e os quatro achados de segurança aceitos. Confirmo as que faltam e aí você faz o merge na main."

## Triagem preparatória do Codex (15/11/2026, registro histórico)

O dono pediu: "analise o contexto e tome as decosoes com base nisso dps execute todas as etapas que faltam no projeto de forma coeerente usando os modelos certos para agentes certos".

Essa mensagem delega as escolhas pendentes e a continuidade entre etapas. Este bloco preserva a análise preliminar feita enquanto faltava a conferência atual de "Varal — Ajustes"; não era resposta do dono nem decisão final. A revisão 24 não foi tratada como atual. A conferência e as decisões finais delegadas estão registradas abaixo; a tabela principal já reflete o resultado.

Encaminhamento a confrontar com a fonte atual:

| Itens | Encaminhamento preliminar | Motivo / limite |
| --- | --- | --- |
| Q04-1–22, Q04-24 e Q04-25 | Ratificar os padrões implementados, ressalvadas as precisões abaixo para Q04-11 e Q04-17 | Preservam os precedentes de permissão, espaço e histórico; aviso ao removido permanece na 09 (P7) |
| Q04-17 e Q04-35 | Separar estado do selo e critério temporal: "Vencidas" inclui abertas `pendente` e `aguardando` com prazo anterior a hoje; `aguardando` mantém o selo | Eliminar divergência entre Início, contagens e filtro, sem alterar o status gravado; registrar ADR e testes |
| Q04-23, Q04-32 e Q04-36 | Preservar a regra por contexto já respondida: membro atual pelo nome ou e-mail; ex-membro nunca pelo e-mail. No detalhe, somente pessoas relacionadas à conta já autorizada; no 409 da própria saída, somente candidatos elegíveis necessários à resolução | Evitar reintroduzir "Pessoa sem nome", expressamente rejeitado pelo dono, e não ampliar acesso a uma lista geral de membros para o pagador; validar conteúdo real dos payloads |
| Q04-37 | Uma opção "Ex-membro" no filtro, agrupando pagadores que já saíram, na Etapa 07 | Sem fundir ids históricos; pagador nulo continua Sem pagador, inclusive após exclusão do usuário |
| Q04-38 | Cada pessoa em uma linha com reticências; a lista quebra entre pessoas | A lista não depende de hover para revelar seus participantes |
| Q04-11 e Q04-39 | Nomes de espaço/casa podem ocupar até duas linhas nos seletores; regra de uma linha permanece para pessoas | Testar grupos com prefixos iguais; duas linhas não garantem distinção de qualquer nome, e a identificação completa precisa continuar disponível |
| Q04-31 / M2 | Corrigir o desvio de consultas no caminho do 404 antes do merge | Evitar decisão baseada em existência de conta invisível; preservar 404 uniforme e travas; não prometer tempo constante |
| Q04-33 / M5 | Antecipar a minimização no Django admin para contas pessoais/restritas e respectivos históricos, sem exceção automática de visibilidade por ser superusuário | Ferramenta de operação deve respeitar o filtro de acesso; revisar também relações e contagens indiretas |
| Q04-34 / M6 | Tolerar o override residual somente em desenvolvimento, documentado; impedir sua utilização indevida em produção | O `make dev` já restaura o padrão; verificar o isolamento antes de fechar a infraestrutura de produção |

Na triagem, a implementação aguardava a conferência dos Ajustes; toda alteração de interface continua exigindo leitura do Doop. A precisão final mantém a criação de `aguardando` pela recorrência variável na 08 e seu suporte de leitura anterior, sem antecipar fluxo de criação por suposição.

## Conferência atual e decisões delegadas do Codex (15/11/2026)

O dono respondeu no chat à solicitação da situação atual de "Varal — Ajustes":

> no varal ajustes n tem nenhum pendente

Esta é uma **conferência atual fornecida pelo dono no chat**, sem leitura pelo conector e sem revalidar a revisão 24 como atual. Não foi feita marcação no documento remoto. As escolhas abaixo são decisões do Codex sob a delegação expressa transcrita na triagem, **não respostas literais do dono a cada Q**. As Q04-23 e Q04-26–30 preservam suas respostas anteriores.

- **Ratificação:** Q04-1–22, Q04-24 e Q04-25, com as precisões de Q04-11/Q04-17. Mantêm-se os padrões já implementados e os precedentes citados na tabela; o aviso ao removido continua na 09 (P7).
- **Prazo versus selo (Q04-17/Q04-35):** uma aguardando vencida precisa aparecer nas contagens e no filtro de vencidas para que Início e Contas concordem. Ela conserva o selo Aguardando e o estado gravado. [ADR 0009](../../arquitetura/adr/0009-filtro-temporal-contas-abertas.md). Reversão: consultas de filtros/contagens e esta precisão documental, sem migração.
- **Pessoas (Q04-32/Q04-36):** aplicar o precedente explícito Q04-23, sem voltar a Pessoa sem nome no dado vivo de membro atual. O detalhe contém somente pessoas relacionadas à conta já autorizada. O 409 contém apenas candidatos elegíveis necessários à saída; não cria uma listagem geral nova para o pagador. Histórico permanece sem e-mail gravado. Reversão: serializadores; dados já expostos não são recuperáveis.
- **Ex-membro (Q04-37):** implementar na 07 uma opção coletiva para identidades preservadas de pagadores que deixaram o grupo. Não fundir nem apagar ids históricos. `pagador=null` continua Sem pagador, inclusive quando a FK ficou nula após excluir usuário; não inferir uma identidade apagada. Reversão: contrato e opções do filtro, sem alterar os dados históricos.
- **Quem vê (Q04-38):** um Nome por pessoa, cada nome em uma linha, com quebra entre pessoas. O motivo é mostrar todos os participantes também no celular; o corte de um nome não pode esconder que há outras pessoas na lista. Reversão: JSX/CSS; exceção de composição documentada e conferida no Doop sem alterar o canvas.
- **Espaço e casa (Q04-11/Q04-39):** até duas linhas nos seletores e em Onde fica, mantendo o valor completo disponível por toque e teclado quando ainda houver corte. Testar nomes com prefixos iguais; duas linhas não garantem distinção. Não exigir confirmação extra para o caso comum da Q04-30. Reversão: CSS e apresentação do valor completo.
- **M2 (Q04-31):** corrigir o desvio estrutural de consultas do 404 antes do merge. Um UUID pode ser compartilhado ou vazar; sua aleatoriedade não substitui RN06. Status e corpo uniformes permanecem, sem alegação de tempo constante. Reversão: consultas internas.
- **M5 (Q04-33):** antecipar a minimização do admin para lançamentos pessoais/restritos e seus históricos, respeitando RN02/RN06 inclusive para superusuário. Rever também relações, buscas e contagens; ocultar registros/modelos se não for possível assegurar o filtro. Isso restringe a aplicação, não o acesso direto de operador ao banco. Reversão: configuração do admin; o que já foi visto não pode ser desfeito.
- **M6 (Q04-34):** aceitar temporariamente o resíduo apenas em desenvolvimento, restaurável por `make dev`. Produção não recebe o override de E2E/CI; verificar esse isolamento no acabamento/deploy. Reversão: recriar o container com configuração normal.

**Execução:** decisões fechadas não significam correções já implementadas. Q04-31/Q04-33/Q04-35/Q04-38/Q04-39 exigem implementação e validação antes do fechamento da revisão. Q04-37 é entrega da 07; Q04-25/P7 é entrega da 09. Q04-36 preserva o precedente e exige conferir os limites efetivos dos payloads. Nenhuma pergunta da 04 permanece aguardando decisão do dono neste registro.

**P6:** a reexportação da especificação pela origem/Claude Code continua externa e pendente. O ADR 0005 e as respostas anteriores já autorizam o MVP sem categoria; não introduzir campo, tabela ou contrato de categoria enquanto a cópia local aguarda atualização. Nunca editar `docs/especificacao-varal.md` manualmente.

## Perguntas da auditoria (registro histórico anterior à decisão delegada)

As propostas, casos contra e condições de espera abaixo preservam a análise original. Não representam pendências atuais: prevalecem a tabela principal e as decisões delegadas acima.

### Q04-35 — "Vencida" com `aguardando`: hero × chip "Vencidas"

- **O que está em jogo:** desde 4c9a1b2, o varal do Início conta uma `aguardando` vencida como "vencida". Na tela Contas, o chip "Vencidas" e o filtro dele só contam `pendente`. A mesma conta dá números diferentes nas duas telas.
- **Proposta:** nos números e nos filtros, "vencida" passa a ser qualquer conta aberta (`pendente` ou `aguardando`) com vencimento antes de hoje. O chip e o filtro "Vencidas" passam a incluir a `aguardando` vencida, e o selo continua "Aguardando". Motivos: é o critério de data da resposta 26, segue a estrela 1 e deixa um número só para cada conceito.
- **O caso contra:** a RN12 e a decisão 17 definem "vencida" como status calculado só sobre `pendente`. Uma `aguardando` não tem código para pagar: o problema dela é "falta o boleto", não "passou do prazo". Um filtro "Vencidas" cheio de cards com selo "Aguardando" confunde. A alternativa honesta é contar `aguardando` à parte no varal, ou só na lista de atenção. Mudar o sentido de "vencida" pode pedir ADR.
- **O que quebra se escolher errado:** Início e Contas discordam e a pessoa deixa de confiar nos números. Desfazer é barato: só `views.py` (contagens e `FILTRO_STATUS`), sem dado gravado.
- **Enquanto não houver resposta:** nada para. Hoje só o seed cria `aguardando` (fluxo real na 05/06/08). Fica como está: o hero conta pela data, o chip pelo status.

### Q04-36 — E-mail de membro sem nome para quem tem papel pagador (com Q04-32 / M4)

- **O que está em jogo:** depois da resposta 23, membro sem nome aparece pelo e-mail no detalhe e na lista `pessoas` do 409 da saída. Quem tem papel pagador nunca vê a página do grupo (decisão 6 da Etapa 03), mas agora recebe esses e-mails: no 409, de todos os admins, membros e observadores sem nome; no detalhe das contas que paga, em "Criada por" e "Quem vê". O dono justificou o e-mail com "igual à lista de membros", e essa lista o pagador não vê.
- **Proposta:** para quem tem papel pagador, membro sem nome aparece como "Pessoa sem nome" no detalhe, porque "Quem paga" é ele mesmo ("Você"). No 409 da saída, o e-mail fica: sem distinguir as pessoas ele não consegue escolher quem vê (ADR 0007), e o caso é raro e fica no histórico. Motivos: estrela 2 e minimização da LGPD; o pagador costuma ser alguém de fora (diarista, condomínio).
- **O caso contra:** o dono disse que a regra é "por contexto, não por tela", e que "em 'Pessoa sem nome' ninguém sabe de quem se trata". Uma regra por papel complica `rotulo`. O pagador pode precisar saber quem criou a conta para perguntar sobre ela. E os e-mails são de quem o convidou ao grupo.
- **O que quebra se escolher errado:** e-mail de familiar exposto a alguém de fora. Mudar o código é barato, mas o que já foi visto não se desfaz.
- **Enquanto não houver resposta:** nada para. Fica como está (e-mail para todos os papéis). A resposta também fecha a Q04-32 (M4).

### Q04-37 — Vários "Ex-membro" iguais no filtro "Quem paga"

- **O que está em jogo:** conta paga guarda o pagador mesmo depois que ele sai (Q7). Pela resposta 23, ele vira "Ex-membro". Com duas pessoas que saíram, o filtro "Quem paga" mostra duas opções "Ex-membro" iguais, e cada uma filtra uma pessoa diferente.
- **Proposta:** juntar todos os que saíram numa opção "Ex-membro", que filtra as contas cujo pagador não é mais membro. Motivo: duas opções iguais não servem para nada.
- **O caso contra:** juntar cria um valor especial no contrato (`pagador=<id>` deixa de bastar). Talvez seja melhor não oferecer ex-membro como opção. E a 07 (quem pagou o quê) pode precisar separar as pessoas.
- **O que quebra se escolher errado:** só confusão na tela; o código é barato de mudar.
- **Enquanto não houver resposta:** nada para. Não acontece antes da 07, porque nenhum fluxo cria conta paga. Pode ir para a spec da 07.

### Q04-38 — "Quem vê" do detalhe cortado numa linha (resposta 29)

- **O que está em jogo:** em 3d4ba32, o texto inteiro "Só Ana, Bia, Carla, …" ficou dentro de um `<Nome>` só. A lista toda vira uma linha com reticências. No celular não existe `title` (não há hover), então quem abre uma conta restrita não vê todas as pessoas que a veem.
- **Proposta:** cortar cada nome, não a lista. Cada pessoa fica num `<Nome>` próprio (nome longo cortado, como a 29 pede) e a lista quebra entre os nomes. Motivo: estrela 2. Saber quem vê a restrita é o ponto dessa linha, e a 29 fala de "nomes e e-mails longos", não de listas.
- **O caso contra:** o dono disse "nunca quebre em várias linhas", e no frame 07 "Quem vê" ocupa uma linha à direita. Quebrar a lista aumenta a altura do detalhe. O texto completo está no nome acessível. Uma alternativa sem quebra seria "Só Ana, Bia e mais 2", com toque para ver todos.
- **O que quebra se escolher errado:** a pessoa acha que só ela (ou poucas pessoas) vê a conta restrita e põe ali algo que não poria. JSX/CSS barato de mudar, mas é decisão de tela e de visibilidade.
- **Enquanto não houver resposta:** nada para. A lista continua cortada.

### Q04-39 — Nome de espaço cortado no seletor e em "Onde fica" (com Q04-11)

- **O que está em jogo:** o frontend estendeu a 29 ao nome do grupo no seletor de espaço (SideNav e pílula do Início). Os Chips de "Onde fica" também cortam (19fb5fe). Os nomes de casa continuam quebrando (decisão 11, que ainda espera o dono). Caso extremo: "Família Martins – casa da praia" e "Família Martins – apartamento" ficam iguais depois do corte no celular. Com a resposta 30 (zero toque), é fácil criar a conta no grupo errado e mostrá-la a outro grupo.
- **Proposta:** nome de espaço (grupo) quebra em até 2 linhas no seletor e em "Onde fica", como casa. O corte em uma linha fica para nomes e e-mails de pessoas, que é do que a 29 trata. Motivo: estrela 2, porque conta no espaço errado aparece para quem não devia.
- **O caso contra:** o dono pediu "nunca quebre em várias linhas" sem separar pessoa de grupo, e a consistência visual pede uma regra só. Nomes de grupo longos e parecidos são raros. No desktop, o `title` mostra o nome todo. Duas linhas no SideNav de 264px desalinham o seletor.
- **O que quebra se escolher errado:** conta criada no grupo errado fica à vista de quem não devia. Para corrigir é preciso cancelar e criar de novo, porque a conta não muda de espaço. CSS barato.
- **Enquanto não houver resposta:** nada para. Fica cortado.

### Q04-31, Q04-33, Q04-34 — Achados de segurança aceitos (o dono pediu para confirmar)

**Q04-31 (M2)**
- **O que está em jogo:** quando a conta existe num grupo do usuário mas ele não a vê, o 404 faz uma consulta a mais. O tempo de resposta pode separar "existe e é restrita" de "não existe".
- **Proposta:** aceitar. Para medir a diferença é preciso já ter o UUID da conta (aleatório), e o 404 continua igual.
- **O caso contra:** a Q6 diz que nada deixa perceber a conta, e tempo de resposta está na lista de privacidade. A correção é barata (rodar as mesmas consultas nos dois caminhos).
- **O que quebra se escolher errado:** quem tem um UUID vazado (link compartilhado) descobre que a restrita existe. A correção é só código.
- **Enquanto não houver resposta:** nada para.

**Q04-33 (M5)**
- **O que está em jogo:** o admin do Django mostra contas restritas ao superusuário.
- **Proposta:** aceitar até a Etapa 11. É ferramenta de operador, e o superusuário já tem o banco.
- **O caso contra:** estrela 2 sem exceção: o operador também não foi escolhido. Esconder as restritas no admin do Django é barato agora.
- **O que quebra se escolher errado:** o operador vê conta restrita alheia. Corrige-se no código; o que já foi visto não volta.
- **Enquanto não houver resposta:** nada para.

**Q04-34 (M6)**
- **O que está em jogo:** depois de um `make e2e`, a API de dev fica com o limite de cadastro alto até o próximo `make dev`.
- **Proposta:** aceitar. Só existe em dev e `make dev` corrige.
- **O caso contra:** o limite alto pode esconder em dev um problema de limite que só aparece em produção.
- **O que quebra se escolher errado:** um teste manual de limite em dev dá resultado falso. Desfazer é trivial.
- **Enquanto não houver resposta:** nada para.
