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
| Q04-1 | 1 | Limite de aceite (RN31): 10/h por usuário; por IP só com a P3 | Etapa 03, decisão 1 | Configuração do limite | `varal-backend` (03) | aguardando o dono |
| Q04-2 | 2 | Token de convite com 256 bits (`token_urlsafe(32)`) | Etapa 03, Q1 | Tokens novos com outro tamanho; os emitidos expiram em 7 dias | `varal-backend` (03) | aguardando o dono |
| Q04-3 | 3 | "Gerenciar papéis" (D04) escondido; o admin toca na linha do membro | Etapa 03, Q2 | Mostrar o botão | `varal-frontend` (03) | aguardando o dono |
| Q04-4 | 4 | Sair do grupo vale para todo papel, inclusive observador e pagador | Etapa 03, Q3 | Regra de permissão em `espacos` | `varal-backend` (03) | aguardando o dono |
| Q04-5 | 5 | O único admin não pode sair, com mensagem | Etapa 03, Q4 | Regra RN04 em `_desligar` | `varal-backend` (03) | aguardando o dono |
| Q04-6 | 6 | Telas sem frame montadas com os componentes do `varal-ui` | Etapa 03, Q5 | Refazer quando houver frame | `varal-frontend` (03) | aguardando o dono |
| Q04-7 | 7 | Fundo atrás da folha: `--scrim-sheet` ink 60% (o frame 11 pinta sólido) | Etapa 03, 3 | Trocar o token | `varal-frontend` (03) | aguardando o dono |
| Q04-8 | 8 | Detalhe do seletor: `Grupo · <papel>` | Etapa 03, 4 | Texto do seletor | `varal-frontend` (03) | aguardando o dono |
| Q04-9 | 9 | Confirmações por `window.confirm` nativo (agora também em "Cancelar conta") | Etapa 03, 5 | Trocar por folha/modal | `varal-frontend` (03, 04) | aguardando o dono |
| Q04-10 | 10 | Foco no `<dialog>`: comportamento nativo | Etapa 03, 6 | Gestão de foco própria | `varal-frontend` (03) | aguardando o dono |
| Q04-11 | 11 | Nomes longos de casa quebram no meio da palavra no mobile | Etapa 03, 7. Veja Q04-39 | CSS | `varal-frontend` (03) | aguardando o dono |
| Q04-12 | 12 | Membro sem nome aparece pelo e-mail na página do grupo | Etapa 03, 8. A resposta da Q04-23 cita esta regra ("igual à lista de membros") | `MembroSerializer.get_email` | `varal-backend` (03) | aguardando o dono |
| Q04-13 | 13 | Rotas `/`, `/contas?mes=&status=&casa=&pagador=`, `/contas/[id]`; as mesmas nas duas larguras | Spec 04, decisão 1 | Rotas do Next | orquestrador / `varal-docs` | aguardando o dono |
| Q04-14 | 14 | Espaço atual no cookie `espaco`, validado contra `/api/me/`. Se for inválido, abre o pessoal. Grupo de pagador leva a `/grupos/[id]/simples` sem gravar o cookie | Spec 04, decisão 2 | `lib/espaco.ts` | orquestrador / `varal-docs` | aguardando o dono |
| Q04-15 | 15 | `on_delete`: `criador`, `pagador` e autor do histórico `SET_NULL`; `espaco` `CASCADE`; `subgrupo` `RESTRICT` | Spec 04, decisão 3 | Migração (a troca de `CASCADE` apaga dados) | orquestrador / `varal-docs` | aguardando o dono |
| Q04-16 | 16 | "Hoje" = `timezone.localdate()` (Fortaleza); `vencimento` é data civil | Spec 04, decisão 4; RNF11 | Código | orquestrador / `varal-docs` | aguardando o dono |
| Q04-17 | 17 | Status calculado: só `pendente` vira `vence`/`vencida`. **A resposta da Q04-26 mudou parte disto; veja Q04-35** | Spec 04, decisão 5; RN12 | `com_status` | orquestrador / `varal-docs` | aguardando o dono |
| Q04-18 | 18 | Conta pessoal: pagador = dono, visibilidade `grupo`, sem casa; campos escondidos no formulário | Spec 04, decisão 6 | Formulário e validação | orquestrador / `varal-docs` | aguardando o dono |
| Q04-19 | 19 | "Quem vê": novos escolhidos só admin, membro ou observador; quem já estava e virou pagador continua | Spec 04, decisão 7; ADR 0008 | `validar` | orquestrador / `varal-docs` | aguardando o dono |
| Q04-20 | 20 | Ações automáticas do histórico sem autor; nunca aparecem como "Ex-membro" | Spec 04, decisão 8 | `HistoricoSerializer` | orquestrador / `varal-docs` | aguardando o dono |
| Q04-21 | 21 | Ação `acesso_removido` no histórico quando a RN21 tira alguém de "Quem vê" (`dados.pessoa`) | Desvio do plano (backend) | Nova ação; linhas gravadas ficam | `varal-backend` | aguardando o dono |
| Q04-22 | 22 | `opcoes` dos filtros no corpo da lista: casas, pagadores e `sem_pagador`, só das contas visíveis do mês | Desvio do plano (backend); Q6 | Endpoint próprio | `varal-backend` | aguardando o dono |
| Q04-23 | 23 | Nome de pessoa por contexto (veja as palavras do dono abaixo) | Dono, 15/11/2026 | — | dono | respondida |
| Q04-24 | 24 | Ordem das travas: admins → membro (`FOR UPDATE OF self`) → todas as restritas abertas do grupo por `pk` → contas da RN21; `editar` e `cancelar` travam só a conta. Vale para sair, remover, trocar papel e excluir usuário | Segurança I1/M1. Pela régua de custo seria uma decisão interna, mas fica aqui porque o dono pediu para confirmar | Código (`espacos.servicos`) | `varal-backend` | aguardando o dono |
| Q04-25 | 25 | O aviso ao removido fica para a Etapa 09 (P7); a 04 só grava `cancelada_automaticamente` com `dados.removido` | ADR 0006; Q17 | Antecipar o aviso | `varal-backend` / `varal-docs` | aguardando o dono |
| Q04-26 | 26 | "Precisa de atenção" com `aguardando`, pelo critério de data (veja as palavras do dono abaixo) | Dono, 15/11/2026 | — | dono | respondida |
| Q04-27 | 27 | Vazio no lugar da barra do D02: corrigir agora | Dono, 15/11/2026 | — | dono | respondida |
| Q04-28 | 28 | Sem TabBar no detalhe mobile | Dono, 15/11/2026 | — | dono | respondida |
| Q04-29 | 29 | Nomes e e-mails longos em uma linha, com reticências | Dono, 15/11/2026. Veja Q04-38 e Q04-39 | — | dono | respondida |
| Q04-30 | 30 | "Onde fica" começa pelo espaço atual, já selecionado | Dono, 15/11/2026 | — | dono | respondida |
| Q04-31 | — | Segurança M2: uma consulta a mais em `lancamento_ou_404` quando a conta existe num espaço do usuário | Aceito pelo `varal-seguranca`. O dono pediu para confirmar os quatro aceitos | Código | `varal-seguranca` | aguardando o dono |
| Q04-32 | — | Segurança M4: o pagador recebe nomes de membros no 409 da saída (`pessoas`) | Aceito pelo `varal-seguranca` (ADR 0007). Depois da resposta 23, o 409 também leva e-mails: veja Q04-36 | `pessoas_para_escolher` | `varal-seguranca` | aguardando o dono |
| Q04-33 | — | Segurança M5: o admin do Django mostra restritas ao superusuário; a minimização de dados fica para a Etapa 11 | Aceito pelo `varal-seguranca` | Admin do Django | `varal-seguranca` | aguardando o dono |
| Q04-34 | — | Segurança M6: o container `api` de dev herda `ACCOUNT_RATE_LIMIT_SIGNUP` do último `make e2e` até o próximo `make dev` | Aceito pelo `varal-seguranca`. Só dev; reversível | `make dev` recria | `varal-seguranca` | aguardando o dono |
| Q04-35 | — | "Vencida" com `aguardando`: o hero conta pela data; o chip e o filtro "Vencidas" contam pelo status | Auditoria (4c9a1b2). Veja a pergunta | Código; nenhum dado gravado | `varal-backend` | aguardando o dono |
| Q04-36 | — | E-mail de membro sem nome entregue a quem tem papel pagador (409 da saída e detalhe) | Auditoria (4c9a1b2). Veja a pergunta | `rotulo` | `varal-backend` | aguardando o dono |
| Q04-37 | — | Vários "Ex-membro" iguais nas opções do filtro "Quem paga" (a partir da 07) | Auditoria (4c9a1b2). Veja a pergunta | `opcoes` | `varal-backend` | aguardando o dono |
| Q04-38 | — | "Quem vê" do detalhe: a lista inteira cortada numa linha só | Auditoria (3d4ba32). Veja a pergunta | JSX/CSS | `varal-frontend` | aguardando o dono |
| Q04-39 | — | Nome de espaço (grupo) cortado no seletor e nos Chips de "Onde fica"; casa continua quebrando | Auditoria (3d4ba32, 19fb5fe). Veja a pergunta | CSS | `varal-frontend`, `varal-qa` | aguardando o dono |
| D04-1 | — | O hero do D02 virou grade de 2 colunas sem altura fixa, com o varal de 560px à direita | Resposta 27 ("o container deve encolher") e as medidas do frame D02 | CSS de `inicio.module.css` | `varal-frontend` | decidida |
| D04-2 | — | Tokens `--hero-padding-y` (28px) e `--hero-varal-width` (560px), com valores do D02, sem mudança visual. Falta listá-los em [tokens](../../design/tokens.md#fora-do-doop) | Frame D02; padrão do bloco "fora do Doop" | Voltar aos valores no CSS | `varal-frontend` | decidida |
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

## Perguntas abertas

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
