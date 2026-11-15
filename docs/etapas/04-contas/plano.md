# Plano — Etapa 04 (Contas, núcleo)

> **Contém:** o que cada agente faz, visibilidade no `acesso.py`, modelos e migrações, serviços (com a guarda RN32), contratos de API, telas e riscos da Etapa 04.
> **Origem:** [spec.md](spec.md) (decisões resolvidas em 15/11/2026; Q17–Q23 abertas), [modelo](../../dados/modelo.md), [ADR 0003](../../arquitetura/adr/0003-rn30-exportar-e-excluir-dados.md), [ADR 0005](../../arquitetura/adr/0005-rf11-sem-categoria.md), [ADR 0006](../../arquitetura/adr/0006-rn32-conta-restrita-orfa.md), [design](../../design/README.md), [movimento](../../design/movimento.md), guia `varal-ui` e código da `main` em 15/11/2026 (`apps/espacos/{acesso,servicos,models}.py`, `apps/lancamentos` vazio, `web/src/components/layout`, `bills/status-badge.tsx`).

Sem dependências novas: `Intl.NumberFormat`/`DateTimeFormat` (R$, fuso e nome do mês), `<input type="date">`, `<dialog>` da Etapa 03, `requestAnimationFrame` para o `count-up`, cookies do Next.

## Agentes

| Ordem / agente | Responsabilidade |
| --- | --- |
| varal-boletos | **Não se aplica** (sem código de barras, Pix nem PDF) |
| varal-backend | Modelos, migrações, `acesso.py` (visibilidade e `quem_ve`), status calculado, serviços com histórico, RN21 e RN32 em `_desligar`, guarda RN32 na exclusão de `Usuario`, janela RN13, endpoints, seed, testes |
| `make types` | Schema e `web/src/types/api.ts` antes do frontend |
| varal-frontend | Reler os frames da spec; BillCard; Início, Contas, Detalhe, formulário (com o aviso de visibilidade); seletor com cookie; FAB/"Nova conta"; "Configurações" do grupo; mensagem do 409 RN32; lista do pagador; HouseCard com dados; vitrine |
| varal-devops | P5: taxa de cadastro do allauth por variável só no E2E/CI (Q15) |
| varal-qa | CA01–CA29, E2E com os papéis e API real, comparação visual com as diferenças esperadas |
| varal-seguranca | Visibilidade (RN02/RN06/RN07) em lista, detalhe, **agregados**, contagens e opções de filtro; 404 e não 403; IDOR por id; validação de casa/pagador/escolhidos; cookie do espaço; RN21; RN32 e concorrência |
| varal-docs | Relatório, PROGRESSO, matriz, `dados/modelo.md`, `api/README.md`, `design/README.md`, `movimento.md` |

## Visibilidade (`api/apps/espacos/acesso.py`)

Uma definição só de "quem vê" (RN02, RN06, RN07), usada pelas consultas e pela RN32. Nenhuma view monta queryset de lançamento sozinha.

| Função | Faz |
| --- | --- |
| `lancamentos_visiveis(usuario, espaco)` | Pessoal do dono: tudo. Grupo, papel `pagador`: `pagador=usuario` (RN07). Admin, membro, observador: `visibilidade=grupo` ou `criador=usuario` ou `pagador=usuario` ou `usuario ∈ acesso` (RN06; admin sem exceção, Q6), `distinct`. Sem papel: vazio |
| `lancamento_ou_404(usuario, lancamento_id, acao=None)` | Busca em `lancamentos_visiveis` dos espaços do usuário; **404** se não vê; 403 só se vê e o papel não tem `acao` (`editar_conta`) |
| `quem_ve(lancamento, sem=None)` | Usuários membros do grupo que veem a conta pela mesma regra, tirando `sem` (quem está saindo) e já com a RN21 (quem sai não conta como pagador nem como escolhido). Base da RN32 |

`PERMISSOES` já tem `criar_conta`/`editar_conta` (dono, admin, membro). Criar usa `espaco_ou_404(usuario, id, "criar_conta")`.

## Modelos e migrações

**`apps/lancamentos` (0001):**

1. **Lancamento:** `id` UUID; `espaco` (CASCADE); `subgrupo?` (RESTRICT); `criador?` (SET_NULL, RN30); `pagador?` (SET_NULL); `descricao` (150); `valor_centavos` (`PositiveIntegerField`, `CheckConstraint > 0`, RN11); `vencimento` (`DateField`); `status` (`aguardando|pendente|paga|confirmada|cancelada`, padrão `pendente`, `CheckConstraint`, RN12); `visibilidade` (`grupo|restrita`, padrão `grupo`); `acesso` (`ManyToManyField` para `Usuario`, tabela `lancamento_acesso`); `criado_em`, `atualizado_em`. Índice `(espaco, vencimento)`.
2. **Historico:** `id`; `lancamento` (CASCADE); `usuario?` (SET_NULL, "Ex-membro"); `acao` (`criada|editada|cancelada|pagador_removido`); `dados` (JSON); `criado_em`. Ordem `criado_em`.
3. Ficam para as etapas delas: `tipo` (v3), `recorrencia` (08), `origem` (10), `instrumento` (05). **Categoria não existe** (ADR 0005).

**`apps/espacos` (0006):** `CheckConstraint` `janela_alerta_dias` entre 1 e 7.

**QuerySet `com_status(janela, hoje)`** em `lancamentos/models.py`: anota `status_exibido` com `Case/When` sobre `pendente` (`vencida`, `vence`) para filtrar e contar no SQL. `hoje = timezone.localdate()`.

Admin do Django: Lancamento e Historico só leitura. Seed: no pessoal do `dev` e na "Família", contas vencida (mês anterior), vence, pendente de outro mês, cancelada, restrita com escolhidos, restrita com pagador fora dos escolhidos e uma do pagador; idempotente.

## Serviços (`apps/lancamentos/servicos.py`)

Toda escrita em `transaction.atomic()`, com `select_for_update` na conta ao editar ou cancelar.

- `validar(espaco, dados)`: casa do espaço e não arquivada; pagador membro com papel admin/membro/pagador (Q16); escolhidos membros com papel admin/membro/observador (decisão 7); no pessoal força pagador = dono, `grupo`, sem casa e sem escolhidos.
- `criar(usuario, espaco, dados)`: grava `pendente` + histórico `criada`.
- `editar(usuario, conta, dados)`: 409 se `cancelada`; grava só os campos mudados; histórico `editada` com `{campo: [antes, depois]}` (pagador e casa por nome; escolhidos por lista).
- `cancelar(usuario, conta)`: só `aguardando`/`pendente`, senão 409; histórico `cancelada`.
- `restritas_sem_quem_veja(grupo, usuario, travar=True)`: contas abertas (`aguardando|pendente`) e restritas do grupo em que `usuario` é criador, pagador ou escolhido, travadas com `select_for_update` em ordem de `pk`; devolve as que ficam com `quem_ve(conta, sem=usuario)` vazio (RN32).

### RN21 + RN32 em `espacos.servicos._desligar(grupo, ...)`

Ponto único de sair e remover (import local para evitar ciclo). Na transação, nesta ordem de travas (sem deadlock com RN04 e com `editar`):

1. Admins do grupo (RN04, já existe) → `Membro` alvo (já existe).
2. `restritas_sem_quem_veja(grupo, usuario)`; se houver, `ContaRestritaSemQuemVeja` (409, `code` `conta_restrita_orfa`) e nada muda. Para quem sai, o corpo lista `[{id, descricao}]` das contas e a orientação; para o admin que remove, conforme **Q17**.
3. RN21: contas abertas do grupo com `pagador=usuario` → `pagador=None` + histórico `pagador_removido`; tira o usuário do `acesso` das contas do grupo. Pagas e canceladas não mudam (Q7).
4. Apaga o `Membro`. Aviso ao admin na 09.

Concorrência: duas pessoas que são as únicas que veem a conta C e saem juntas travam a mesma linha de C; a segunda espera, relê (READ COMMITTED) sem a primeira e recebe 409. `editar` também trava C, então mudar "Quem vê" e sair não se cruzam.

### RN32 na exclusão de `Usuario`

Novo receptor `pre_delete` ao lado de `proteger_ultimo_admin` (mesma guarda RN04, roda dentro da transação do Collector em `obj.delete()`, `queryset.delete()` e no admin do Django): para cada grupo do usuário, `restritas_sem_quem_veja`; se houver, 409 com a orientação. O admin do Django (`contas_usuario/admin.py`) mostra a mensagem em vez de 500, como na RN04. A exclusão não passa por `_desligar` (o `Membro` cai em cascata e `pagador` vira nulo pelo `SET_NULL`); o histórico da RN21 nesse caminho fica com o endpoint da Etapa 11.

Em aberto: Q18 (último que vê sem `editar_conta`) e Q19 (alterar papel e editar a conta) podem acrescentar chamadas à mesma função.

## Contratos de API

DRF, sessão e CSRF. Erros de regra em pt-BR. Datas `AAAA-MM-DD`; instantes ISO 8601 UTC.

| Método e caminho | Quem | Entrada → saída |
| --- | --- | --- |
| `GET /api/espacos/{id}/lancamentos/` | participante (filtrado) | `?mes=AAAA-MM` (padrão: mês de hoje) `&status=todas\|a_pagar\|vencidas\|pagas\|canceladas` `&subgrupo=<id>` `&pagador=<id>\|nenhum` → `{mes, total_centavos, contagens: {todas, a_pagar, vencidas, pagas, canceladas}, itens: [Conta]}`. Sem paginação (limite de um mês) |
| `POST /api/espacos/{id}/lancamentos/` | `criar_conta` | `{descricao, valor_centavos, vencimento, subgrupo?, pagador?, visibilidade?, acesso?: [usuario_id]}` → 201 `ContaDetalhe` |
| `GET /api/espacos/{id}/resumo/` | participante (filtrado) | `{mes, janela_alerta_dias, total_centavos, qtd, vencidas_qtd, vence_qtd, pagas_qtd, atencao: [Conta], por_casa: [{id, nome, total_centavos, qtd}]}` (`por_casa` vazio no pessoal; `pagas_qtd` só para o varal, conforme Q23) |
| `GET /api/lancamentos/{id}/` | quem vê | `ContaDetalhe`; 404 se não vê |
| `PATCH /api/lancamentos/{id}/` | `editar_conta` | campos do POST, todos opcionais → `ContaDetalhe`; 404 se não vê; 409 cancelada |
| `POST /api/lancamentos/{id}/cancelar/` | `editar_conta` | → `ContaDetalhe`; 404 se não vê; 409 se não `aguardando`/`pendente` |
| `PATCH /api/grupos/{id}/` | `gerenciar_grupo` | `{janela_alerta_dias}` 1–7 → grupo (RN13) |
| `POST /api/grupos/{id}/sair/`, `DELETE /api/grupos/{id}/membros/{membro_id}/` | já existem | novo 409 `conta_restrita_orfa` (RN32) com `detail` e, para quem sai, `contas: [{id, descricao}]` |

- **Conta:** `id, espaco: {id, nome, tipo}, descricao, valor_centavos, vencimento, status, status_exibido, dias_para_vencer, subgrupo: {id, nome}|null, pagador: {id, nome, sou_eu}|null, visibilidade, criado_em`.
- **ContaDetalhe:** Conta + `criador: {nome, sou_eu}` ("Ex-membro" se nulo), `acesso: [{id, nome}]`, `historico: [{acao, autor, sou_eu, dados, criado_em}]`, `pode_editar`.
- Nome de pessoa: `nome` ou, se vazio, e-mail (regra da Etapa 03/M3).
- Contagens, totais, `atencao`, `por_casa` e as opções de pagador/casa do filtro saem de `lancamentos_visiveis`; canceladas fora de tudo, menos de `contagens.canceladas` e `status=canceladas` (D2). Sem campo de pagamento (`pago_centavos`) até a 07 (Q12).
- Opções do formulário (membros e casas) vêm de `GET /api/grupos/{id}/` (quem cria tem `ver_grupo`).

## Frontend

Reler HTML e screenshot (scale 2) de 02, D02, 03, D03, 07, 05, M01, 06, M02, 10, D04 e BillCard; citar os frames no topo de cada arquivo.

- **Base:** `components/bills/bill-card.tsx` (link para `/contas/<id>`; ícone `casa` com casa, senão `manual`; meta "Vence dd/mm · Mãe paga"/"Venceu dd/mm"/"Sem pagador"; cancelada riscada e opaca). `lib/contas/{client,hooks,formato}.ts`: R$ pt-BR, datas e nome do mês em `America/Fortaleza` por `Intl`; valor digitado "287,43" → 28743 sem biblioteca.
- **Espaço atual:** `lib/espaco.ts` lê o cookie `espaco` no servidor e o valida com `requireUser()`; o seletor (SideNav e pílula do cabeçalho do Início) grava o cookie e faz `router.refresh()`.
- **Início `/` (02/D02):** hero "Total de <mês>" com `count-up` (1,2s), varal `swing` (vencidas · vencem já · pagas conforme Q23), **sem barra**; "Precisa de atenção" (BillCard, `rise`) sem rótulo de mês e "Ver todas" → `/contas`; D02: saudação, "<Mês> de 2026 · <espaço>", grade de 2 colunas e "Por casa" (HouseCard: total e "N contas"). Sai a linha do healthcheck (`home-placeholder.tsx`).
- **Contas `/contas` (03/D03):** mês com setas, "Total de <mês>", Chips com contagem (Todas, A pagar, Vencidas, Pagas, Canceladas; desktop + "Casa" e "Quem paga"), botão "Filtros" no mobile (folha), grupos Vencidas · Esta semana · Mais adiante · Pagas, cada um com soma; vazio: frase curta.
- **Detalhe `/contas/[id]` (07 ↔ painel D03):** < 1024px página 07 com TopBar "Conta" (voltar, Editar); ≥ 1024px lista + painel `slide-in` com Editar e Fechar. Cor da conta pendurada pelo status. Info: Casa, Quem paga, Quem vê, Criada por; Histórico. Sem conta aberta no desktop: "Escolha uma conta". 404 da API = "Conta não encontrada", igual para inexistente e invisível.
- **Formulário** (`components/bills/conta-folha.tsx`, sobre `ui/folha.tsx`): criar e editar. "Onde fica" (só na criação), Valor, Vencimento (`type=date`), Descrição, Casa, Quem paga ("Eu" pré-selecionado; admin/membro/pagador), "Quem vê" (Todo o grupo / Só algumas pessoas com Chips de admin/membro/observador). **Aviso:** com "Só algumas pessoas" e pagador ≠ "Eu", texto "Quem paga também vê esta conta" logo abaixo de "Quem paga", em região `aria-live="polite"`, nas duas larguras. Editar acrescenta "Cancelar conta" (danger, `window.confirm`). Erros da API inline.
- **FAB e SideNav:** abrem o formulário com o espaço atual (ou o pessoal, se o papel não cria).
- **Grupo (10/D04):** HouseCard com total do mês e "N contas", sem barra (Q12); botão "Configurações" (D04) / ícone (10), só admin, abre folha/modal com "Avisar N dias antes" 1–7 (Q10).
- **RN32 na UI:** `sair-do-grupo.tsx` e a remoção de membro mostram o `detail` do 409 e, quando vier, a lista de contas com link para `/contas/<id>` (lá a pessoa muda "Quem vê" ou cancela). Texto do admin conforme Q17.
- **Pagador (Q5):** `/grupos/[id]/simples` lista as contas dele (BillCard) acima de "Sair do grupo"; o detalhe abre sem Editar.
- Vitrine ganha BillCard (todos os status, inclusive cancelada).

## Validação e riscos

- pytest por papel e visibilidade, inclusive agregados e opções de filtro; relógio fixo para RN12/RNF11 (23h30 em Fortaleza); `select_for_update` na edição; RN32 com threads (dois saindo juntos) e nos três caminhos de exclusão de `Usuario`. E2E: admin cria restrita e não escolhido não a vê nem nos totais; pagador fora dos escolhidos vê; aviso de visibilidade no formulário; bloqueio RN32 ao sair; observador vê sem Editar; pagador só a dele em `/simples`; cancelar some do Início e aparece em "Canceladas"; trocar espaço; painel `slide-in`. Nas duas resoluções.
- **Vazamento por agregado ou por status HTTP:** total, contagens, "Por casa", opções de filtro ou um 403 no lugar de 404 revelariam restritas. Testes dedicados (CA07).
- **Fuso:** `vencimento` é data civil; comparar sempre com `timezone.localdate()`.
- **P5:** sem ela o limite de 20 cadastros/min por IP volta a derrubar o E2E.
- **Q17–Q23 abertas:** a resposta ao admin no 409 (Q17), os casos sem quem possa editar (Q18), os outros caminhos da RN32 (Q19), o CU04 alternativo (Q20) e o varal do hero (Q23) mudam pontos do código; o resto não depende delas.
