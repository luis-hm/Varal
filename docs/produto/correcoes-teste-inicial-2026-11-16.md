# Correções e evolução após o teste inicial

> **Contém:** correções solicitadas após os testes, diagnósticos reproduzidos, propostas e critérios de aceite futuros.
> **Origem:** relato do dono e três capturas enviados no chat em 16/11/2026, complementados em 17/11/2026 por diagnóstico de “Sem casa”, revisão visual/Perfil, categorias no lugar das casas, permissões por categoria e falha CSRF no login Google.
> **Status:** análise e backlog documental; nenhuma correção implementada nesta tarefa.
> **Objetivo:** tornar o retorno à aba confiável, permitir consultar contas sem navegar mês a mês e simplificar a organização pessoal e em grupos.

Este documento registra o pedido novo sem substituir as regras vigentes. Distingue o que o dono pediu, a proposta para atender ao pedido e o que ainda precisa amadurecer. A Etapa 11 continua aberta com seus aceites anteriores. A análise inicial usou capturas e leitura de código; os complementos incluem componentes reais em Vitest, endpoints Django com fixtures/rollback e início do login Google em navegador anônimo próprio na homologação. Não houve reprodução no navegador do dono, autenticação em sua conta Google ou inspeção das suas contas reais. O problema de retorno à aba continua sem reprodução completa.

Não foi consultado o documento remoto “Varal — Ajustes” nem o canvas ao vivo. Este registro não é uma cópia desses documentos. Antes de transformar o backlog em uma etapa de implementação, solicitar ao dono o texto atual de Ajustes, conforme `AGENTS.md`, conciliar as fontes e ler os frames envolvidos no Doop, somente em leitura. Não marcar nenhum item como feito agora.

## 1. Direção solicitada

| ID | Pedido do dono | Situação |
| --- | --- | --- |
| COR-01 | Sair da aba e voltar não deve deixar o app preso nas mensagens de carregamento ou sessão. | Defeito relatado; causa completa ainda não reproduzida. |
| COR-02 | Contas deve listar contas de todos os meses; mês vira filtro opcional. | Direção explícita; exige alteração na tela e na API. |
| COR-03 | Filtros devem funcionar sem depender do mês e permitir combinações, como “a pagar em determinado mês”. | Direção explícita; composição e significado dos estados precisam de contrato claro. |
| COR-04 | Organização livre, sem obrigar a pensar em casas ou família; permitir grupo só para si, como “Contas de luz”. | Complemento do dono define categoria como evolução da atual casa, dentro do grupo. |
| COR-05 | Contas principal mostra apenas contas pessoais por padrão; contas de grupos ficam nos respectivos grupos. Poder consultar um grupo por filtro na principal. | Padrão explícito; comportamento do filtro de grupo ainda a amadurecer. |
| COR-06 | Cadastro sem grupo é pessoal; escolher grupo carrega seus integrantes e habilita pagador e visibilidade. Substituir o conceito de casa pelo destino em categoria. | Categoria interna confirmada no complemento; escolha inicial, obrigatoriedade e dados existentes ainda precisam de definição. |
| COR-07 | Investigar por que contas “Sem casa” parecem desaparecer e corrigir os caminhos/filtros envolvidos. | Gravação e consulta confirmadas; lacunas de navegação/resumo e filtro oculto reproduzidas. Correção pendente. |
| COR-08 | Atualizar o design do frontend para as mudanças e adequar o código ao desenho definido. | Entrega de design, implementação e validação conjunta explicitada neste complemento. |
| COR-09 | Criar uma apresentação bonita e bem organizada para Perfil. | Redesenhar a tela funcional existente, preservando seus fluxos e proteções. |
| COR-10 | Como admin, configurar quem pode fazer cada ação em cada categoria (atual casa). | Capacidade solicitada explicitamente; matriz de ações, padrões e precedência das regras precisam ser fechados. |
| COR-11 | Criar a tela de contas ao clicar na categoria pela aba Grupos e corrigir as telas existentes para o novo fluxo. | Percurso definido: Grupos → grupo → categoria → contas → detalhe/pagamento autorizado. |
| COR-12 | Corrigir o login Google que abre “Proibido (403) — Verificação CSRF falhou”. | Dois bloqueios confirmados: política de referrer gera `Origin: null` no formulário; após contorno diagnóstico, Google rejeita o retorno com `redirect_uri_mismatch`. Corrigir política e cadastro OAuth, sem enfraquecer CSRF. |

“Todas as contas” significa **sem recorte obrigatório de mês dentro do contexto escolhido**. Não significa misturar automaticamente contas pessoais com as dos grupos, nem mostrar dados sem permissão.

**Correção de entendimento trazida pelo dono:** já é possível consultar suas contas a pagar nos grupos. Não registrar isso como funcionalidade inexistente. O trabalho é preservar essa capacidade, melhorar seu acesso e corrigir as lacunas abaixo; o padrão pessoal e a organização futura continuam em discussão.

**Definição posterior do dono (17/11/2026):** “categoria (atual casa)” mantém o nível interno ao grupo. A proposta inicial de possivelmente eliminar esse nível está superada neste backlog. Categorias terão acesso às suas contas e permissões por ação configuráveis pelo administrador. O pedido não define ainda todos os detalhes da política de autorização ou da migração.

## 2. COR-01 — Retorno à aba e recuperação da sessão

### Evidência e comportamento atual

As duas primeiras capturas mostram a raiz em `localhost:3000` com o conteúdo do app ausente e estas mensagens:

- “Carregando sua conta…”;
- “Verificando sua sessão. Conecte-se para continuar. Entrar”.

As capturas não mostram resposta HTTP, erro de console ou duração da espera. Portanto, não comprovam expiração de sessão nem permitem atribuir uma causa única.

A leitura de [SessaoGuard](../../web/src/components/auth/sessao-guard.tsx), [bootstrap de sessão](../../web/src/components/auth/bootstrap-sessao.ts) e [ProtectedShell](../../web/src/components/auth/protected-shell.tsx) confirma que:

1. Ocultar a aba aciona proteção da sessão, oculta o conteúdo privado e limpa o cache de consultas.
2. Voltar à aba consulta `/api/me/`, confere identidade, cabeçalho e cookies e, se tudo passar, recarrega a página inteira.
3. Diversos retornos antecipados e falhas de rede mantêm a interface oculta. A mensagem de verificação também pede login, sem distinguir verificação em andamento, falta de conexão e sessão encerrada.

Esse fluxo explica a origem das mensagens e é o primeiro ponto a investigar. Não prova qual condição ocorreu no teste do dono. O recarregamento também merece investigação por possível perda do formulário em preenchimento.

### Correção esperada

- Retomar automaticamente a navegação quando a sessão continuar válida, sem exigir login só por trocar de aba.
- Separar os estados de carregamento inicial, revalidação, indisponibilidade de rede/servidor e sessão efetivamente encerrada.
- Oferecer recuperação clara para falha temporária, evitando espera indefinida ou ciclos de recarregamento.
- Preservar rota, filtros e, na mesma identidade válida, o preenchimento em andamento. Não persistir rascunhos financeiros em armazenamento inseguro para resolver o problema.
- Manter a proteção contra dados de outro usuário após logout, troca de conta, eventos entre abas e restauração pelo histórico. Não remover a guarda de privacidade como atalho.

### Investigação e aceite futuro

Reproduzir com sessão válida, expirada, rede offline/retomada, resposta lenta/5xx, alternâncias rápidas, duas abas e formulário aberto. Inspecionar `/api/me/`, motivo de cada bloqueio e eventos de visibilidade sem registrar cookies ou tokens.

O aceite exige retorno funcional com sessão válida, recuperação de falha temporária, mensagem específica para sessão encerrada e ausência de dados antigos após troca de identidade. Testar também Voltar/Avançar e restauração de página (BFCache). Relacionar à CA11 da Etapa 11; as capturas não encerram o diagnóstico nem esse critério.

## 3. COR-02 e COR-03 — Contas sem mês obrigatório

### O que existe

[ContasPagina](../../web/src/components/bills/contas-pagina.tsx) usa o mês atual quando a URL não informa `mes`. A [API de lançamentos](../../api/apps/lancamentos/views.py) também assume o mês atual e restringe a consulta por vencimento antes de calcular itens, contagens e opções de filtros. Retirar apenas as setas de mês não resolve a limitação.

### Comportamento proposto

- Entrada padrão: **contas pessoais, todos os períodos**, sem exigir seleção de mês.
- Mês/ano opcionais e combináveis com status e contexto. Proposta: mês continua significando **mês de vencimento**, como hoje, não data de pagamento nem competência da recorrência.
- Filtros disponíveis mesmo quando a lista está vazia, para permitir limpar ou corrigir a seleção.
- Opções não devem desaparecer só porque não há contas naquele mês. Sua origem deve respeitar o contexto e as permissões do usuário, sem revelar contas restritas por nomes ou contagens.
- Filtros aplicados no servidor sobre todo o conjunto autorizado, antes da paginação. “Todos os períodos” não deve exigir carregar o histórico inteiro de uma vez.
- URL deve representar a consulta; abrir detalhe e voltar preserva filtros. A tela deve mostrar claramente o contexto e o período ativos.
- Totais e contagens devem indicar seu universo. Proposta: total da lista acompanha todos os filtros; contagens dos chips consideram contexto/período/demais filtros, variando apenas o status. Valor ainda indefinido continua identificado, sem virar zero silenciosamente.

| Consulta | Resultado esperado |
| --- | --- |
| Pessoais + todos os períodos | Contas do espaço pessoal sem corte mensal, conforme status escolhido. |
| Pessoais + a pagar | Contas pessoais abertas, inclusive vencidas, de qualquer mês. |
| Pessoais + a pagar + novembro/2026 | Interseção entre contas pessoais abertas e vencimento em novembro/2026. |
| Grupo “Contas de luz” + todos os períodos | Contas autorizadas desse grupo, sem misturar pessoais pela proposta inicial. |
| Grupo “Viagem” + pagas + dezembro/2026 | Contas autorizadas do grupo, pagas/confirmadas, com vencimento no período proposto. |

Definição proposta de **a pagar**: estados `pendente` e `aguardando`, incluindo vencidas. Uma conta aguardando boleto/valor deve manter sua indicação e suas restrições de pagamento. Confirmar o nome e essa composição antes de implementar; não criar novo status persistido.

A regra vigente D2 exclui canceladas da lista padrão e dos totais, permitindo consulta explícita. Proposta: preservar essa exceção; o pedido de todos os meses não decide sozinho incluir canceladas. Ordenação, rótulos e posição das pagas ainda devem ser definidos, sem alterar a semântica dos estados apenas para reorganizar a tela.

Aceite futuro: fixture com meses passados/atual/futuros, pessoais e grupos, abertas/pagas/canceladas e valores indefinidos; comprovar interseção dos filtros, totais, paginação sem duplicação/perda e retorno do detalhe. Uma busca sem mês não pode continuar implicitamente limitada ao mês atual.

## 4. COR-04 e COR-05 — Grupos livres e separação da área pessoal

### A distinção necessária

Hoje o [modelo de espaços](../../api/apps/espacos/models.py) tem dois níveis diferentes:

| Conceito atual | Função |
| --- | --- |
| Espaço pessoal | Contas particulares de uma pessoa. |
| Grupo (`Espaco` de tipo grupo) | Espaço com membros, papéis e regras de acesso. |
| Casa (`Subgrupo`) | Organização interna de um grupo; não tem membros próprios. |

Assim, trocar “Casa” por “Categoria” apenas no texto não atende, por si só, ao pedido de escolher um grupo e carregar seus usuários. O modelo já admite um grupo com um único administrador e nome livre; a interface e os textos reforçam o uso familiar. A experiência desse caso deve ser validada ponta a ponta.

### Estrutura desejada após o complemento

Usar **Grupo** como um espaço livre de organização, individual ou compartilhado: “Contas de luz”, “Viagem”, “Trabalho” ou outro nome. Convites são opcionais. Dentro dele, **Categoria** substitui a atual casa como organização livre das contas e passa a ter permissões configuráveis. Isso não introduz, por si só, orçamento por categoria ou categorias globais entre grupos.

- **Contas principal:** pessoais por padrão, mesmo depois de visitar um grupo. Conta criada pelo usuário ou atribuída a ele dentro de um grupo continua pertencendo ao grupo; autoria ou pagador não a tornam pessoal.
- **Área de um grupo:** entrada direta para suas contas e pagamento conforme permissão, sem precisar trocar implicitamente toda a aplicação de espaço.
- **Filtro de grupo na principal:** reorganizar o acesso que já existe por seleção de espaço e filtros de status/pagador. Proposta inicial de selecionar um grupo e substituir o conjunto pessoal pelo conjunto daquele grupo, com contexto visível. Mistura “pessoais + grupos” ou seleção de vários grupos fica como decisão aberta; não reconstruir a consulta existente como se ela não existisse.
- **Cards hoje chamados casas:** passam a representar categorias internas; a ação principal abre as contas autorizadas daquela categoria. Editar categoria e configurar permissões são ações distintas da consulta.

Exemplo: criar “Contas de luz” só com o próprio usuário, cadastrar ali as faturas e consultá-las pela área do grupo. Elas ficam fora de Contas pessoais por padrão, mas podem aparecer ao selecionar esse grupo no filtro.

O [seletor atual](../../web/src/lib/espaco.ts) persiste o espaço em cookie, e Contas usa esse contexto. O novo padrão pessoal exige rever essa ligação; mudar apenas o rótulo da navegação não garante a separação desejada. A tela **Início** é distinta de **Contas**: não assumir que seus resumos devem mudar também sem definição.

### Visibilidade e pagamento: detalhamento ainda pendente

O complemento define que o admin escolhe quem pode fazer cada coisa por categoria. Portanto, o acesso não deve ser descrito como “todos veem e pagam tudo”. A consulta e cada ação devem seguir as permissões efetivas da categoria e o tratamento de contas restritas que for definido.

Ainda é necessário decidir como isso se combina com papéis do grupo, pagador atribuído, autor da conta e “Só algumas pessoas”. Administrar permissões não deve ser interpretado automaticamente como ler todas as contas restritas: hoje o admin também respeita essa restrição. COR-10 detalha o trabalho e as decisões restantes.

O [ADR 0005](../arquitetura/adr/0005-rf11-sem-categoria.md) retirou a entidade categoria do MVP. O novo pedido trata da evolução de `Subgrupo`/casa com permissões, e deve ser formalizado em ADR delimitando essa diferença, a compatibilidade e eventual superação parcial da decisão anterior. Não editar retroativamente o ADR nem presumir que basta renomear uma tabela; o esquema e a migração ainda não foram definidos.

## 5. COR-06 — Cadastro com destino claro

A terceira captura mostra Casa/Sem casa, Quem paga e Quem vê. No [formulário atual](../../web/src/components/bills/conta-folha.tsx), os controles de grupo já dependem de `emGrupo`; o destino inicial é o espaço atual priorizado por `espacosParaCriar`. Portanto, a imagem não comprova que esses campos aparecem numa conta pessoal: pode refletir um grupo previamente selecionado pelo contexto. O problema envolve também tornar o destino explícito e previsível.

| Situação desejada | Comportamento |
| --- | --- |
| Cadastro aberto a partir de Contas pessoais, sem grupo escolhido | Conta pessoal; ocultar Casa/Sem casa, Quem paga e Quem vê; nenhum compartilhamento. |
| Grupo escolhido | Carregar membros desse grupo; mostrar escolhas de pagador e visibilidade conforme a política aprovada. |
| Cadastro aberto dentro de um grupo | Proposta: grupo preenchido, visível e explícito, para salvar no lugar esperado. |
| Cadastro aberto na lista de uma categoria | Proposta: grupo e categoria preenchidos explicitamente; oferecer criação somente a quem puder cadastrar ali. |
| Categoria escolhida ou alterada | Revalidar criação, pagador e audiência possíveis; não manter escolhas incompatíveis da categoria anterior. |
| Trocar grupo A por B antes de salvar | Invalidar pagador e pessoas escolhidas de A; carregar B e impedir salvamento com referências antigas. |
| Remover o grupo antes de salvar | Voltar ao pessoal; limpar vínculos e visibilidade de grupo também no envio à API. |
| Falha ao carregar integrantes | Informar erro e permitir tentar de novo; não salvar silenciosamente como pessoal ou em outro grupo. |

Retirar “Casa” e “Sem casa” do cadastro proposto. Com o complemento, haverá destino em **Categoria** dentro do grupo; definir apresentação, pré-seleção e obrigatoriedade. “Sem categoria”, se permitido, não significa conta pessoal. Contas legadas sem casa precisam continuar acessíveis no grupo até uma migração explicitamente definida, sem herdar uma permissão arbitrária.

Aplicar a mesma lógica ao cadastro manual, código de boleto, Pix, conferência de PDF e recorrências. Trocar destino durante upload/leitura requer tratar documento temporário, resposta atrasada e autorização do novo destino. Campos escondidos não podem continuar compartilhando dados por um payload antigo.

Proposta: edição mantém o destino gravado; mover uma conta existente entre pessoal/grupos fica fora desta primeira correção até definir histórico, anexos, pagamentos, recorrência e visibilidade. Escolher o destino de uma conta nova não equivale a autorizar transferência de dados já salvos.

## 6. COR-07 — Diagnóstico real de “Sem casa” e filtros

### O que foi reproduzido

Teste com usuário/grupo fictícios, três contas de R$ 100 e data controlada em 16/11/2026: uma conta com casa em novembro, uma sem casa em novembro e uma sem casa em dezembro. A autenticação foi fornecida pelo cliente de teste; os endpoints, serializers, consultas e regras de acesso executaram de verdade no Django. Toda a criação ocorreu em transação revertida; foi conferido que o usuário sintético não permaneceu no banco. Não se testou login de navegador nesse ensaio.

| Verificação | Resultado observado |
| --- | --- |
| Cadastrar no grupo com `subgrupo: null` | HTTP 201; lançamento persistido no grupo com casa nula durante o ensaio. |
| Listar o grupo em novembro, sem filtro de casa | Retorna a conta com casa **e** a sem casa. |
| Filtrar por `a_pagar` e pelo próprio usuário como pagador | Retorna ambas; essa capacidade já existe. |
| Selecionar uma casa específica | Retorna somente a conta vinculada àquela casa; a sem casa fica fora desse recorte. |
| Remover o filtro de casa | A conta sem casa reaparece. |
| Consultar dezembro | Retorna a conta de dezembro; novembro continua sendo o padrão da lista comum com o relógio do ensaio. |
| Consultar abertas pelo endpoint do modo simples | Retorna as três contas, inclusive dezembro e as sem casa. O corte mensal da lista comum não deve ser generalizado para esse fluxo. |
| Consultar o espaço pessoal | Não retorna nenhuma das três contas do grupo, comportamento coerente com a separação de espaços. |
| Resumo mensal do grupo | Total R$ 200 e 2 contas; `por_casa` representa apenas 1 conta/R$ 100. A conta sem casa entra no total, mas fica fora da distribuição por casas. |
| Tentar filtro explícito `subgrupo=nenhum` | HTTP 400, “Deve ser um UUID válido.” O contrato atual só aceita UUID; não oferece filtro para casa nula. |
| Página do grupo sem casas, com resumo contendo uma conta | Mostra “Nenhuma casa ainda.” e não oferece link local para listar as contas. Reproduzido com o componente real. |
| Clique no card de uma casa como admin | Abre “Editar casa”; não navega para as contas. Para outros papéis na página comum, o card é um bloco sem ação, conforme o código. |
| Lista vazia com `casa=c1` ainda na URL e sem opções disponíveis | Mostra “Nenhuma conta com esses filtros.”, mas o botão Filtros desaparece. Reproduzido com o componente real. |
| API em janeiro/2027 sem contas, mantendo filtro da casa | Retorna itens vazios e nenhuma opção de casa/pagador, confirmando a condição que oculta os controles na tela. |

### Causas identificadas e seus limites

1. **A conta sem casa não é perdida no cadastro testado.** Ela continua sendo conta de grupo. “Sem casa” não significa “pessoal”; procurá-la no espaço pessoal não a encontrará. A lista do grupo com mês correto e filtro de casa removido a retorna.
2. **A organização por casas deixa contas sem casa sem representação.** O resumo em `api/apps/lancamentos/views.py` monta `por_casa` com `subgrupo__isnull=False`. `GrupoPagina` renderiza somente `grupo.casas`; não há card sem casa nem uma entrada local para todas as contas do grupo. `HouseCard` recebe ação de editar, não um destino de listagem. Isso explica o desaparecimento aparente por esse caminho, inclusive para quem espera clicar na casa para pagar.
3. **Não existe opção específica para consultar apenas “Sem casa”.** A API lista casas não nulas nas opções, a tela usa essas opções e o filtro de API valida UUID. A opção “Todas” remove o recorte de casa e inclui contas sem casa, mas não permite isolá-las. Isso é uma lacuna do contrato/interface atual, não um caso em que um filtro “Sem casa” já implementado retorna errado.
4. **Filtros ativos podem ficar escondidos.** `ContasPagina` condiciona botão, menus e folha a `temFiltros(lista.data)`. Essa função examina somente as opções devolvidas, não os filtros ativos na URL. Como a API constrói as opções a partir do mês consultado, um mês sem contas oculta os controles, mas conserva `casa`/`pagador`. Voltar a um mês com dados continua aplicando o filtro antigo. O texto de vazio aparece, porém falta uma ação para limpar o recorte ali.
5. **O mês obrigatório contribui para a impressão de ausência.** A lista comum restringe por vencimento ao mês atual por padrão, antes dos demais filtros. Isso foi confirmado alternando apenas `mes`; é distinto da ausência de casa e já está coberto por COR-02/03.

As hipóteses confrontadas foram perda na gravação/permissão, exclusão por mês/casa e falta de acesso na navegação. A primeira não se confirmou na fixture do criador/admin; as duas últimas se confirmaram nos recortes descritos. Isso não prova qual combinação exata estava ativa na conta real do dono, nem que todos os papéis foram reproduzidos. Não classificar a conta como “invisível em qualquer lugar”.

### Correção a executar

- Garantir uma entrada clara para **todas as contas autorizadas do grupo**, incluindo as sem casa/classificação, independentemente de haver casas cadastradas.
- Separar **abrir contas** de **editar organização**. Pelo complemento, os cards serão de categorias: a ação principal abre o recorte e a edição/configuração de permissões fica em ações próprias.
- Contemplar contas sem classificação nos resumos e filtros e definir sua política de acesso durante a evolução para categorias. Não criar uma casa artificial nem migrar contas para o pessoal como correção.
- Manter filtros ativos visíveis e removíveis mesmo com zero resultados/opções; oferecer “Limpar filtros” no estado vazio. Tratar filtro antigo/indisponível sem deixá-lo oculto.
- Alinhar totais e distribuição: nenhuma parcela pode desaparecer silenciosamente da apresentação. Rótulos devem indicar o período e o universo contado.
- Preservar a consulta existente de contas atribuídas ao próprio usuário, as permissões e o modo simples. Revisar navegação de ida/volta, espaço selecionado e retorno após cadastro, sem atribuir a eles um defeito ainda não reproduzido.

**Aceite:** cadastrar conta sem classificação, encontrá-la pela lista do grupo e pelo filtro do próprio pagador, abrir detalhe/pagamento autorizado, retirar filtros em resultado vazio e navegar entre meses sem filtro oculto. Cobrir grupos sem casas/com casas, mês vazio, datas de outros meses, papéis elegíveis e contas restritas. A correção deve passar nos dois layouts.

[Evidências e reprodução](evidencias/sem-casa-2026-11-17/README.md) guardam script, fixture de componente e resultados. Os testes de interface demonstram falhas existentes; não são uma suíte verde nem uma correção entregue. A tarefa solicitada aqui termina no diagnóstico/documentação; implementação e regressões finais ficam no backlog.

## 7. COR-08 — Revisão do design e adequação do frontend

O ajuste deve entregar **design e código coerentes com o novo comportamento**, não apenas renomear campos. A estrutura grupo → categoria está definida pelo complemento; fechar a política de permissões e a semântica dos filtros, produzir a revisão visual/fluxos e implementá-la nos componentes reais.

| Área | Trabalho de design e comportamento | Adequação de código |
| --- | --- | --- |
| Contas e detalhe | Contexto pessoal/grupo evidente, todos os períodos como padrão proposto, mês opcional, filtros combináveis, resumo legível e limpar filtros no vazio. Preservar retorno do detalhe. | `contas-pagina`, menus/folha, URLs, hooks e contratos de listagem/totais. |
| Grupos e organização | Linguagem livre, grupo individual, acesso direto às contas e representação das não classificadas; separar consulta e administração. | `grupos-lista`, `grupo-pagina`, `house-card`, resumo e permissões. |
| Contas da categoria — nova tela | Cabeçalho grupo/categoria, lista autorizada, filtros, totais e acesso ao detalhe/pagamento; retorno ao grupo e estados vazio/erro/sem acesso. | Rota contextual e componentes de listagem compartilhados; categoria validada dentro do grupo. |
| Permissões da categoria — nova tela/folha | Admin seleciona pessoas e ações, consulta permissões efetivas e salva com feedback claro. | Editor de permissões, endpoints e cálculo centralizado de capacidades; validação também no servidor. |
| Navegação | Tornar claro onde a conta está e qual conjunto se está consultando, mantendo acesso às próprias contas a pagar dos grupos. | Shell, seletor de espaço, navegação mobile/desktop e rotas. |
| Cadastro/conferência | Destino pessoal ou grupo explícito; campos condicionais, estados de troca/carregamento/erro e layout sem lacunas após ocultar campos. | `conta-folha`, PDF/boleto/Pix, recorrências, reset do estado e validação de envio. |
| Retorno à aba | Estados de verificação, rede indisponível e sessão encerrada distinguíveis, com recuperação clara. | Guardas de sessão e shell, preservando isolamento. |
| Perfil | Composição própria e refinada, conforme COR-09. | Página/componente de Perfil e estados dos fluxos existentes. |

Entregáveis: mapa de navegação revisado, layouts mobile/desktop, estados normal/carregando/vazio/erro, comportamento de foco e ações, implementação correspondente e capturas comparativas do app funcionando. Revisar ícones, textos, espaçamentos, tipografia, alinhamento e hierarquia; remover referências a “casa/família” onde a organização passar a ser livre. Reutilizar a identidade e os componentes do Varal.

Não declarar concluído só por atualizar um desenho ou só por mudar uma label. O aceite inclui percorrer o fluxo real e conferir dados, URLs, estados e design em 390×844 e 1440×900, sem overflow, com teclado/foco, contraste e movimento reduzido. Atualizar testes significativos e tipos se houver mudança de API. O canvas permanece somente leitura nesta tarefa documental; não foi produzido nem aplicado um desenho novo aqui.

## 8. COR-09 — Perfil com apresentação própria

O pedido é criar uma **tela de Perfil bonita, clara e consistente com o restante do app**. Já existe implementação funcional em [Perfil](../../web/src/components/perfil/perfil.tsx); o trabalho é redesenhar sua apresentação e integrar o novo layout, preservando comportamento útil.

Direção proposta para o design:

- Cabeçalho de identidade com nome/e-mail e composição visual cuidada; avatar com iniciais pode ser considerado sem criar upload de foto.
- Seções bem delimitadas para dados pessoais, preferências de notificações e privacidade/dados, com leitura rápida e espaçamento consistente.
- Exportação com progresso e estados pronto/erro/expirado próximos da ação correspondente; feedback compreensível e acessível.
- Área de exclusão visualmente distinta, afastada das ações frequentes, com explicação e confirmação explícita; sair da conta fácil de encontrar.
- Reautenticação integrada ao fluxo e ao padrão de folha/modal responsivo, com tratamento de senha/código, erro e cancelamento.
- Layout compacto no celular e uso intencional da largura no desktop, com a mesma hierarquia e funcionalidades.

Escopo funcional a preservar: dados exibidos, preferências, exportar/baixar, excluir, confirmar identidade e sair. Não prometer edição de nome/e-mail, troca de senha, upload de avatar ou novos dados de perfil sem definir esses recursos separadamente. Preservar RN30, prazo da exportação, confirmações, restrições para exclusão e proteção da sessão.

Aceite: revisão visual nas duas larguras; nomes/e-mails longos legíveis; hierarquia clara; nenhum controle decorativo sem função; estados de carregamento/erro/sucesso; navegação por teclado e foco; regressões dos fluxos reais de preferências, exportação, reautenticação, exclusão e logout. Não basta criar uma imagem de referência: a entrega inclui o componente funcional com o novo design.

## 9. COR-10 — Permissões por categoria configuradas pelo admin

**Pedido confirmado:** o administrador do grupo deve conseguir definir quem pode fazer cada ação em cada categoria. Uma pessoa pode ter capacidades diferentes em duas categorias do mesmo grupo. Configurar a categoria não deve exigir promover essa pessoa a administrador do grupo inteiro.

Hoje [acesso.py](../../api/apps/espacos/acesso.py) define ações a partir do papel no grupo e aplica visibilidade por conta; não consulta permissões por `Subgrupo`. A categoria passa a participar da autorização, exigindo mudança no backend, contratos e interface — esconder botões isoladamente não atende ao pedido.

### Matriz de ações a especificar

A lista abaixo é uma **proposta de granularidade**, não uma matriz de concessões já aprovada. Na configuração, cada pessoa do grupo deve ter suas capacidades na categoria compreensíveis; decidir se a edição será individual, por perfil reutilizável ou combinada.

| Capacidade | O que precisa ser definido |
| --- | --- |
| Visualizar contas | Acesso à lista, detalhe, totais, histórico e dados de pagamento; definir relação com contas restritas. |
| Cadastrar contas | Criar conta manual, boleto/Pix/PDF naquela categoria. |
| Editar contas | Alterar dados; separar atribuição de pagador, compartilhamento e mudança de categoria se exigirem poderes distintos. |
| Registrar pagamento | Distinguir pagar somente as atribuídas à pessoa de pagar outras contas autorizadas da categoria. |
| Gerenciar comprovantes e desfazer pagamento | Definir se são capacidades separadas; respeitar estado da conta e regras de autoria/pagamento. |
| Cancelar contas | Cancelamento com histórico; não equivale a apagar registro ou anexo. |
| Gerenciar recorrências | Criar/editar/pausar/retomar/encerrar e aplicar alterações nos próximos lançamentos autorizados. |
| Administrar categoria e permissões | Separar edição/arquivamento da categoria da concessão de acesso; gerenciar permissões é função solicitada para admin do grupo, sem delegação automática. |

Exemplo ilustrativo: em “Energia”, Ana consulta e registra pagamentos, enquanto Bruno apenas consulta; em “Internet”, Bruno também cadastra contas. As permissões de uma categoria não se propagam silenciosamente à outra. Nenhuma combinação do exemplo é um padrão aprovado.

### Política e dados que precisam de definição

- Determinar como o papel no grupo fornece padrões ou limites e se uma permissão específica pode ampliá-lo. Exemplo a resolver: observador pode cadastrar em uma categoria se o admin permitir?
- Definir a precedência entre permissão da categoria, conta restrita, criador e pagador atribuído. Não transformar concessão de “visualizar categoria” em abertura automática de todas as restritas existentes.
- Definir valores iniciais para novas categorias/membros, migração de casas atuais e comportamento de contas sem categoria. Exibir na tela o que será permitido; não aplicar um padrão amplo silenciosamente.
- Definir o alcance de alterações sobre contas existentes/futuras, histórico e arquivos, e como remover acesso sem deixar conta restrita aberta órfã. Considerar saída/remoção de membro e exclusão de usuário.
- Proposta de controle: alterações ficam registradas com autor, categoria, data e diferença de permissões; gravação deve detectar edição concorrente para evitar sobrescrever alterações administrativas sem aviso.
- Conceder uma ação não elimina pré-condições: conta paga/cancelada, boleto aguardando conferência e regras de pagamento continuam sendo validados.

### Implementação e aceite

Centralizar a autorização efetiva no backend e refletir suas capacidades na UI. Aplicar o mesmo cálculo a lista, detalhe, busca/filtros, totais, downloads de boleto/comprovante, recorrências, modo simples, avisos e rotinas em segundo plano. Na revogação, novas consultas, ações e emissão de links devem revalidar acesso; tratar respostas/cache antigos conforme a proteção existente, sem prometer revogar bytes já baixados ou URLs assinadas já emitidas antes de expirarem.

Aceite futuro: admin configura duas pessoas em duas categorias com ações diferentes; cada combinação permitida funciona e cada negada é recusada também por chamada direta à API. Usuário sem administração não altera permissões. Trocar IDs de grupo/categoria não dá acesso cruzado. Contagens e arquivos não revelam contas não autorizadas. Cobrir revogação com tela aberta, alteração concorrente, migração, sem categoria, contas restritas, pagador/autor e recorrências. A configuração visual deve corresponder às permissões efetivas, nas duas larguras.

## 10. COR-11 — Telas de contas da categoria e revisão do fluxo completo

**Fluxo solicitado:** aba **Grupos → grupo → categoria → contas da categoria → detalhe → pagamento**, quando permitido. Voltar retorna ao ponto de origem preservando filtros; a consulta não deve depender de navegar por casas para editar seus nomes.

### Novas telas/estados a entregar

1. **Contas da categoria:** nome do grupo e categoria visíveis; contas autorizadas de todos os períodos por padrão; filtros opcionais por mês/status/pagador, totais do recorte e indicação de filtros ativos. Nova conta somente quando autorizada. No celular, lista e detalhe em telas; no desktop, aproveitar o padrão de lista/detalhe lado a lado. Rota deve carregar diretamente e validar que a categoria pertence ao grupo.
2. **Permissões da categoria:** entrada administrativa própria; lista de membros do grupo, ações configuráveis e explicação do acesso efetivo. Estados de carregar, salvar, sucesso, erro e conflito de edição. Não usar o clique principal do card para abrir essa administração.
3. **Estados de acesso e dados:** categoria vazia, erro recuperável, falta/perda de acesso, categoria arquivada e grupo indisponível; manter retorno seguro. Não exibir nome, total ou existência de contexto não autorizado para tornar a mensagem mais específica.

Compartilhar lógica de lista/filtros/detalhe com Contas principal; “nova tela” significa nova experiência contextual de navegação, não duplicar regras financeiras ou criar um app separado por tamanho de tela. A URL exata é detalhe de implementação, mas grupo/categoria/filtros precisam ser identificáveis e preservados na navegação.

### Telas existentes que precisam acompanhar a mudança

| Tela/fluxo | Revisão necessária |
| --- | --- |
| Lista de grupos e detalhe do grupo | Termos e contagens de categorias, cards que abrem contas, configuração separada, dados sem classificação e resumos apenas autorizados. |
| Contas principal e filtros | Preservar padrão pessoal e consulta existente dos grupos; permitir recorte por categoria conforme política; limpar filtros ativos mesmo no vazio. |
| Nova conta, edição e conferência PDF/Pix/boleto | Grupo/categoria explícitos; destino inicial conforme origem; pagador/audiência elegíveis; tratar troca de categoria e revogação durante preenchimento/upload. |
| Detalhe, pagamento e comprovantes | Mostrar contexto autorizado e ações efetivas; voltar à categoria correta com filtros; mensagens de acesso revogado ou ação recusada. |
| Recorrências e solicitações de pagamento | Validar destino, audiência e ações conforme categoria, inclusive nos próximos lançamentos e cópias; definir destino das solicitações hoje sem casa. |
| Membros, convites e administração | Explicar diferença entre papel no grupo e permissões por categoria; definir como novos membros recebem acesso, sem inferir isso do papel anterior. |
| Início, avisos e modo simples | Rever resumos, links e ações afetados pelas categorias/permissões; manter a consulta de contas atribuídas e evitar links para contextos revogados. Mudança do período dos resumos segue DEC-07. |
| Perfil | Entregar COR-09 com identidade visual coerente com as telas novas; manter escopo pessoal e fluxos existentes. |

Aceite futuro: percorrer Grupos → categoria → conta → pagamento/voltar, abrir link direto e atualizar página, preservar filtros e contexto, cadastrar a partir da categoria certa e conferir ações de dois usuários com permissões diferentes. Repetir em 390×844 e 1440×900, com vazio/erro/revogação e conta sem classificação acessível por caminho definido. Revisão visual deve cobrir o fluxo inteiro, não só as telas novas.

## 11. COR-12 — Login Google bloqueado por CSRF

### O que foi reproduzido

A captura do dono mostra a página de falha CSRF do Django. Em sessão anônima própria de navegador na homologação, clicar **Continuar com Google** reproduziu o mesmo403 no `POST /api/auth/browser/v1/auth/provider/redirect`, antes de autenticar no provedor. O formulário enviou um único campo CSRF preenchido, igual ao cookie vigente; a requisição levou **`Origin: null` e nenhum `Referer`**. A página de entrada recebeu duas ocorrências de `Referrer-Policy: no-referrer`, uma do Next e outra do edge.

O ensaio HTTP abaixo usou cookies anônimos novos e token correto, sem seguir o redirecionamento nem expor cookies, tokens ou `state`:

| Variação de origem/referência | Resultado do endpoint real em HMG |
| --- | --- |
| `Origin: null`, sem `Referer` |403, página de falha CSRF do Django. |
| `Origin` da própria HMG, sem `Referer` |302 para `accounts.google.com`. |
| Sem `Origin` nem `Referer` |403. |
| Sem `Origin`, com `Referer` válido da própria HMG |302 para `accounts.google.com`. |

Um probe isolado do middleware Django também aprovou nove verificações sintéticas: origem própria, origem nula, referência ausente/válida, cookie ausente/rotacionado e precedência entre campo de formulário e header CSRF. São verificações de protocolo; não um login Google completo.

Em outro contexto anônimo de navegador, alterar **somente a meta de referrer no DOM dessa sessão para `strict-origin`** fez o formulário enviar a origem da HMG e uma referência presente. A página403 desapareceu, e a navegação alcançou `accounts.google.com/signin/oauth/error`, onde o Google exibiu **`redirect_uri_mismatch`**. O status intermediário desse POST não foi capturado pelo observador de navegador; os302 da tabela acima pertencem ao ensaio HTTP separado. A intervenção não alterou código versionado, headers do servidor ou o deploy.

Portanto, há duas correções distintas: liberar a requisição legítima na aplicação e ajustar a URI de retorno aceita pelo cliente OAuth no Google. Não foi inspecionado o Console Google para dizer quais URIs estão atualmente cadastradas; a tela do provedor comprova que o retorno solicitado não foi aceito naquele fluxo.

### Causa técnica e lacuna dos testes

[AuthForm](../../web/src/components/auth/auth-form.tsx) inicia Google com `form.submit()`, uma navegação POST nativa. O login por senha usa `fetch` e envia o token em header, por outro caminho. [Next](../../web/next.config.ts) aplica `no-referrer` às páginas de entrada/cadastro, e o [edge](../../infra/deploy/edge.conf.template) acrescenta a mesma política globalmente.

Para essa modalidade de POST, a política `no-referrer` faz o navegador serializar a origem como `null`. Django verifica a origem antes de comparar o token CSRF e rejeita essa origem opaca, mesmo com cookie e campo corretos. O [padrão Fetch](https://fetch.spec.whatwg.org/#append-a-request-origin-header) descreve o comportamento; a [documentação do Django sobre retirada do Referer](https://docs.djangoproject.com/en/6.1/ref/csrf/#removing-the-referer-header) alerta para o conflito com formulários protegidos em HTTPS. As versões locais examinadas são Django6.1.3 e django-allauth65.22.0.

Token vazio/antigo não explica a reprodução observada, pois cookie e campo coincidiram no envio. Origem pública/proxy incorretos também não explicam o recorte em que informar a própria origem produz302. Não usar esses resultados para afirmar que todos os caminhos de proxy ou o retorno OAuth já foram validados.

Os [testes backend de Google](../../api/tests/test_autenticacao.py) preenchem `HTTP_ORIGIN` válido manualmente; não exercitam o header produzido pelo navegador sob a política da página. Os testes de [AuthForm](../../web/src/components/auth/auth-form.test.tsx) e o [E2E de autenticação](../../web/e2e/auth.spec.ts) cobrem Google indisponível, mas não o POST nativo com provedor configurado e os headers produtivos. Essa lacuna permitiu o403 apesar das provas anteriores de API.

### Correção a executar

1. Ajustar a política efetiva **somente nas páginas que iniciam o formulário de entrada/cadastro**, propondo `strict-origin`. Ela conserva a origem necessária ao POST e limita a referência à origem, sem enviar caminho/query.
2. Alinhar Next e edge. Corrigir só uma camada pode deixar a outra acrescentar `no-referrer`; verificar a resposta final e evitar políticas duplicadas conflitantes.
3. Preservar `no-referrer` nas URLs sensíveis de retorno/ticket, convites e confirmações. Manter cookies seguros, validação de origem, token CSRF, `state`/PKCE e vínculo de identidade. **Não adicionar `null` às origens confiáveis, não usar `csrf_exempt` e não desligar CSRF.**
4. Corrigir o cadastro OAuth no Google, que já rejeitou o retorno no ensaio anônimo. Conferir o **Client ID efetivamente usado pela HMG** e cadastrar exatamente `https://hmgvaral.codehub.systems/accounts/google/login/callback/` em **URIs de redirecionamento autorizados**, preservando esquema, host, caminho e barra final. Conferir a origem HMG `https://hmgvaral.codehub.systems` na configuração pertinente do cliente. A URI local permanece `http://localhost:8000/accounts/google/login/callback/`; não substituí-la indiscriminadamente pela de HMG. O erro e a exigência de correspondência exata estão descritos na [documentação OAuth do Google](https://developers.google.com/identity/protocols/oauth2/web-server#uri-mismatch).
5. Após as duas correções, validar consentimento, retorno, troca do código e sessão final. Um302 para o Google não basta para considerar o login completo funcionando.

`GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` são as credenciais OAuth desse login. A chave `API_KEY_GOOGLE` planejada para IA não corrige essa falha.

### Configuração Google Cloud a executar pelo dono

Complemento solicitado em17/11/2026. As capturas posteriores do dono mostram Branding com domínio/links ainda vazios, público externo em teste sem usuários cadastrados e lista de escopos vazia. Elas não mostram o cadastro do cliente OAuth nem comprovam alterações já salvas. Checklist abaixo **pendente de execução e validação**, separado da correção de CSRF no aplicativo.

**Branding**

| Campo | Preenchimento para HMG |
| --- | --- |
| Nome do aplicativo | `Varal`. |
| E-mail de suporte | E-mail de atendimento definido pelo dono. |
| Página inicial | `https://hmgvaral.codehub.systems/entrar`. |
| Domínios autorizados | `codehub.systems`, sem esquema, subdomínio ou caminho. |
| Contato do desenvolvedor | Manter o e-mail de contato do dono, sem copiar o dado pessoal para este documento. |
| Política de privacidade e termos de serviço | Publicar páginas reais e acessíveis antes do lançamento público; não cadastrar URLs fictícias. Durante os testes, deixar vazios somente se o Console permitir salvar. |

O domínio registrável autorizado cobre os subdomínios usados pelo projeto. Se o Google exigir comprovação de propriedade para verificação, fazê-la pelo Search Console. A página de entrada serve como endereço acessível para o teste; não substitui a apresentação pública e as páginas necessárias ao lançamento/verificação. Referências: [Branding](https://support.google.com/cloud/answer/15549049?hl=pt-BR) e [verificação de domínio/marca](https://developers.google.com/identity/verification/authentication-verification).

**Público-alvo**

- Manter **Externo** e status **Testando** para HMG; não publicar agora.
- Adicionar a própria conta Google e as contas dos testadores em **Adicionar usuários**.
- Não tratar a lista como controle de acesso ao HMG: para solicitações somente de identidade básica (`openid`, e-mail e perfil), o Google documenta uma exceção que permite autenticação sem inclusão na lista. [Regras do público e modo de testes](https://support.google.com/cloud/answer/15549945?hl=pt-BR).

**Acesso a dados**

Em **Adicionar ou remover escopos**, selecionar somente os dados de identidade usados pelo login:

```text
openid
https://www.googleapis.com/auth/userinfo.email
https://www.googleapis.com/auth/userinfo.profile
```

Não adicionar permissões de Gmail/Drive ou outras APIs para esse login. A lista vazia das capturas não prova quais escopos o código envia em tempo de execução; conferir ambos na validação. [Referência OpenID Connect](https://developers.google.com/identity/openid-connect/reference).

**Clientes**

1. Abrir o cliente do tipo **Aplicativo da Web** cujo ID corresponde ao `GOOGLE_CLIENT_ID` efetivamente configurado no backend da HMG; editar o cliente existente.
2. Em **URIs de redirecionamento autorizados**, salvar exatamente o retorno de HMG e, se esse cliente também for usado em desenvolvimento local, o retorno local:

| Ambiente | URI de redirecionamento |
| --- | --- |
| HMG — agora | `https://hmgvaral.codehub.systems/accounts/google/login/callback/` |
| Local — se usar o mesmo cliente | `http://localhost:8000/accounts/google/login/callback/` |
| Produção — preparação futura em cliente próprio | `https://varal.codehub.systems/accounts/google/login/callback/` |

Preservar esquema, host, porta local, caminho e barra final. `/entrar/retorno` é um retorno interno do frontend e não substitui o callback OAuth acima. O fluxo atual é iniciado pelo backend; **Origens JavaScript autorizadas não são necessárias para esse fluxo** e não substituem a configuração de redirecionamento. [Correspondência exata exigida pelo Google](https://developers.google.com/identity/protocols/oauth2/web-server#uri-mismatch).

Editar apenas as URIs do cliente existente não exige trocar suas credenciais. Se for criado outro cliente, atualizar `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` somente no ambiente correspondente do backend, sem colar segredos no chat, documento ou frontend. `API_KEY_GOOGLE` continua separada, destinada ao planejamento de IA.

**Antes de produção e validação final**

- Preparar cliente OAuth próprio para produção, com o retorno indicado, e páginas públicas reais de apresentação/privacidade/termos; revisar os requisitos de publicação/verificação aplicáveis no Google. Essa preparação não autoriza iniciar o recurso de produção.
- Após salvar a configuração Google **e** implantar a correção CSRF, testar o fluxo completo com conta autorizada: consentimento, callback, troca do código, criação/recuperação da sessão e acesso ao espaço pessoal.
- Marcar a configuração e o login como concluídos somente com evidência. Alterar o Google Cloud sozinho não corrige o403 atual; redirecionar ao Google sozinho também não comprova login funcional.

### Aceite futuro e limites

- Regressão de navegador com Google configurado: abrir entrada/cadastro, clicar o botão real e observar o302 do endpoint para o provedor, com cookie/token válidos e origem própria. Executar em390×844 e1440×900, com os headers reais da produção, além do ambiente local aplicável.
- Manter negativos para origem alheia/nula, token ausente/incorreto/rotacionado e cookie ausente. O servidor deve continuar recusando `Origin: null`; a correção é o navegador enviar o pedido legítimo corretamente.
- Conferir as políticas finais de entrada e das páginas sensíveis; testar também login por senha, logout, cancelamento/erro do Google, retorno/ticket de uso único e destino seguro.
- Concluir o fluxo com conta Google real somente com autorização adequada, confirmando sessão e espaço pessoal sem duplicação nem vínculo inseguro por coincidência de e-mail.

[Evidências e reprodução](evidencias/google-csrf-2026-11-17/README.md) registram as verificações sanitizadas. Este item é diagnóstico/backlog: nenhum código versionado ou configuração do servidor/provedor foi alterado, nenhuma correção foi implantada e nenhum aceite da etapa foi encerrado. O login completo com conta Google real continua sem validação. O serviço mantém a política original e ainda pode reproduzir o403 até que a correção seja implementada.

## 12. Decisões para a próxima conversa

Estas perguntas ficam registradas para amadurecimento; não bloqueiam a entrega deste documento.

| ID | Decisão | Estado / proposta |
| --- | --- | --- |
| DEC-01 | Grupo e categoria serão o mesmo conceito ou haverá categoria dentro do grupo? | **Definida pelo dono em 17/11:** categoria substitui a atual casa dentro do grupo; possui contas e permissões configuráveis. |
| DEC-02 | O que fazer com casas e vínculos existentes? | Preservar tudo até definir um mapeamento explícito; não transformar automaticamente cada casa em grupo. |
| DEC-03 | Filtro de grupo substitui pessoais, soma pessoais ou permite múltiplos grupos? | Selecionar um grupo substitui a lista pessoal; limpar retorna ao pessoal. |
| DEC-04 | Todos veem e pagam tudo ou há controle por categoria? | **Controle por categoria solicitado pelo dono.** Falta definir precedência com papel, criador/pagador e restrições da conta; ver COR-10. |
| DEC-05 | “A pagar”, “todas” e mês terão qual semântica? | Abertas = pendente/aguardando; todas inclui pagas e mantém canceladas em filtro próprio; mês por vencimento. |
| DEC-06 | Qual o destino inicial e a lembrança de filtros? | Nova entrada em Contas é pessoal; retorno do detalhe preserva a consulta; cadastro dentro de grupo sugere esse grupo explicitamente. |
| DEC-07 | A mudança também vale para Início e resumos dos grupos? | Delimitar primeiro Contas/cadastro/grupo; identificar explicitamente os resumos que passarão a cobrir todos os períodos. |
| DEC-08 | Quais ações são configuráveis e como o admin concede acesso? | Matriz proposta em COR-10; escolher concessões por pessoa/perfil, defaults e possibilidade de ampliar o papel do grupo. |
| DEC-09 | Categoria será obrigatória e qual a política de contas sem categoria? | Preservar acesso às legadas durante transição; definir criação futura, permissões e destino de solicitações. |
| DEC-10 | Permissões novas afetam histórico/contas existentes e como tratar revogação? | Definir alcance, regras de órfãs, mudança de categoria e política de migração sem abertura silenciosa de restritas. |

## 13. Impacto e ordem sugerida

| Prioridade proposta | Trabalho | Dependências e validação |
| --- | --- | --- |
| Alta, bloqueio de autenticação | Corrigir o login Google (COR-12). | Política de referrer consistente entre Next/edge e URI OAuth autorizada para o cliente HMG; regressão do formulário real, negativos CSRF e validação do callback/login completo. Não depende de categorias ou migração. |
| Alta | Diagnosticar e corrigir retorno à aba (COR-01). | Pode ser tratado separadamente da organização; regressões de sessão, offline e privacidade. |
| Alta | Corrigir acesso às contas sem casa e filtros ocultos (COR-07). | Diagnóstico reproduzido; preservar consulta existente por pagador e definir acesso às não classificadas. Não depender de migração para recuperar acesso. |
| Alta | Retirar recorte mensal obrigatório (COR-02/03). | Fechar semântica de status/período; API, tipos, paginação, totais, filtros e telas nas duas larguras. |
| Alta | Consolidar modelo de grupos e separação pessoal (COR-04/05). | DEC-01–04/06/07, navegação e revisão de acesso; necessário antes de migrar dados ou redesenhar cards. |
| Alta, antes da integração das telas novas | Especificar e implementar permissões por categoria (COR-10). | Fechar matriz/precedência/migração, registrar ADR, centralizar autorização e revisar segurança; decisões restantes DEC-04/08–10. |
| Alta | Entregar contas da categoria e administração de permissões (COR-11). | Consumir capacidades do backend, compartilhar componentes e validar o percurso completo com a revisão das telas existentes. |
| Alta | Simplificar cadastro por destino (COR-06). | Modelo escolhido, estados do formulário, PDF/recorrência e validação backend. |
| Transversal | Revisar design e adequar frontend (COR-08). | Desenho acompanha as regras definidas; cada fatia entrega código e validação visual/funcional juntos. |
| Próxima fatia visual | Redesenhar e implementar Perfil (COR-09). | Usar funcionalidades existentes e validar RN30/reauth/logout; pode ser preparado sem decidir categorias. |
| Após definição | Adequar dados existentes e experiências relacionadas. | Plano de migração verificável, histórico, anexos, solicitações de pagamento e notificações sem ampliar acesso. |

Pontos do código a revisar: `web/src/components/auth/`, `web/src/lib/auth/`, `web/src/components/bills/`, `web/src/components/groups/`, `web/src/components/recurrences/`, shell/seletor de espaço, `web/src/lib/contas/`, `api/apps/lancamentos/`, `api/apps/espacos/` e regras de recorrências/solicitações que dependam do destino. Contratos alterados exigem OpenAPI e tipos coerentes.

Rastreabilidade a revisar na implementação: RF01/CU01/RNF01 e CA06/CA12 da autenticação para COR-12; RF11/RF13; CU04–07; RN01–07 (espaço/papel/visibilidade), RN12 (status), RN20 (solicitações), RN21/RN32 (saída e restritas); D2; ADR 0005; CA11/12/13/14/18 da Etapa 11. Permissões por categoria exigem contrato próprio e atualização das regras derivadas após fechar a política. A listagem entre espaços/categorias precisa aplicar autorização também a opções de filtro, contagens, totais e links de arquivos.

Validar mobile 390×844 e desktop 1440×900 com os mesmos dados e rotas. Conferir antes os frames 03/D03, 05/M01, 06/M02, 10/D04 e, se afetado, 13/D05 no Doop. Alterações do canvas exigem pedido explícito. Os nomes citados são referências do índice local, não evidência de leitura ao vivo nesta tarefa.

Antes de implementar mudanças de regras, registrar as decisões em ADR e atualizar spec/plano/tarefas e documentos derivados pertinentes. Não editar manualmente `docs/especificacao-varal.md`; reexportação permanece com Claude Code. Após implementação e validação, o relatório deve indicar quais itens COR-01–12 foram efetivamente concluídos para o dono ou Claude Code atualizar Ajustes. Os diagnósticos de COR-07 e do início de COR-12 foram executados; nenhuma correção de produto, permissão nova ou revisão visual está implementada neste registro.
