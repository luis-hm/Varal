# Plano — Etapa 03 (Espaços e grupos)

> **Contém:** o que cada agente faz, o filtro central de acesso, modelos, contratos de API, telas sem frame e riscos da Etapa 03.
> **Origem:** [spec.md](spec.md) (decisões resolvidas em 14/11/2026), [ADR 0004](../../arquitetura/adr/0004-rn31-link-de-convite.md), [modelo](../../dados/modelo.md), [design](../../design/README.md), guia `varal-ui` e código da `main` em 14/11/2026 (`apps/espacos`, `config/settings.py`, `web/src/components/layout`, `web/src/lib/auth`).

Sem dependências novas: `<dialog>`, Web Share e Clipboard são nativos; DRF (`ScopedRateThrottle`), cache Redis, React Query e o cliente CSRF da Etapa 02 já existem.

## Agentes

| Ordem / agente | Responsabilidade |
| --- | --- |
| varal-boletos | Não se aplica |
| varal-backend | Modelos, migrações, `acesso.py`, serviços, guarda RN04 na exclusão de `Usuario`, endpoints, throttle, `/api/me/`, seed, testes |
| `make types` | Schema e `web/src/types/api.ts` antes do frontend |
| varal-frontend | Reler 10, D04, 11, M05 e componentes; RadioCard, MemberRow, HouseCard, folha/modal; `/grupos`, `/grupos/[id]`, `/grupos/[id]/simples`, `/c/[token]`; telas sem frame; `proximo`; seletor; vitrine |
| varal-devops | Nada previsto; só se o E2E com dois usuários pedir ajuste |
| varal-qa | CA01–CA22, E2E com quatro papéis e API real, comparação visual com as diferenças esperadas (CA18) |
| varal-seguranca | Permissões por papel, IDOR em rotas aninhadas, token (hash, entropia, uso único, revogação, ausência em logs), limite de aceite, `proximo`, concorrência RN04/RN24, guarda de exclusão |
| varal-docs | Relatório, PROGRESSO, matriz, `dados/modelo.md`, `api/README.md`, `design/README.md`, `movimento.md` |

## Filtro central de acesso (`api/apps/espacos/acesso.py`)

Toda view que recebe id de espaço, membro, casa ou convite parte daqui; nenhuma view monta queryset de espaço por conta própria.

| Função | Faz |
| --- | --- |
| `espacos_do_usuario(usuario)` | QuerySet: o pessoal dele + grupos em que tem `Membro` (RN01/RN02) |
| `papel(usuario, espaco)` | `"dono"` no próprio pessoal, o papel no grupo, ou `None` |
| `PERMISSOES` | Constante papel → ações: `ver_grupo`, `criar_conta`, `editar_conta`, `pagar_qualquer`, `pagar_propria`, `gerenciar_grupo`. Dono e admin: tudo; membro: tudo menos `gerenciar_grupo`; observador: `ver_grupo`; pagador: `pagar_propria` (sem `ver_grupo`, decisão 6) |
| `espaco_ou_404(usuario, espaco_id, acao=None)` | 404 se não participa (não revela existência); 403 se participa e o papel não tem a ação; `acao=None` só exige participar (usado em "sair") |

Etapa 04 acrescenta `lancamentos_visiveis(usuario, espaco)` com RN02, RN06, RN07. Rotas aninhadas buscam o objeto **filtrando pelo espaço já autorizado**, nunca só pelo id.

## Modelos e migrações (`apps/espacos`)

1. **Espaco:** `dono` só no pessoal; `CheckConstraint` `tipo=grupo` ⇒ `dono` nulo. Migração de dados converte grupo com dono, se houver, em `Membro` admin.
2. **Membro:** `id` UUID, `espaco` (CASCADE), `usuario` (CASCADE), `papel` (`admin|membro|pagador|observador`), `criado_em`; `UniqueConstraint(espaco, usuario)`. RN03 validado no serviço, com teste.
3. **Convite (RN31):** `id`, `espaco` (CASCADE), `papel`, `token_hash` (SHA-256 hex, 64, único), `expira_em`, `usado_por` (SET_NULL), `usado_em`, `revogado_em`, `criado_por` (SET_NULL), `criado_em`. Token em claro só na resposta da criação; nunca em coluna, log, admin ou resposta posterior.
4. **Subgrupo:** `id`, `espaco` (CASCADE), `nome` (150), `arquivado` (falso).
5. **Guarda RN04 na exclusão de conta:** receptor `pre_delete` de `Usuario` (dispara em `obj.delete()`, `queryset.delete()` e no admin; roda dentro da transação do `Collector`): trava com `select_for_update` os `Membro` admin dos grupos onde ele é admin e, se for o único em algum, levanta erro de domínio e nada é apagado. No admin do Django, a recusa aparece como mensagem, não como 500.
6. Admin do Django: os quatro modelos só leitura (sem `token_hash` na lista). `make seed`: grupo "Família" com `dev` admin, mais um usuário por papel e duas casas, idempotente.

Lembrete para a Etapa 04: `lancamento.criador` não pode ser `CASCADE` (RN30).

## Serviços (`apps/espacos/servicos.py`)

Toda escrita em `transaction.atomic()`.

- `criar_grupo(usuario, nome, casas)`: espaço + `Membro` admin + casas.
- `gerar_convite(admin, grupo, papel)`: recusa pessoal (RN03); `token = secrets.token_urlsafe(32)`; grava `sha256(token)`; `expira_em = agora + 7 dias`; devolve o token uma vez.
- `revogar_convite(admin, grupo, convite_id)`: só pendente; marca `revogado_em`.
- `aceitar_convite(usuario, token)`: busca por `sha256(token)` com `select_for_update`; expirado/usado/revogado/inexistente → mesmo erro; já membro → erro sem consumir; senão cria `Membro` e marca usado.
- `alterar_papel`, `remover_membro` (admin), `sair(usuario, grupo)` (qualquer papel): `select_for_update` em todos os `Membro` admin do grupo antes de contar (RN04). `remover_membro`/`sair` são o ponto único da RN21 (04: contas sem pagador; 09: aviso).
- `criar_casa`, `renomear_casa`, `arquivar_casa`.

## Contratos de API

DRF autenticado e com CSRF. Exceção: `GET /api/convites/{token}/` aceita anônimo (token de 256 bits; sem limite por IP até a P3). Erros de regra com mensagem em pt-BR.

| Método e caminho | Quem | Entrada → saída |
| --- | --- | --- |
| `GET /api/me/` | autenticado | acrescenta `grupos: [{id, nome, papel}]` |
| `GET /api/grupos/` | autenticado | `id, nome, papel, membros_qtd, casas_qtd` (contagens `null` para pagador) |
| `POST /api/grupos/` | autenticado | `{nome, casas?: [nome]}` → 201 grupo |
| `GET /api/grupos/{id}/` | `ver_grupo` (pagador 403) | `id, nome, meu_papel, membros: [{id, nome, email, papel, sou_eu}], casas: [{id, nome}]` (não arquivadas) |
| `POST /api/grupos/{id}/sair/` | participante | 204; 409 se RN04 |
| `POST /api/grupos/{id}/convites/` | `gerenciar_grupo` | `{papel}` → `{id, url, expira_em, papel}` (`url` = `FRONTEND_URL/c/<token>`, só aqui) |
| `GET /api/grupos/{id}/convites/` | `gerenciar_grupo` | pendentes: `[{id, papel, criado_em, expira_em, criado_por_nome}]` |
| `DELETE /api/grupos/{id}/convites/{cid}/` | `gerenciar_grupo` | 204 (revoga) |
| `GET /api/convites/{token}/` | qualquer | `{grupo_nome, papel, expira_em}`; 410 para expirado, usado, revogado ou inexistente (mesma resposta) |
| `POST /api/convites/{token}/aceitar/` | autenticado; throttle `convite_aceite` = `10/hour` por usuário | 201 `{grupo_id, papel}`; 410; 409 já membro; 429 |
| `PATCH /api/grupos/{id}/membros/{mid}/` | `gerenciar_grupo` | `{papel}`; 409 se RN04 |
| `DELETE /api/grupos/{id}/membros/{mid}/` | `gerenciar_grupo` | 204; 409 se RN04 |
| `POST /api/grupos/{id}/subgrupos/` | `gerenciar_grupo` | `{nome}` → 201 |
| `PATCH /api/grupos/{id}/subgrupos/{sid}/` | `gerenciar_grupo` | `{nome?, arquivado?}` |

`email` dos membros só vai a quem vê o grupo (`ver_grupo`). O throttle usa `ScopedRateThrottle` (chave = id do usuário autenticado) sobre o cache Redis já configurado; conta toda tentativa.

## Frontend

- Reler HTML e screenshot (scale 2) de 10, D04, 11, M05 e de RadioCard, MemberRow, HouseCard; citar os frames no topo de cada arquivo.
- **Componentes:** `ui/radio-card.tsx` (`input type=radio` nativo), `groups/member-row.tsx`, `groups/house-card.tsx`, `ui/folha.tsx` (`<dialog>` com `showModal()`; CSS decide folha `sheet-up` < 1024px ou modal `modal-pop` ≥ 1024px).
- **`/grupos/[id]` (10/D04):** conteúdo da decisão 4. Ações por `meu_papel` (o backend decide): admin vê "Convidar pessoa"/"+ Convidar", "+ Nova casa", HouseCard e MemberRow clicáveis e "Convites pendentes"; membro e observador, nada disso. 403 da API → `router.replace('/grupos/<id>/simples')`.
- **Convite (11/M05):** ao abrir, gera convite com o papel marcado (Pagador, como no frame); trocar o papel revoga o anterior e gera outro (o `shine` recomeça); fechar sem copiar nem compartilhar revoga. Exibe `host/c/` + 8 primeiros + `…` + 4 últimos caracteres do token; copiar e compartilhar usam a `url` inteira; `aria-label` "Link do convite, copiar".
- **`/grupos/[id]/simples`:** "Em breve" com o nome do grupo (de `/api/me/`) e "Sair do grupo" (Q3); a Etapa 10 troca pelo 13/D05.
- **`/c/[token]`:** fora do segmento protegido, no layout de autenticação. **`proximo`** no login, cadastro e retorno Google: só caminho local (começa com `/`, não `//`, sem esquema); Google leva no `callback_url`.
- **SideNav:** seletor usa `user.grupos` de `/api/me/`; menu com Pessoal, cada grupo (pagador → `/simples`) e "Criar grupo". Mobile: aba Grupos.
- Cliente em `web/src/lib/grupos/` com tipos gerados e CSRF de `lib/auth`; após mutação, `router.refresh()`. Vitrine ganha os quatro componentes.

## Telas sem frame

Guia `varal-ui`: componentes existentes, folha < 1024px e modal centralizado ≥ 1024px, margem 20px (cards 12px) no mobile e 28px 40px no desktop, botões 52px, alvo 44px, título em `--font-display`. Quando houver frame, ele manda.

| Tela | Composição |
| --- | --- |
| `/grupos` | Título "Grupos"; cards brancos `--radius-lg` (nome, "N membros · N casas", papel em texto); vazio: frase + botão. "Criar grupo" (Button primary) abre folha/modal: Field "Nome do grupo", Fields de casas com "+ Adicionar casa", Button "Criar grupo" |
| Aceite `/c/[token]` | Layout 01 ↔ D01. "Convite para" + nome do grupo, papel com o texto do RadioCard correspondente (sem seleção), validade. Sem sessão: "Entrar" e "Criar conta" (ghost). Com sessão: "Aceitar convite". Inválido: "Este convite não vale mais. Peça um novo a quem convidou." |
| Gestão do membro | Admin toca MemberRow → folha/modal: nome ou e-mail, 4 RadioCard (textos do convite), "Salvar papel", "Remover do grupo" (danger, com confirmação). Erro RN04 inline |
| Casa | "+ Nova casa" → Field "Nome da casa" + "Criar". Admin toca HouseCard → Field nome, "Salvar", "Arquivar casa" (ghost, com confirmação) |
| Convites pendentes | Card abaixo de Membros (só admin, se houver): papel, "Expira em N dias", "Revogar" (ghost) |
| Sair | "Sair do grupo" (ghost) ao fim da página para todo papel que a vê; erro RN04 inline |
| Menu do seletor | Popover abaixo do seletor do SideNav: Pessoal, grupos com papel, divisória, "Criar grupo"; Esc fecha |

## Validação e riscos

- pytest com cada papel, concorrência (RN04: dois admins se rebaixando; RN24: dois aceites) com threads e banco real, exclusão de `Usuario` pelos três caminhos, throttle com cache limpo por teste. E2E: A cria grupo e convida Pagador; B anônimo abre o link, cria conta, aceita e cai em `/simples`; A convida C como Observador (página sem ações); A revoga um convite; A sozinho não sai; D recebe 404. Nas duas resoluções.
- **P3:** limite por IP no aceite só depois da cadeia de proxies (ADR 0004).
- **P4:** HTTPS interno em produção (Etapa 11).
