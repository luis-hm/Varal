# Plano — Etapa 04 (Contas, núcleo)

> **Contém:** o que cada agente faz, visibilidade no `acesso.py`, modelos e migrações, serviços (com a guarda RN32), contratos de API, telas e riscos da Etapa 04.
> **Origem:** [spec.md](spec.md) (Q1–Q23 resolvidas em 15/11/2026), [modelo](../../dados/modelo.md), [ADR 0003](../../arquitetura/adr/0003-rn30-exportar-e-excluir-dados.md), [ADR 0005](../../arquitetura/adr/0005-rf11-sem-categoria.md), [ADR 0006](../../arquitetura/adr/0006-rn32-conta-restrita-orfa.md), [ADR 0007](../../arquitetura/adr/0007-rn05-excecao-saida-rn32.md), [ADR 0008](../../arquitetura/adr/0008-rn06-prevalece-sobre-rn07.md), [design](../../design/README.md), [movimento](../../design/movimento.md), guia `varal-ui` e código da `main` em 15/11/2026 (`apps/espacos/{acesso,servicos,models}.py`, `apps/lancamentos` vazio, `web/src/components/layout`, `bills/status-badge.tsx`).

Sem dependências novas: `Intl.NumberFormat`/`DateTimeFormat` (R$, fuso e nome do mês), `<input type="date">`, `<dialog>` da Etapa 03, `requestAnimationFrame` para o `count-up`, cookies do Next.

## Agentes

| Ordem / agente | Responsabilidade |
| --- | --- |
| varal-boletos | **Não se aplica** (sem código de barras, Pix nem PDF) |
| varal-backend | Modelos, migrações, `acesso.py` (visibilidade com ADR 0008 e `quem_ve`), status calculado, serviços com histórico, RN21 e RN32 em `_desligar` (dois modos) com as resoluções da saída (ADR 0007), RN32 em `alterar_papel` e `editar`, guarda RN32 na exclusão de `Usuario`, janela RN13, endpoints, seed, testes |
| `make types` | Schema e `web/src/types/api.ts` antes do frontend |
| varal-frontend | Reler os frames da spec; BillCard; Início, Contas, Detalhe, formulário (com o aviso de visibilidade e o 400 da Q19b); seletor com cookie; FAB/"Nova conta"; "Configurações" do grupo; folha de saída barrada pela RN32 (resolver e sair); lista do pagador; HouseCard com dados; vitrine |
| varal-devops | P5: taxa de cadastro do allauth por variável só no E2E/CI (Q15) |
| varal-qa | CA01–CA34, E2E com os papéis e API real, comparação visual com as diferenças esperadas |
| varal-seguranca | Visibilidade (RN02/RN06/RN07, ADR 0008) em lista, detalhe, **agregados**, contagens e opções de filtro; 404 e não 403; IDOR por id; validação de casa/pagador/escolhidos; cookie do espaço; RN21; RN32 e concorrência; **nenhum sinal ao admin** na remoção e na troca de papel; exceção da RN05 presa à saída (ADR 0007) |
| varal-docs | Relatório, PROGRESSO, matriz, `dados/modelo.md`, `api/README.md`, `design/README.md`, `movimento.md` |

## Visibilidade (`api/apps/espacos/acesso.py`)

Uma definição só de "quem vê" (RN02, RN06, RN07), usada pelas consultas e pela RN32. Nenhuma view monta queryset de lançamento sozinha.

| Função | Faz |
| --- | --- |
| `lancamentos_visiveis(usuario, espaco)` | Pessoal do dono: tudo. Grupo, papel `pagador`: `pagador=usuario` ou (`restrita` e `usuario ∈ acesso`) (RN07; RN06 prevalece, ADR 0008). Admin, membro, observador: `visibilidade=grupo` ou `criador=usuario` ou `pagador=usuario` ou `usuario ∈ acesso` (RN06; admin sem exceção, Q6), `distinct`. Sem papel: vazio |
| `lancamento_ou_404(usuario, lancamento_id, acao=None)` | Busca em `lancamentos_visiveis` dos espaços do usuário; **404** se não vê; 403 só se vê e o papel não tem `acao` (`editar_conta`) |
| `quem_ve(lancamento, sem=None)` | Usuários membros do grupo que veem a conta pela mesma regra, tirando `sem` (quem está saindo) e já com a RN21 (quem sai não conta como pagador nem como escolhido). Base da RN32 |

`PERMISSOES` já tem `criar_conta`/`editar_conta` (dono, admin, membro). Criar usa `espaco_ou_404(usuario, id, "criar_conta")`.

## Modelos e migrações

**`apps/lancamentos` (0001):**

1. **Lancamento:** `id` UUID; `espaco` (CASCADE); `subgrupo?` (RESTRICT); `criador?` (SET_NULL, RN30); `pagador?` (SET_NULL); `descricao` (150); `valor_centavos` (`PositiveIntegerField`, `CheckConstraint > 0`, RN11); `vencimento` (`DateField`); `status` (`aguardando|pendente|paga|confirmada|cancelada`, padrão `pendente`, `CheckConstraint`, RN12); `visibilidade` (`grupo|restrita`, padrão `grupo`); `acesso` (`ManyToManyField` para `Usuario`, tabela `lancamento_acesso`); `criado_em`, `atualizado_em`. Índice `(espaco, vencimento)`.
2. **Historico:** `id`; `lancamento` (CASCADE); `usuario?` (SET_NULL, "Ex-membro"); `acao` (`criada|editada|cancelada|pagador_removido|cancelada_automaticamente|acesso_preservado`); `dados` (JSON); `criado_em`. Ordem `criado_em`. As três últimas ações (e `pagador_removido`) são automáticas: `usuario` nulo, exibidas sem autor (decisão 8).
3. Ficam para as etapas delas: `tipo` (v3), `recorrencia` (08), `origem` (10), `instrumento` (05). **Categoria não existe** (ADR 0005).

**`apps/espacos` (0006):** `CheckConstraint` `janela_alerta_dias` entre 1 e 7.

**QuerySet `com_status(janela, hoje)`** em `lancamentos/models.py`: anota `status_exibido` com `Case/When` sobre `pendente` (`vencida`, `vence`) para filtrar e contar no SQL. `hoje = timezone.localdate()`.

Admin do Django: Lancamento e Historico só leitura. Seed: no pessoal do `dev` e na "Família", contas vencida (mês anterior), vence, pendente de outro mês, cancelada, restrita com escolhidos, restrita com pagador fora dos escolhidos e uma do pagador; idempotente.

## Serviços (`apps/lancamentos/servicos.py`)

Toda escrita em `transaction.atomic()`, com `select_for_update` na conta ao editar ou cancelar.

- `validar(espaco, dados, conta=None)`: casa do espaço e não arquivada (só quando a casa muda: conta de casa arquivada mantém e mostra o nome, Q20); pagador membro com papel admin/membro/pagador (Q16); escolhidos **novos** membros com papel admin/membro/observador, os que já estão em `acesso` continuam válidos (decisão 7, ADR 0008); `visibilidade=grupo` limpa `acesso`; no pessoal força pagador = dono, `grupo`, sem casa e sem escolhidos.
- `criar(usuario, espaco, dados)`: grava `pendente` + histórico `criada`.
- `editar(usuario, conta, dados)`: 409 se `cancelada`; grava só os campos mudados; histórico `editada` com `{campo: [antes, depois]}` (pagador e casa por nome; escolhidos por lista). **Q19b:** se a conta é restrita aberta e `quem_ve(conta)` fica vazio depois da mudança, 400 "Você é a única pessoa que vê esta conta. Escolha outra pessoa antes de sair da lista." e nada grava.
- `cancelar(usuario, conta)`: só `aguardando`/`pendente`, senão 409; histórico `cancelada`.
- `restritas_sem_quem_veja(grupo, usuario, travar=True)`: contas abertas (`aguardando|pendente`) e restritas do grupo em que `usuario` é criador, pagador ou escolhido, travadas com `select_for_update` em ordem de `pk`; devolve as que ficam com `quem_ve(conta, sem=usuario)` vazio (RN32).

### RN21 + RN32 em `espacos.servicos._desligar(grupo, modo, resolucoes=(), ...)`

Ponto único de sair e remover (import local para evitar ciclo). Dois modos (Q17):

| Modo | Chamado por | Restrita aberta que ficaria sem ninguém |
| --- | --- | --- |
| `voluntario` | `sair` | Aplica as `resolucoes` (ADR 0007, abaixo); se ainda sobrar alguma órfã, `ContaRestritaSemQuemVeja` (409, `code` `conta_restrita_orfa`) e nada muda, nem as resoluções. Corpo: `detail`, `contas: [{id, descricao}]`, `pessoas: [{id, nome}]` (quem pode ser escolhido) |
| `admin` | `remover_membro` | **Nunca bloqueia.** Cada uma vira `cancelada` + histórico `cancelada_automaticamente` (`usuario` nulo, `dados: {motivo: "sem_quem_veja", removido: <usuario_id>}`). Resposta igual à de hoje (mesmo status e corpo), sem campo, contagem, log ou atalho que dependa de haver órfãs: a consulta de órfãs roda sempre |

Na transação, nesta ordem de travas (a mesma em `alterar_papel`; sem deadlock com RN04 e com `editar`):

1. Admins do grupo (RN04, já existe) → `Membro` alvo (já existe).
2. `restritas_sem_quem_veja(grupo, usuario)` (trava as contas por `pk`) → modo `voluntario` ou `admin` como na tabela.
3. RN21: contas abertas do grupo com `pagador=usuario` → `pagador=None` + histórico `pagador_removido`; tira o usuário do `acesso` das contas do grupo. Pagas e canceladas não mudam (Q7).
4. Apaga o `Membro`. Avisos na 09: ao admin, só das contas que ele vê (Q21); ao removido, a lista das canceladas, montada a partir do histórico `cancelada_automaticamente` com `dados.removido`.

**Exceção da RN05 (Q18, ADR 0007)**, checada só aqui: `POST /api/grupos/{id}/sair/` aceita `resolucoes: [{lancamento, acao: "acesso", usuarios: [id]} | {lancamento, acao: "cancelar"}]`. Cada `lancamento` tem de estar em `restritas_sem_quem_veja(grupo, usuario)` (senão 400); `usuarios` passam pela validação de escolhidos (membros admin/membro/observador, não quem sai). Histórico `editada` (acesso antes → depois) ou `cancelada`, autor quem sai, `dados.motivo = "saida_rn32"`. Como a saída acontece na mesma transação, ninguém fica com permissão nova. Fora daí, PATCH e cancelar seguem a RN05 (403 se vê, 404 se não vê).

Concorrência: duas pessoas que são as únicas que veem a conta C e saem juntas travam a mesma linha de C; a segunda espera, relê (READ COMMITTED) sem a primeira e recebe 409. Dois admins removendo as duas: a segunda remoção relê, acha C órfã e a cancela uma vez (a primeira já não a via como órfã). `editar` também trava C, então mudar "Quem vê" e sair ou ser removido não se cruzam.

### RN32 em `alterar_papel` (Q19a, ADR 0008)

Quando o papel novo é `pagador`, depois das travas admins → `Membro`: trava (por `pk`) as restritas abertas do grupo que a pessoa vê agora e deixaria de ver pela RN07 (é criadora, não está em `acesso` nem é pagadora); para cada uma com `quem_ve(conta, sem=pessoa)` vazio, inclui a pessoa em `acesso` + histórico `acesso_preservado` (`usuario` nulo, `dados: {motivo: "papel_pagador"}`). Resposta ao admin igual à de uma troca sem esse efeito. Nunca dá acesso ao admin.

### RN32 na exclusão de `Usuario`

Novo receptor `pre_delete` ao lado de `proteger_ultimo_admin` (mesma guarda RN04, roda dentro da transação do Collector em `obj.delete()`, `queryset.delete()` e no admin do Django): para cada grupo do usuário, `restritas_sem_quem_veja`; se houver, 409 com a orientação (modo `voluntario`: é a própria pessoa que age, Q17; sem resoluções, que só existem na saída). O admin do Django (`contas_usuario/admin.py`) mostra a mensagem em vez de 500, como na RN04. A exclusão não passa por `_desligar` (o `Membro` cai em cascata e `pagador` vira nulo pelo `SET_NULL`); o histórico da RN21 nesse caminho fica com o endpoint da Etapa 11.

## Contratos de API

DRF, sessão e CSRF. Erros de regra em pt-BR. Datas `AAAA-MM-DD`; instantes ISO 8601 UTC.

| Método e caminho | Quem | Entrada → saída |
| --- | --- | --- |
| `GET /api/espacos/{id}/lancamentos/` | participante (filtrado) | `?mes=AAAA-MM` (padrão: mês de hoje) `&status=todas\|a_pagar\|vencidas\|pagas\|canceladas` `&subgrupo=<id>` `&pagador=<id>\|nenhum` → `{mes, total_centavos, contagens: {todas, a_pagar, vencidas, pagas, canceladas}, itens: [Conta]}`. Sem paginação (limite de um mês) |
| `POST /api/espacos/{id}/lancamentos/` | `criar_conta` | `{descricao, valor_centavos, vencimento, subgrupo?, pagador?, visibilidade?, acesso?: [usuario_id]}` → 201 `ContaDetalhe` |
| `GET /api/espacos/{id}/resumo/` | participante (filtrado) | `{mes, janela_alerta_dias, total_centavos, qtd, vencidas_qtd, vence_qtd, atencao: [Conta], por_casa: [{id, nome, total_centavos, qtd}]}` (`por_casa` vazio no pessoal; sem `pagas_qtd` até a 07, Q23) |
| `GET /api/lancamentos/{id}/` | quem vê | `ContaDetalhe`; 404 se não vê |
| `PATCH /api/lancamentos/{id}/` | `editar_conta` | campos do POST, todos opcionais → `ContaDetalhe`; 404 se não vê; 409 cancelada |
| `POST /api/lancamentos/{id}/cancelar/` | `editar_conta` | → `ContaDetalhe`; 404 se não vê; 409 se não `aguardando`/`pendente` |
| `PATCH /api/grupos/{id}/` | `gerenciar_grupo` | `{janela_alerta_dias}` 1–7 → grupo (RN13) |
| `POST /api/grupos/{id}/sair/` | já existe | corpo opcional `{resolucoes: [...]}` (ADR 0007); novo 409 `conta_restrita_orfa` com `detail`, `contas: [{id, descricao}]`, `pessoas: [{id, nome}]`; 400 se uma resolução não é de conta que bloqueia |
| `DELETE /api/grupos/{id}/membros/{membro_id}/`, `PATCH /api/grupos/{id}/membros/{membro_id}/` | já existem | **contrato e respostas sem mudança** (Q17, Q19a): cancelamento automático e acesso preservado não aparecem para o admin |

- **Conta:** `id, espaco: {id, nome, tipo}, descricao, valor_centavos, vencimento, status, status_exibido, dias_para_vencer, subgrupo: {id, nome}|null, pagador: {id, nome, sou_eu}|null, visibilidade, criado_em`.
- **ContaDetalhe:** Conta + `criador: {nome, sou_eu}` ("Ex-membro" se nulo), `acesso: [{id, nome}]`, `historico: [{acao, autor, sou_eu, dados, criado_em}]`, `pode_editar`.
- Nome de pessoa: `nome` ou, se vazio, e-mail (regra da Etapa 03/M3).
- Contagens, totais, `atencao`, `por_casa` e as opções de pagador/casa do filtro saem de `lancamentos_visiveis`; canceladas fora de tudo, menos de `contagens.canceladas` e `status=canceladas` (D2). Sem campo de pagamento (`pago_centavos`) até a 07 (Q12).
- Opções do formulário (membros e casas) vêm de `GET /api/grupos/{id}/` (quem cria tem `ver_grupo`).

## Frontend

Reler HTML e screenshot (scale 2) de 02, D02, 03, D03, 07, 05, M01, 06, M02, 10, D04 e BillCard; citar os frames no topo de cada arquivo.

- **Base:** `components/bills/bill-card.tsx` (link para `/contas/<id>`; ícone `casa` com casa, senão `manual`; meta "Vence dd/mm · Mãe paga"/"Venceu dd/mm"/"Sem pagador"; cancelada riscada e opaca). `lib/contas/{client,hooks,formato}.ts`: R$ pt-BR, datas e nome do mês em `America/Fortaleza` por `Intl`; valor digitado "287,43" → 28743 sem biblioteca.
- **Espaço atual:** `lib/espaco.ts` lê o cookie `espaco` no servidor e o valida com `requireUser()`; o seletor (SideNav e pílula do cabeçalho do Início) grava o cookie e faz `router.refresh()`.
- **Início `/` (02/D02):** hero "Total de <mês>" com `count-up` (1,2s), varal `swing` (vencidas · vencem já; a conta "pagas" volta na 07, Q23), **sem barra**; "Precisa de atenção" (BillCard, `rise`) sem rótulo de mês e "Ver todas" → `/contas`; D02: saudação, "<Mês> de 2026 · <espaço>", grade de 2 colunas e "Por casa" (HouseCard: total e "N contas"). Sai a linha do healthcheck (`home-placeholder.tsx`).
- **Contas `/contas` (03/D03):** mês com setas, "Total de <mês>", Chips com contagem (Todas, A pagar, Vencidas, Pagas, Canceladas; desktop + "Casa" e "Quem paga"), botão "Filtros" no mobile (folha), grupos Vencidas · Esta semana · Mais adiante · Pagas, cada um com soma; vazio: frase curta.
- **Detalhe `/contas/[id]` (07 ↔ painel D03):** < 1024px página 07 com TopBar "Conta" (voltar, Editar); ≥ 1024px lista + painel `slide-in` com Editar e Fechar. Cor da conta pendurada pelo status. Info: Casa, Quem paga, Quem vê, Criada por; Histórico. Sem conta aberta no desktop: "Escolha uma conta". 404 da API = "Conta não encontrada", igual para inexistente e invisível.
- **Formulário** (`components/bills/conta-folha.tsx`, sobre `ui/folha.tsx`): criar e editar. "Onde fica" (só na criação), Valor, Vencimento (`type=date`), Descrição, Casa, Quem paga ("Eu" pré-selecionado; admin/membro/pagador), "Quem vê" (Todo o grupo / Só algumas pessoas com Chips de admin/membro/observador). **Aviso:** com "Só algumas pessoas" e pagador ≠ "Eu", texto "Quem paga também vê esta conta" logo abaixo de "Quem paga", em região `aria-live="polite"`, nas duas larguras. Editar acrescenta "Cancelar conta" (danger, `window.confirm`). Erros da API inline.
- **FAB e SideNav:** abrem o formulário com o espaço atual (ou o pessoal, se o papel não cria).
- **Grupo (10/D04):** HouseCard com total do mês e "N contas", sem barra (Q12); botão "Configurações" (D04) / ícone (10), só admin, abre folha/modal com "Avisar N dias antes" 1–7 (Q10).
- **RN32 na UI:** `sair-do-grupo.tsx`, no 409, vira a folha de saída barrada: `detail` e, por conta (link para `/contas/<id>`), "Escolher quem vê" (Chips de `pessoas`) ou "Cancelar conta"; "Sair" reenvia com `resolucoes`. A remoção de membro não muda (Q17). O formulário mostra o 400 da Q19b junto de "Quem vê". Histórico: ações automáticas sem autor.
- **Pagador (Q5):** `/grupos/[id]/simples` lista as contas dele (BillCard) acima de "Sair do grupo"; o detalhe abre sem Editar.
- Vitrine ganha BillCard (todos os status, inclusive cancelada).

## Validação e riscos

- pytest por papel e visibilidade, inclusive agregados e opções de filtro; relógio fixo para RN12/RNF11 (23h30 em Fortaleza); `select_for_update` na edição; RN32 com threads (dois saindo juntos; dois admins removendo juntos) e nos três caminhos de exclusão de `Usuario`; remoção órfã × não órfã com resposta comparada byte a byte. E2E: admin cria restrita e não escolhido não a vê nem nos totais; pagador fora dos escolhidos vê; aviso de visibilidade no formulário; bloqueio RN32 ao sair e saída com resolução; observador vê sem Editar; pagador só a dele em `/simples`; cancelar some do Início e aparece em "Canceladas"; trocar espaço; painel `slide-in`. Nas duas resoluções.
- **Vazamento por agregado ou por status HTTP:** total, contagens, "Por casa", opções de filtro ou um 403 no lugar de 404 revelariam restritas. Testes dedicados (CA07).
- **Fuso:** `vencimento` é data civil; comparar sempre com `timezone.localdate()`.
- **P5:** sem ela o limite de 20 cadastros/min por IP volta a derrubar o E2E.
- **Sinal ao admin (Q17, Q19a):** qualquer diferença de resposta, campo, contagem, log acessível ou atalho condicional entre remoção/troca com e sem conta órfã revela a restrita. Testes dedicados (CA21, CA24).
- **Exceção da RN05 (ADR 0007):** só existe no corpo de `sair`; nenhum outro endpoint aceita `resolucoes` (CA23).
