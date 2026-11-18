# Handoff ao Codex — o que falta na Etapa 12

> **Contém:** tudo o que ainda falta na etapa 12, passo a passo, com arquivos, comandos e critérios de pronto.
> **Origem:** sessão do Claude Code de 18/11/2026, que fez COR-01 a COR-09, COR-11 e COR-12 (parte de código).
> Leia **inteiro** antes de começar. Faça na ordem. Não pule a seção 0.

## 0. Regras que valem o tempo todo

1. Leia antes: `CLAUDE.md`, `AGENTS.md`, `docs/PROGRESSO.md`, [spec](spec.md), [decisões](decisoes.md), [ADR 0016](../../arquitetura/adr/0016-categorias-com-icone.md), [ADR 0017](../../arquitetura/adr/0017-permissoes-por-categoria.md) e [correções do teste inicial](../../produto/correcoes-teste-inicial-2026-11-16.md).
2. Branch: `etapa/12-correcoes-teste`. **Não** faça push, merge nem deploy.
3. **Não use o banco de dev** (`make migrate`, `make seed`, `make dev` com o volume `varal_pgdata`): a senha do Postgres local não bate com o volume. Rode os testes da API num projeto Compose isolado chamado `varaltest`:
   ```sh
   # na raiz do repositório
   docker compose -p varaltest -f infra/docker-compose.yml run --rm --user $(id -u):$(id -g) api pytest -q -p no:cacheprovider
   # um arquivo só:
   docker compose -p varaltest -f infra/docker-compose.yml run --rm --user $(id -u):$(id -g) api pytest -q -p no:cacheprovider tests/test_contas.py
   # ruff (não existe no host):
   docker compose -p varaltest -f infra/docker-compose.yml run --rm --no-deps --user $(id -u):$(id -g) api sh -c "ruff format apps tests; ruff check apps tests"
   # gerar migração:
   docker compose -p varaltest -f infra/docker-compose.yml run --rm --user $(id -u):$(id -g) api python manage.py makemigrations espacos
   ```
   Se a porta 9000 estiver ocupada, pare a stack de dev com `docker compose -f infra/docker-compose.yml stop` (**nunca** `down -v`).
4. Web (em `web/`): `npx vitest run`, `npx tsc --noEmit`, `npm run lint` (não use `npx eslint`). Rotas novas exigem `npx next typegen`. Contrato da API mudou → `make types` na raiz.
5. Canvas do Doop `k0kB5dc-Vo` é **somente leitura**. Toda tela cita os frames no topo do arquivo.
6. Domínio em português sem acento; dinheiro em centavos; UUID; permissão sempre no backend; teste de regra com o ID no nome (`test_cor10_...`, `test_rn07_...`).
7. Commits Conventional Commits em pt-BR, terminando com uma linha `Co-Authored-By:` do agente. Docs mudam no mesmo commit do código.
8. Regra de negócio, privacidade, dados gravados e texto de tela novo são do dono: se algo não está escrito aqui ou no ADR, **pergunte**, não invente.

## 1. O que já está pronto (não refaça)

| Commit | O quê |
| --- | --- |
| `c806774` | COR-01 (sessão não mascara ao voltar à aba: `web/src/components/auth/sessao-guard.tsx`, `bootstrap-sessao.ts`, `lib/auth/isolamento.ts`) e COR-12 (referrer `strict-origin` em `/entrar` e `/criar-conta`: `web/next.config.ts`, `infra/deploy/edge.conf.template`, `infra/lab/nginx.conf`). |
| `7aa9ad1` | API: `Subgrupo.icone` (migração `0007`), lista sem mês obrigatório, `subgrupo=nenhum`, `opcoes.sem_categoria`, `por_casa` com linha "Sem categoria" (`id: null`) e `abertas_qtd`. |
| `1f7e9ba` | Web: ícones de categoria (`web/src/lib/categorias/icones.ts`, 12 ícones novos em `components/ui/icon.tsx`), Contas sem mês e com `?espaco=`, tela da categoria (`components/groups/categoria-pagina.tsx`, rotas `app/(app)/grupos/[id]/categorias/[categoria]/...`), Nova conta com destino (`destinoDaTela` em `components/layout/app-shell.tsx`), cards de categoria no grupo. |
| `905a43a` | Perfil redesenhado (COR-09), espaçamento do Início e do detalhe. |

Situação: API 569 testes verdes; web 170 testes verdes; `tsc` e lint limpos. **E2E não foi rodado** depois das mudanças (seção 4).

## 2. COR-10 — Permissões por categoria — **feito** (ADR 0017 aprovado em 18/11/2026)

Não reimplemente. O que existe:

- **Modelo:** `Subgrupo.personalizada`, `Subgrupo.versao`, `PermissaoCategoria`, `HistoricoPermissao` (migração `api/apps/espacos/migrations/0008_permissoes_categoria.py`).
- **Regra central** em `api/apps/espacos/acesso.py`: `capacidades(usuario, papel, subgrupo_id)`, `pode_na(usuario, papel, subgrupo_id, acao)`, `categorias_visiveis(...)`. `_ve` esconde contas "do grupo" de categorias personalizadas para membro/observador sem `ver` (criador, pagador e escolhidos continuam vendo). `lancamento_ou_404` e `recorrencia_ou_404` checam a ação na categoria.
- **Serviços:** `lancamentos.servicos.criar/editar/cancelar`, `recorrencias.servicos.criar/editar_modelo`, `pagamentos.servicos.pode_pagar`.
- **API:** `GET/PUT /api/grupos/{id}/subgrupos/{casa}/permissoes/` (admin; versão antiga dá 409); `casas[].capacidades` e `casas[].personalizada` no detalhe do grupo.
- **Web:** `web/src/components/groups/permissoes-folha.tsx` (aberta por "Quem pode fazer o quê" dentro de "Editar categoria"); a Nova conta só oferece categorias com `criar` e as recorrências só com `recorrencias`; o grupo do observador aparece na Nova conta só a partir das telas daquele grupo.
- **Testes:** `api/tests/test_permissoes_categoria.py` (23, com os achados da revisão de segurança), `grupo-pagina.test.tsx` e `conta-folha.test.tsx` (casos COR-10).

**O que falta (E2E, seção 4):** um teste que, nas duas larguras, faça o admin personalizar "Energia" tirando "Ver" do membro, e confira que o membro não vê a categoria nem a conta e que `GET /api/lancamentos/{id}/` dá 404 para ele.

## 3. Auditoria do escopo inicial

Itens encontrados na auditoria e ainda abertos. Faça um commit por item.

### 3.1 Trocar `window.confirm` por `Folha` — **feito** (commit "fix(web): confirmacoes em folha...")

`web/src/components/ui/confirmar.tsx` (`useConfirmar`) substituiu os 5 `window.confirm` (remover membro, sair do grupo, encerrar recorrência, desfazer pagamento, cancelar conta). O título da folha é a pergunta; o botão vermelho repete a ação ("Remover do grupo", "Sair", "Encerrar", "Desfazer pagamento", "Cancelar conta"); a `Folha` já põe o "Cancelar". **Consequência no E2E:** `page.on("dialog", d => d.accept())` não confirma mais nada; depois do clique, o teste precisa clicar no botão dentro do diálogo, por exemplo:
```ts
await page.getByRole("button", { name: "Sair do grupo" }).click();
await page.getByRole("dialog", { name: /Sair de / }).getByRole("button", { name: "Sair" }).click();
```
Arquivos com `page.on("dialog")`: `e2e/fixtures.ts:123`, `contas.spec.ts:32`, `pagamentos.spec.ts:12`, `solicitacoes.spec.ts:13`, `recorrencias.spec.ts:72`, `grupos.spec.ts:34`.

### 3.2 Nome do usuário (depende da Q12-2 do dono)

Só se o dono aprovar: campo "Seu nome" opcional no cadastro (`web/src/components/auth/`), `PATCH /api/me/ {nome}` em `api/apps/contas_usuario/`, campo editável na seção "Seus dados" do Perfil (`web/src/components/perfil/perfil.tsx`). Sem aprovação, não mexa.

### 3.3 Textos inconsistentes — **feito em parte**

- "5 MiB" → "5 MB" em `comprovante-campo.tsx` e `pagamento-acoes.tsx` (feito).
- "voltará a ficar pendente" → "volta a ficar pendente" (feito).
- **Não mexa** em "Eu" (opção de pagador na Nova conta, decisão Q16 da etapa 04) nem em "Aguardando conferência" do modo simples (rótulo próprio da etapa 10): vêm de decisões anteriores. Se achar que devem mudar, pergunte ao dono.

### 3.4 Fluxos incompletos do escopo inicial

1. **CU02 — convite depois de criar grupo — feito:** criar grupo navega para `/grupos/{id}?convidar=1` e a folha de convite abre uma vez (teste em `grupo-pagina.test.tsx`). Falta o E2E (`grupos.spec.ts` que cria grupo deve fechar ou usar essa folha).
2. **CU01 — e-mail já cadastrado — feito:** com `email_taken` no cadastro aparece "Já existe uma conta com este e-mail. Entrar ou recuperar a senha." (`auth-form.tsx`). Não preenche o e-mail na recuperação (não foi pedido).
3. **CU05 — PDF sem código — feito:** os estados reais do PDF são `pendente`, `lido`, `conferencia_manual` e `invalido` (a folha testava um `"falhou"` que não existe). Agora `invalido` mostra "Escolha outro arquivo ou cole o código" e `conferencia_manual` sem candidatos mostra "Não achamos o código neste PDF. Colar código" (`conta-folha.tsx`). Falta o E2E em `pdf.spec.ts`.
4. **Recorrência clicada — feito:** o grupo passa `inicial={r.id}` para `RecorrenciasFolha`. Falta só um E2E que clique numa recorrência e veja o detalhe dela.

### 3.5 Limpeza

- `grep -rn "px" web/src/components --include=*.module.css` e troque valores soltos de espaçamento por tokens (`var(--spacing-N)`) quando houver token igual. Não mexa em larguras fixas do design (264px do SideNav, 52px do botão, 44px de alvo).
- Margem lateral de 20px (`var(--spacing-5)`) no mobile em Avisos, Perfil (já feito) e modo simples.
- Código morto — **feito:** apagados `em-breve.tsx`/`em-breve.module.css`, `contas-pagador.tsx` e o `simples.module.css` da rota (o de `components/simple/` está em uso).
- Comentários "stays in stage N" / "fica para a etapa N" já superados: atualize ou apague.

## 4. E2E (Playwright)

O E2E **não foi rodado** depois das mudanças e vai quebrar nestes pontos conhecidos (procure outros com `grep -n "casa\|Casa\|mes=" web/e2e/*.ts`):

| Arquivo:linha | Era | Agora |
| --- | --- | --- |
| `contas.spec.ts:118` | URL `/contas/{id}?mes=AAAA-MM` depois de criar | conta pessoal vai para `/contas/{id}` (sem mês); grupo vai para `/contas/{id}?espaco=...` ou para a base da categoria |
| `contas.spec.ts:182` | grupo de chips "Casa" | "Categoria" |
| `contas.spec.ts:211-213` | região "Por casa", texto "0 de 1 pagas em {mes}" | "Por categoria"; legendas: "R$ X em {mes}" e "1 conta a pagar" |
| `contas.spec.ts:224` | card com "0 de 1 pagas em {mes}" | "1 conta a pagar" |
| `contas.spec.ts:321,335` | filtro "Casa" | "Categoria" |
| `grupos.spec.ts:69-71,160,174` | "+ Nova casa", diálogo "Nova casa", "Nome da casa" | "+ Nova categoria", "Nova categoria", "Nome da categoria" |
| `grupos.spec.ts:407` e `recorrencias.spec.ts:189-190` | "Editar casa", "Arquivar casa" | "Editar categoria", "Arquivar categoria" |
| Testes que abrem `/contas` esperando o grupo do seletor | Contas seguia o cookie do espaço | Contas abre **pessoal**; use `/contas?espaco={id}` |
| Testes que esperam o mês atual na lista de Contas | mês obrigatório | lista mostra todos os meses ("Todos os meses") |
| `auth.spec.ts`, `identidade11.check.ts`, `privacidade11.spec.ts` | máscara ao trocar de aba | só mascara em `pagehide`/identidade trocada; voltar à aba revalida sem esconder |

Ao corrigir: mude o **teste** para o comportamento novo (ele é o pedido do dono), nunca o contrário. Rode `make e2e` (sobe API/worker; Playwright roda 390×844 e 1440×900). Acrescente E2E novos:
- Grupos → grupo → categoria → conta → voltar (COR-11), nas duas larguras.
- Criar categoria com ícone "Luz" e ver o ícone no card (COR-04).
- Conta sem categoria aparece em "Sem categoria" (COR-07).
- Trocar de aba e voltar sem pedir login (COR-01): `page.evaluate(() => document.dispatchEvent(new Event("visibilitychange")))`.
- Depois do COR-10: membro sem "Ver" não vê a categoria nem as contas; chamada direta à API dá 404.

## 5. Validação visual

Suba um ambiente isolado com seed (não o de dev) — por exemplo `docker compose -p varaltest -f infra/docker-compose.yml up -d` e `docker compose -p varaltest ... run --rm api python manage.py seed` (confira o comando real no `Makefile`, alvo `seed`) — e o Next com `npm run dev` apontando para ele. Tire capturas em **390×844 e 1440×900** de: Início, Contas (sem mês, com mês, com `?espaco=`), Grupo, Categoria, Nova conta (com destino), Detalhe, Perfil, Avisos. Compare com os frames do Doop (tabela em `docs/design/README.md`) e verifique:
- 24px (`--spacing-6`) entre seções; 20px de margem lateral no mobile;
- nada cortado/sobreposto em 360px de largura;
- foco visível e alvos de 44px.
Guarde as capturas em `docs/etapas/12-correcoes-teste/evidencias/`.

## 6. Documentação no fim

1. [relatorio.md](relatorio.md): marque o que foi feito, cole os números dos testes (API, web, E2E), pendências.
2. [tarefas.md](tarefas.md): marque as caixas.
3. `docs/PROGRESSO.md`: linha da etapa 12 e entrada no log (data, o que mudou, commits).
4. `docs/matriz-rastreabilidade.md`: linhas COR-01..12 → telas → testes.
5. `docs/dados/modelo.md`: `subgrupo` com `icone` (e `personalizada`, `versao`, `PermissaoCategoria` se COR-10 entrou).
7. Doc "Varal — Ajustes" (Claude Docs `ce521944-15d6-44a5-b70c-f0790e03de41`): leia ao vivo; se houver itens que esta etapa resolveu, só **acrescente** " — feito na etapa 12" no fim do item. Nunca apague nem reescreva.

## 7. Ações do dono (não são suas)

- Responder a Q12-2 (nome do usuário). O ADR 0017 já foi aprovado.
- Google Console: cadastrar `https://hmgvaral.codehub.systems/accounts/google/login/callback/` nas URIs de redirecionamento do cliente OAuth da HMG e testar o login Google na HMG (COR-12).

## 8. Pronto quando

- [ ] `docker compose -p varaltest ... pytest -q` verde (569 testes em 18/11/2026).
- [ ] `npx vitest run`, `npx tsc --noEmit`, `npm run lint` verdes em `web/`.
- [ ] `make types` sem diff.
- [ ] `make e2e` verde nas duas larguras.
- [ ] Capturas da seção 5 salvas.
- [ ] Docs da seção 6 atualizados, commits locais feitos, **sem push**.
