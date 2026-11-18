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

Situação: API 546+ testes verdes; web 164 testes verdes; `tsc` e lint limpos. **E2E não foi rodado** depois das mudanças (seção 4).

## 2. COR-10 — Permissões por categoria

**Só comece depois que o dono aprovar o [ADR 0017](../../arquitetura/adr/0017-permissoes-por-categoria.md)** (resposta no chat ou item no doc "Varal — Ajustes"). Se ele mudar a proposta, ajuste o ADR primeiro. Se não houver ok, pule para a seção 3.

### 2.1 Modelo (`api/apps/espacos/models.py`)

```python
class Subgrupo(models.Model):
    ...
    personalizada = models.BooleanField(default=False)   # False = vale o padrão do papel (regra atual)
    versao = models.PositiveIntegerField(default=1)      # concorrência otimista (409)

class PermissaoCategoria(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subgrupo = models.ForeignKey(Subgrupo, on_delete=models.CASCADE, related_name="permissoes")
    membro = models.ForeignKey("espacos.Membro", on_delete=models.CASCADE, related_name="permissoes_categoria")
    ver = models.BooleanField(default=False)
    criar = models.BooleanField(default=False)
    editar = models.BooleanField(default=False)
    pagar = models.BooleanField(default=False)
    recorrencias = models.BooleanField(default=False)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["subgrupo", "membro"], name="permissao_categoria_unica"),
            models.CheckConstraint(condition=Q(ver=True) | Q(criar=False, editar=False, pagar=False, recorrencias=False), name="permissao_exige_ver"),
        ]
```
Confira o nome real do modelo de membro em `api/apps/espacos/models.py` antes (pode ser `Membro`/`Participacao`). Migração `0008_...` com `makemigrations espacos`. Não crie linhas na migração: categoria existente fica `personalizada=False` (nada muda).

Histórico: grave cada alteração (autor, subgrupo, data, antes, depois em JSON). Se já existir um modelo de histórico de grupo em `apps/espacos`, reuse; senão, crie `HistoricoPermissao(subgrupo, autor SET_NULL, criado_em, antes JSONField, depois JSONField)`.

### 2.2 Autorização central (`api/apps/espacos/acesso.py`)

Hoje: `PERMISSOES` (por papel), `pode(papel, acao)`, `_ve(usuario, papel, modelo)` (Q de visibilidade), `lancamentos_visiveis`, `lancamento_ou_404`, `quem_ve`, `recorrencias_visiveis`, `recorrencia_ou_404`.

Faça:

1. Uma função `capacidades(usuario, espaco, subgrupo_id) -> frozenset[str]` com `{"ver","criar","editar","pagar","recorrencias"}`:
   - dono (pessoal) ou admin: todas.
   - papel `pagador`: vazio (o pagador vê/paga só pelo RN07, já tratado em `_ve` e `pode_pagar`).
   - `subgrupo_id` é `None` ou a categoria não é `personalizada`: deriva do papel como hoje (`membro` → ver, criar, editar, pagar, recorrencias; `observador` → ver).
   - categoria personalizada: lê a `PermissaoCategoria` do membro; sem linha = vazio.
2. `_ve` para `membro` e `observador`: a parte `Q(visibilidade=GRUPO)` vira `Q(visibilidade=GRUPO) & (Q(subgrupo__isnull=True) | Q(subgrupo__personalizada=False) | Q(subgrupo__permissoes__membro__usuario=usuario, subgrupo__permissoes__ver=True))`. **Mantenha** `| Q(criador=usuario) | Q(pagador=usuario) | Q(escolhido)` sem condição de categoria (criador/pagador/escolhido sempre veem). Use `Exists(...)` em vez de join para não duplicar linhas. Admin continua igual (não ganha restritas).
3. `pode(papel, acao)` continua para ações de grupo (`gerenciar_grupo`, `ver_grupo`). Para ações sobre conta, crie `pode_na_conta(usuario, conta, acao)` que usa `capacidades` com `conta.subgrupo_id`, mapeando: `criar_conta→criar`, `editar_conta→editar`, `pagar_qualquer→pagar`.
4. `recorrencias_visiveis`/`recorrencia_ou_404`: mesma regra usando `recorrencia.subgrupo`.

### 2.3 Pontos que precisam usar a regra nova (todos)

| Arquivo | O que mudar |
| --- | --- |
| `api/apps/lancamentos/servicos.py` `criar` (linha ~143) | Exigir `criar` na categoria escolhida (`dados["subgrupo"]`); sem categoria → padrão do papel. 403 se faltar. |
| `api/apps/lancamentos/servicos.py` `editar` (linha ~193) | Exigir `editar` na categoria **atual**; se mudar de categoria, exigir `criar` na **nova** também. |
| Cancelar conta (procure `cancel` em `apps/lancamentos`) | Exigir `editar`. |
| `api/apps/pagamentos/servicos.py` `pode_pagar` | `pagar` na categoria **ou** pagador atribuído (`pagar_propria` + `conta.pagador_id == usuario.pk`). `pode_desfazer`/`pode_anexar` seguem `pode_pagar`. |
| `api/apps/recorrencias/servicos.py` `criar` e ações (pausar/retomar/encerrar/editar) | Exigir `recorrencias` na categoria da recorrência. |
| `api/apps/solicitacoes/` | Pedir para alguém pagar: quem pede precisa `ver`; o destinatário continua pelo fluxo atual (ADR 0014). Não amplie acesso. |
| `api/apps/boletos/` downloads de PDF/comprovante | Já passam por `lancamento_ou_404`; confirme com teste que categoria sem `ver` dá 404. |
| `api/apps/notificacoes/` | Lembretes e avisos usam `quem_ve`; confirme que `quem_ve` usa o mesmo `_ve` (deve usar). Teste: membro sem `ver` não recebe lembrete. |
| `ResumoView` e `LancamentosView` (`api/apps/lancamentos/views.py`) | Já partem de `lancamentos_visiveis`; `por_casa` deve esconder categorias personalizadas sem `ver` para quem não é admin, e totais/contagens não podem contar contas invisíveis. |
| Serializers de conta/categoria | Devolver `pode` por conta (`{"editar": bool, "pagar": bool, "cancelar": bool}`) e por categoria (`{"criar": bool, "recorrencias": bool}`) para a UI esconder botões. A UI só esconde; a API é que recusa. |

### 2.4 Endpoints (admin do grupo)

- `GET /api/espacos/{espaco}/casas/{id}/permissoes/` → `{personalizada, versao, membros: [{membro_id, nome, papel, ver, criar, editar, pagar, recorrencias}]}` (membros atuais `membro`/`observador`; se não personalizada, os valores mostram o padrão do papel).
- `PUT` no mesmo caminho com `{personalizada, versao, membros: [...]}`: só admin/dono (`gerenciar_grupo`), `versao` diferente → 409, `pagar/criar/editar/recorrencias` sem `ver` → 400, membro de outro grupo → 400, categoria "Sem categoria" não existe aqui (só categorias reais). Incrementa `versao` e grava histórico numa transação (`select_for_update` no subgrupo).
- Siga o padrão das views de casas já existentes em `api/apps/espacos/views.py` (`CasaSerializer`, `CasaAlterarSerializer`). Rode `make types`.
- Saída/remoção de membro: a linha some em cascata. Exclusão de usuário (RN30): idem.

### 2.5 Testes da API (`api/tests/test_permissoes_categoria.py`, novo)

Nomeie com o ID. Mínimo:
1. `test_cor10_sem_personalizar_nada_muda` (membro vê, cria, paga como antes).
2. `test_cor10_observador_pode_criar_se_admin_permitir`.
3. `test_cor10_membro_sem_ver_nao_lista_nem_abre_detalhe` (lista, detalhe 404, totais, contagens, `por_casa`, filtro de opções, PDF/comprovante 404).
4. `test_cor10_ver_nao_abre_restrita` (ADR 0008 continua).
5. `test_cor10_criador_e_pagador_sempre_veem`.
6. `test_cor10_pagar_exige_permissao_ou_ser_pagador`.
7. `test_cor10_mudar_categoria_exige_criar_na_nova`.
8. `test_cor10_recorrencias_exige_permissao`.
9. `test_cor10_so_admin_altera_permissoes` (membro → 403; outro grupo → 404).
10. `test_cor10_versao_antiga_da_409`.
11. `test_cor10_permissao_sem_ver_da_400`.
12. `test_cor10_ids_de_outro_grupo_nao_dao_acesso` (trocar `espaco`/`subgrupo` na URL).
13. `test_cor10_revogar_vale_na_proxima_consulta`.
14. `test_cor10_lembrete_nao_vai_para_quem_nao_ve`.
15. `test_cor10_membro_removido_perde_permissoes`.

### 2.6 Tela (web)

- No card da categoria do grupo (`components/groups/grupo-pagina.tsx`, `CasaFolha` "Editar categoria"), admin vê o botão "Quem pode fazer o quê". Abre uma `Folha` (`components/ui/folha.tsx`; no desktop vira modal, no mobile folha de baixo) com:
  - interruptor "Personalizar permissões desta categoria" (desligado = texto "Vale o padrão de cada papel");
  - ligado: uma linha por membro com nome, papel e 5 caixas (Ver, Cadastrar, Editar, Pagar, Recorrências). Desmarcar "Ver" desmarca e desabilita as outras;
  - botões "Salvar" e "Cancelar"; 409 → mensagem "Outra pessoa mudou estas permissões. Recarregue para ver a versão atual." com botão "Recarregar".
- Esconda "+ Nova conta" e botões de editar/pagar/cancelar quando o `pode` da API disser `false`. Não confie só nisso.
- Hooks em `web/src/lib/grupos/hooks.ts` (siga o padrão dos hooks de casa/categoria que já existem ali; todos chamam `call()` de `web/src/lib/grupos/client.ts`).
- Testes Vitest: abrir a folha, desmarcar Ver desabilita o resto, 409 mostra a mensagem, membro comum não vê o botão.
- **Texto e layout novos são tela**: antes de implementar, mostre ao dono um rascunho (lista dos textos acima) se ele ainda não aprovou junto com o ADR.

### 2.7 Segurança

Ao terminar, rode o agente `varal-seguranca` (somente leitura) sobre o diff de COR-10 e corrija o que for bloqueante.

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
3. **CU05 — PDF sem código:** quando a leitura do PDF terminar sem linha digitável nem Pix, a conferência (M02) deve oferecer "Colar código" (o mesmo campo da Nova conta) em vez de só mostrar erro. Arquivos em `components/bills/` (procure `instrumento`/`pdf`).
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
6. [ADR 0017](../../arquitetura/adr/0017-permissoes-por-categoria.md): status "aceita (data)" quando o dono aprovar.
7. Doc "Varal — Ajustes" (Claude Docs `ce521944-15d6-44a5-b70c-f0790e03de41`): leia ao vivo; se houver itens que esta etapa resolveu, só **acrescente** " — feito na etapa 12" no fim do item. Nunca apague nem reescreva.

## 7. Ações do dono (não são suas)

- Aprovar ou ajustar o ADR 0017 (Q12-1) e responder a Q12-2 (nome do usuário).
- Google Console: cadastrar `https://hmgvaral.codehub.systems/accounts/google/login/callback/` nas URIs de redirecionamento do cliente OAuth da HMG e testar o login Google na HMG (COR-12).

## 8. Pronto quando

- [ ] `docker compose -p varaltest ... pytest -q` verde.
- [ ] `npx vitest run`, `npx tsc --noEmit`, `npm run lint` verdes em `web/`.
- [ ] `make types` sem diff.
- [ ] `make e2e` verde nas duas larguras.
- [ ] Capturas da seção 5 salvas.
- [ ] Docs da seção 6 atualizados, commits locais feitos, **sem push**.
