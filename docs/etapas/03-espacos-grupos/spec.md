# Spec — Etapa 03 (Espaços e grupos)

> **Contém:** escopo, requisitos, ajustes, telas, decisões resolvidas, critérios de aceite e fora de escopo da Etapa 03.
> **Origem:** [etapas](../README.md), RF04–RF07, [CU02](../../casos-de-uso/CU02-criar-grupo.md)–[CU04](../../casos-de-uso/CU04-gerenciar-subgrupos.md), RN01–RN07, RN21, RN24, [RN31 / ADR 0004](../../arquitetura/adr/0004-rn31-link-de-convite.md), [modelo](../../dados/modelo.md), [design](../../design/README.md), [ADR 0003](../../arquitetura/adr/0003-rn30-exportar-e-excluir-dados.md), "Varal — Ajustes" rev 24 (14/11/2026), ok do dono com correções e releitura do Doop (guia `varal-ui`, frames 10, D04, 11, M05) em 14/11/2026.

## Escopo

- Criar grupo com casas iniciais; o criador vira admin. Convite por **link** (RN24, RN31) com papel; aceite com entrada ou cadastro antes. Alterar papel, remover membro, sair, revogar convite pendente. Criar, renomear e arquivar casas.
- **Filtro central de acesso** em `api/apps/espacos/acesso.py`, usado por toda view desta etapa e obrigatório nas Etapas 04+.
- Página do grupo em **três níveis** (decisão 6): admin e membro veem tudo; observador vê a mesma página sem ações; pagador vai para `/grupos/[id]/simples` ("Em breve" até a Etapa 10).
- **Invariante RN04:** todo grupo tem sempre pelo menos um admin, inclusive contra exclusão do `Usuario` (guarda no domínio).
- Telas 10 ↔ D04 e 11 ↔ M05 nas duas resoluções; telas sem frame montadas pelo guia `varal-ui`; `/grupos` deixa de ser "Em breve"; seletor de espaço com dados reais. Convite **não envia e-mail**.

| Requisito | Entrega nesta etapa |
| --- | --- |
| RF04 / CU02 / RN04 | Criar grupo (nome + casas opcionais), criador único admin, atômico |
| RF05 / CU03 / RN24 / RN31 | Link com papel; token de alta entropia guardado só como hash; 7 dias; uso único; revogável; limite de tentativas no aceite |
| RF06 / CU03 / RN04 / RN21 | Alterar papel, remover, sair; nunca grupo sem admin (também na exclusão de conta); quem sai perde acesso na hora |
| RF07 / CU04 | Criar, renomear e arquivar casa |
| RN01 / RN02 / RNF01 | Espaço só visível a quem participa; pessoal só ao dono; não membro recebe 404 |
| RN03 | Espaço pessoal recusa membros e convites |
| RN05 / RN07 | Tabela papel × ação completa; gestão só admin; pagador sem acesso à página do grupo (403). Filtro de contas por visibilidade/pagador na Etapa 04 |
| RN06 | Parcial: só a tabela; visibilidade restrita de conta na Etapa 04 |
| RN21 | Parcial: saída/remoção. Contas sem pagador na 04; aviso ao admin na 09 |

## Ajustes incluídos

"Varal — Ajustes" rev 24 lido ao vivo em 14/11/2026: nenhum item novo para a Etapa 03. As correções desta spec vieram do ok do dono no chat; a regra nova do link virou RN31 pelo ADR 0004.

## Telas do Doop

Canvas `k0kB5dc-Vo`, frames achados por nome e relidos em HTML em 14/11/2026. Canvas somente leitura.

| Mobile (390) | Desktop (1440) | Aprovação | Conteúdo |
| --- | --- | --- | --- |
| 10 · Grupo (`SfhuKVOQIF`, 390×944) | D04 · Grupo (`5UzCB5yNaI`, 1440×900) | 10 draft; D04 **ready_for_dev** | Cabeçalho, Casas (HouseCard), Membros (MemberRow), Contas que se repetem, Configurações; D04 com "Convidar pessoa", "Gerenciar papéis" e aviso de privacidade (`cadeado`) |
| 11 · Convidar membro (`bkv_O9ohNO`, folha) | M05 · Convidar membro (`8XSFrkwy2d`, modal **560×480**) | 11 draft; M05 **ready_for_dev** | Papel em 4 RadioCard (Pagador marcado por padrão), caixa do link `varal.app/c/9fKq2mXb…R4dT` com botão de copiar (ícone, 44px) e "Expira em 7 dias · vale para 1 pessoa", `shine`, "Compartilhar convite"; M05 com "Cancelar" e fechar |

Mudou nos frames 11/M05 desde a preparação: campo "Nome de quem vai entrar" removido do M05 (que passou de 560×560 para 560×480); link agora longo e encurtado no meio, em vez de `7KQ2-M9PX`.

**Telas sem frame** (guia `varal-ui`, seção "Telas sem frame"): lista e criação de grupo, aceite do convite, gestão de membros, edição de casa e menu do seletor. Montadas com os componentes do guia e o layout responsivo dele (folha < 1024px, modal centralizado ≥ 1024px; margens 20px / 28px 40px; botões 52px; alvo 44px). O aceite usa o layout de autenticação (01 ↔ D01). Quando o dono criar o frame, o frame passa a mandar.

## Decisões resolvidas (ok do dono, 14/11/2026)

1. **Telas sem frame:** montar com componentes existentes seguindo o `varal-ui`; aceite no layout do login. Canvas continua somente leitura.
2. **Nome no convite:** removido. O convite carrega só o papel; o nome vem da conta de quem aceita. A lista de membros mostra `nome` ou, se vazio, o e-mail.
3. **Link de convite (RN31, [ADR 0004](../../arquitetura/adr/0004-rn31-link-de-convite.md)):** token `secrets.token_urlsafe(32)`; banco guarda só o hash; uso único; 7 dias; revogável pelo admin; limite no aceite de **10 tentativas por usuário por hora** (por IP depois da P3, a confirmar com o dono); na tela sempre encurtado (`varal.app/c/9fKq2mXb…R4dT`).
4. **Dados de etapas futuras:** casa sem contas mostra "Sem contas ainda" e esconde a barra; MemberRow sem "Paga N contas", só o papel; "Contas que se repetem", "Configurações" e "Gerenciar papéis" escondidos até a etapa de cada um. Os frames ficam como alvo final; diferenças esperadas listadas no CA18.
5. **`shine`:** como no frame: 2,4s, atraso 0,6–0,8s, **2 repetições e para**; desligada com `prefers-reduced-motion`.
6. **Quem vê a página do grupo:** admin e membro, a página inteira; observador, a mesma página sem ações (ver pergunta Q3 sobre "Sair"); **pagador não entra**: API 403 no detalhe e o web leva para `/grupos/[id]/simples` ("Em breve" até a Etapa 10; rota proposta pelo orquestrador, a confirmar no relatório). Gerenciar (convidar, criar/editar casa, mudar papel, remover, revogar convite) só admin.
7. **Modelagem:** grupo sem `dono`; administração só pelo papel admin. **Todo grupo tem sempre pelo menos um admin:** o último admin não sai, não se rebaixa, não é removido e não exclui a conta (guarda no domínio, inclusive pelo admin do Django) até promover outra pessoa.
8. **Frames:** D04 e M05 ready_for_dev; 10 e 11 draft, mas os quatro podem ser implementados.

## Perguntas em aberto (para o relatório)

Não bloqueiam o código; o orquestrador segue o padrão indicado até a resposta.

- **Q1.** O dono pediu "token de 128 bits (`secrets.token_urlsafe(32)`)", mas `token_urlsafe(32)` gera 32 bytes = **256 bits** (43 caracteres); 128 bits seria `token_urlsafe(16)`. Padrão: `token_urlsafe(32)` (atende ao mínimo de 128 bits).
- **Q2.** D04 mostra "Gerenciar papéis", que a decisão 4 manda esconder, mas alterar papel e remover (RF06) são desta etapa. Padrão: link escondido; o admin abre a gestão do membro tocando no MemberRow (folha/modal sem frame).
- **Q3.** "Observador sem nenhuma ação" e "pagador não entra" deixam os dois sem como **sair do grupo** (RF06). Padrão: sair vale para todo papel (é sobre si, não gestão); botão "Sair do grupo" para o observador na página e para o pagador na página "Em breve".
- **Q4.** Grupo com um só membro (o admin): pela invariante, ele não sai nem exclui a conta enquanto não houver "excluir grupo" (fora de escopo). Padrão: bloquear, com mensagem pedindo para convidar e promover alguém.
- **Q5.** O `varal-ui` diz "monte com os componentes acima e estes layouts", mas a seção não traz layout por tela; só as regras gerais. Padrão: as composições do [plano](plano.md#telas-sem-frame).

## Critérios de aceite

Testes planejados; nomes e resultados reais vão no relatório. Testes de regra com o ID no nome.

| CA | Dado / Quando / Então | Verificação planejada |
| --- | --- | --- |
| CA01 | **Dado** usuário autenticado, **quando** cria grupo com nome e casas, **então** o grupo nasce com `dono` nulo, ele como único admin e as casas criadas; nome vazio ou falha no meio não grava nada. | `test_rf04_rn04_*` |
| CA02 | **Dado** espaço pessoal, **quando** alguém tenta gerar convite, aceitar ou incluir membro, **então** é recusado e nenhum `Membro` é criado. | `test_rn03_*` |
| CA03 | **Dado** admin, **quando** gera convite com um papel, **então** recebe o link inteiro uma única vez; o banco guarda só o hash (o token não aparece em nenhuma coluna, log nem resposta posterior); `expira_em` = criação + 7 dias. | `test_rf05_rn24_rn31_*` |
| CA04 | **Dado** visitante sem sessão com link válido, **quando** abre `/c/<token>`, entra ou se cadastra (e-mail ou Google) e aceita, **então** volta ao convite, vira membro com o papel do convite e o convite fica usado. | pytest RF05; E2E com dois usuários e API real |
| CA05 | **Dado** convite expirado, usado, revogado ou inexistente, **quando** é aberto ou aceito, **então** a resposta pede um novo convite e nada muda; dois aceites simultâneos do mesmo link geram um único membro. | `test_rn24_rn31_*` (inclui concorrência) |
| CA06 | **Dado** usuário que já é membro, **quando** aceita outro convite do mesmo grupo, **então** o papel não muda e o convite não é consumido. | `test_rf05_*` |
| CA07 | **Dado** admin, **quando** revoga um convite pendente, **então** ele some da lista de pendentes e o link passa a responder como inválido; Membro, Pagador e Observador recebem 403 ao listar ou revogar. | `test_rn31_revogar_*` |
| CA08 | **Dado** um usuário autenticado, **quando** faz a 11ª tentativa de aceite em uma hora (válida ou não), **então** recebe 429 sem consumir convite; o contador é por usuário. | `test_rn31_limite_aceite_*` |
| CA09 | **Dado** Membro, Pagador ou Observador, **quando** tenta convidar, mudar papel, remover outro, criar/renomear/arquivar casa ou revogar convite, **então** recebe 403; admin consegue. | `test_rn05_*`, por papel |
| CA10 | **Dado** a tabela de permissões, **quando** consulto cada papel × ação (`ver_grupo`, `criar_conta`, `editar_conta`, `pagar_qualquer`, `pagar_propria`, `gerenciar_grupo`), **então** bate com a RN05/RN07 e a decisão 6; dono do pessoal pode tudo no próprio espaço. | `test_rn05_tabela_*` parametrizado |
| CA11 | **Dado** grupo com os quatro papéis, **quando** cada um abre `GET /api/grupos/{id}/` e `/grupos/<id>`, **então** admin e membro recebem a página inteira (só admin com ações de gestão); observador recebe a mesma página sem nenhuma ação; pagador recebe 403 na API e o web o leva para `/grupos/<id>/simples` ("Em breve"). | `test_rn05_rn07_detalhe_grupo_*` por papel; Vitest; E2E |
| CA12 | **Dado** grupo com um admin, **quando** ele se rebaixa, se remove ou sai, **então** é bloqueado com mensagem; com dois admins rebaixando um ao outro ao mesmo tempo, sobra pelo menos um. | `test_rn04_*` (inclui concorrência com threads) |
| CA13 | **Dado** usuário que é o único admin de algum grupo, **quando** sua conta é excluída pelo ORM, por queryset ou pelo admin do Django, **então** a exclusão é bloqueada com mensagem e nada é apagado; após promover outro admin, a exclusão passa. | `test_rn04_exclusao_usuario_ultimo_admin_*` |
| CA14 | **Dado** membro removido ou que saiu, **quando** acessa o grupo, **então** recebe 404 e o grupo some de `/api/me/` e do seletor. | `test_rn21_*`; E2E |
| CA15 | **Dado** usuário que não participa do grupo, **quando** chama qualquer rota do grupo (incluindo ids de membro, casa ou convite de outro grupo na URL de um grupo seu), **então** recebe 404 sem revelar existência; o pessoal de outro nunca aparece. | `test_rnf01_rn01_rn02_*` |
| CA16 | **Dado** admin, **quando** cria, renomeia e arquiva casa, **então** a arquivada sai da lista padrão e continua no banco. | `test_rf07_*` |
| CA17 | **Dado** usuário em grupos, **quando** carrega o app, **então** `/api/me/` traz o pessoal e só os grupos dele com o papel; o seletor troca entre Pessoal e cada grupo (pagador → `/grupos/<id>/simples`); `/grupos` lista e cria. | pytest `/api/me/`; Vitest do seletor; E2E |
| CA18 | **Dado** página do grupo nos dois tamanhos, **quando** comparo com 10/D04, **então** composição, componentes, cores, fontes e espaçamentos correspondem, exceto as diferenças esperadas: casas com "Sem contas ainda" e sem barra; MemberRow sem "Paga N contas"/"modo simples"/"Só acompanha" (só papel); sem "Contas que se repetem" e "+ Nova recorrente"/"Ver todas"; sem "Configurações" (botão em D04, ícone em 10); sem "Gerenciar papéis"; cabeçalho sem "N contas que se repetem"; dados reais no lugar de "Família Martins". Acréscimo sem frame: "Convites pendentes" abaixo de Membros, só para admin e só quando houver. | Playwright 390×844 e 1440×900; comparação com Doop |
| CA19 | **Dado** "Convidar", **quando** abro, **então** é folha (`sheet-up`) < 1024px e modal 560×480 (`modal-pop`) ≥ 1024px; Pagador vem marcado; o link aparece encurtado no formato `varal.app/c/xxxxxxxx…xxxx` com "Expira em 7 dias · vale para 1 pessoa"; `shine` roda 2 vezes e para; copiar e "Compartilhar" (Web Share ou cópia) levam o link inteiro; foco preso, Esc fecha e devolve o foco; movimento reduzido desliga as animações. | Vitest + Playwright, comparação com 11/M05 |
| CA20 | **Dado** teclado, leitor de tela ou 360px, **quando** uso grupo, convite, gestão e aceite, **então** RadioCard é grupo de rádio acessível, alvos ≥ 44px, sem rolagem horizontal, papel nunca só por cor, link encurtado com rótulo acessível. | Vitest + Playwright RNF08/RNF09 |
| CA21 | **Dado** o contrato novo, **quando** rodo `make types`, **então** o schema valida, os tipos cobrem as rotas usadas e regenerar não produz diff. | `make types` |
| CA22 | **Dado** a etapa pronta, **quando** encerro, **então** `make test`, `make lint` e E2E passam, revisão de segurança sem bloqueantes (permissões, IDOR, token, limite) e docs/matriz atualizadas. | QA, segurança, relatório |

## Fora de escopo

Contas, valores e progresso das casas, arquivar casa com contas pendentes (CU04 alternativo), RN13 e `janela_alerta_dias` (Etapa 04); efeito da RN21 nas contas (04) e aviso ao admin (09); recorrentes (08); modo simples de verdade (10; aqui só a rota "Em breve"); renomear/excluir grupo e tela Configurações; convite por e-mail; limite de aceite por IP (P3); endpoint de exclusão de conta e RN30 (11; aqui só a guarda RN04 no domínio); proxy/HTTPS de produção (P4).
