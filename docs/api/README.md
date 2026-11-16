# API e OpenAPI

> **Contém:** endpoints, sessão/CSRF e geração do contrato composto e dos tipos do frontend.
> **Origem:** RNF12, seção 9 de `docs/especificacao-varal.md` e implementação das Etapas 00 e 02–05.

## Fluxo

1. Endpoints próprios usam drf-spectacular (`@extend_schema`); autenticação usa o schema nativo do allauth.
2. `make types` executa `manage.py export_schema --file openapi.yaml`: `CombinedSchemaGenerator` combina ambos, preserva os caminhos e prefixa componentes/referências da biblioteca com `Allauth`. Divergência de versão OpenAPI, colisões e schema inválido fazem a geração falhar.
3. openapi-typescript gera `web/src/types/api.ts` a partir desse contrato único. A exportação é ordenada e tem teste de determinismo.
4. Os dois arquivos são **versionados** e entram no mesmo commit da mudança na API; o job `types` do CI usa o mesmo exportador e falha se houver diff.

O front só usa tipos de `@/types/api` (ex.: `components["schemas"]["Health"]`); nada de tipo da API escrito à mão.

## Onde ver

| URL (dev) | O quê |
| --- | --- |
| http://localhost:8000/api/schema/ | Schema OpenAPI (YAML; JSON com `Accept: application/json`) |
| http://localhost:8000/api/docs/ | Swagger UI |
| http://localhost:3000/api/… | Mesma API, via proxy do Next (é o caminho que o front usa) |

## Convenções

- Rotas próprias sob `/api/`, terminando em `/`. **Exceção:** endpoints nativos allauth em `/api/auth/browser/v1/` preservam os sufixos sem barra final; o proxy Next mantém método, body e cookies, sem redirecionar o POST.
- Autenticação exigida por padrão, **só por sessão** (`SessionAuthentication`; sem HTTP Basic desde a Etapa 03); rota pública declara `AllowAny`.
- Dinheiro em centavos (`int`), ids UUID, datas ISO 8601 em UTC.

## Endpoints

| Método e rota | Etapa | Descrição |
| --- | --- | --- |
| `GET /api/health/` | 00 | `{"status": "ok"}` se a API alcança o banco |
| `GET /api/me/` | 02 | `id`, `nome`, `email`, `espaco_pessoal: {id, tipo, nome}` do solicitante; `Cache-Control: private, no-store` |
| `GET /api/me/` | 03 | acrescenta `grupos: [{id, nome, papel}]` |

## Grupos e convites (Etapa 03)

Toda rota de grupo passa por `api/apps/espacos/acesso.py`: **404** se não participa (sem revelar existência), **403** se o papel não tem a ação. Ids aninhados (membro, casa, convite) são buscados dentro do grupo da URL. **409** quando a RN04 barra (último admin).

| Método e rota | Permissão | Entrada / resultado |
| --- | --- | --- |
| `GET /api/grupos/` | autenticado | `id, nome, papel, membros_qtd, casas_qtd` (contagens `null` para pagador) |
| `POST /api/grupos/` | autenticado | `{nome, casas?}` → 201; criador único admin |
| `GET /api/grupos/{id}/` | `ver_grupo` (pagador 403) | `meu_papel`, `janela_alerta_dias` (04), `membros [{id, usuario, nome, email, papel, sou_eu}]`, `casas` não arquivadas. `usuario` (id do usuário, Etapa 04) alimenta "Quem paga" e "Quem vê". `email` é `null` para não admin quando o membro tem nome (RNF04) |
| `PATCH /api/grupos/{id}/` | `gerenciar_grupo` | Etapa 04: `{janela_alerta_dias}` 1–7 (RN13) → grupo; fora do intervalo 400 |
| `POST /api/grupos/{id}/sair/` | participante | 204; 409 (RN04 ou RN32). Etapa 04: ver [saída e RN32](#saída-e-rn32-etapa-04) |
| `POST /api/grupos/{id}/convites/` | `gerenciar_grupo` | `{papel}` → `{id, url, expira_em, papel}`; `url` com o token **só aqui** |
| `GET /api/grupos/{id}/convites/` | `gerenciar_grupo` | pendentes `[{id, papel, criado_em, expira_em, criado_por_nome}]` |
| `DELETE /api/grupos/{id}/convites/{cid}/` | `gerenciar_grupo` | 204 (revoga) |
| `PATCH` / `DELETE /api/grupos/{id}/membros/{mid}/` | `gerenciar_grupo` | `{papel}` / remove; 409. Admin que deixa de ser admin perde os convites pendentes que gerou |
| `POST /api/grupos/{id}/subgrupos/` | `gerenciar_grupo` | `{nome}` → 201 |
| `PATCH /api/grupos/{id}/subgrupos/{sid}/` | `gerenciar_grupo` | `{nome?, arquivado?}` |
| `GET /api/convites/{token}/` | público | `{grupo_nome, papel, expira_em}`; 410 igual para expirado, usado, revogado ou inexistente |
| `POST /api/convites/{token}/aceitar/` | autenticado; throttle `convite_aceite` 10/h por usuário | 201 `{grupo_id, papel}`; 410; 409 já membro; 429 |

O token de convite não aparece em log do Django nem do `next dev`; o access log de produção fica na P4.

## Contas (Etapa 04)

Toda consulta passa pelo filtro central de `acesso.py`: `lancamentos_visiveis` dentro de um espaço e `lancamentos_do_usuario` no detalhe e no admin. Ambos usam as mesmas regras de papel e visibilidade. **404** para conta que o usuário não vê (inexistente, de outro espaço ou restrita sem acesso; nunca 403); **403** só se ele vê e o papel não tem `editar_conta`/`criar_conta` (RN05). Inexistente e invisível percorrem o mesmo caminho estrutural de consultas, sem garantia de tempo constante. Totais, contagens, `atencao`, `por_casa` e `opcoes` saem só do visível. Totais, `atencao` e `por_casa` nunca somam canceladas (D2); elas só entram em `contagens.canceladas` e em `status=canceladas`.

**Prazo e selo ([ADR 0009](../arquitetura/adr/0009-filtro-temporal-contas-abertas.md)):** `status=vencidas` e `contagens.vencidas` incluem abertas `pendente` ou `aguardando` com vencimento anterior a hoje em Fortaleza, dentro do mês/filtros da lista. O resumo usa esse mesmo critério temporal em `atencao`, que pode reunir vários meses. Aguardando mantém `status_exibido=aguardando`; só pendente recebe o selo calculado `vence`/`vencida`. A data é resolvida a cada requisição, inclusive após a virada do dia.

| Método e rota | Permissão | Entrada / resultado |
| --- | --- | --- |
| `GET /api/espacos/{id}/lancamentos/` | participante | `?mes=AAAA-MM` (padrão: mês atual em Fortaleza) `&status=todas\|a_pagar\|vencidas\|pagas\|canceladas` `&subgrupo=<id>` `&pagador=<id>\|nenhum` → `{mes, total_centavos, contagens: {todas, a_pagar, vencidas, pagas, canceladas}, opcoes: {casas, pagadores, sem_pagador}, itens: [Conta]}`. `opcoes` alimenta os chips "Casa" e "Quem paga" com o visível do mês |
| `POST /api/espacos/{id}/lancamentos/` | `criar_conta` | `{descricao, valor_centavos, vencimento, subgrupo?, pagador?, visibilidade?, acesso?: [usuario_id] (≤ 50)}` → 201 `ContaDetalhe`; nasce `pendente`; sem categoria |
| `GET /api/espacos/{id}/resumo/` | participante | `{mes, janela_alerta_dias, total_centavos, qtd, vencidas_qtd, vence_qtd, atencao: [Conta], por_casa: [{id, nome, total_centavos, qtd}]}`. `atencao` = vencidas de qualquer mês + vence na janela; `por_casa` vazio no pessoal; sem `pagas_qtd` até a 07 |
| `GET /api/lancamentos/{id}/` | quem vê | `ContaDetalhe` |
| `PATCH /api/lancamentos/{id}/` | `editar_conta` | campos do POST, opcionais (espaço não muda) → `ContaDetalhe`; 400 (inclui a Q19b: ninguém mais veria), 409 cancelada |
| `POST /api/lancamentos/{id}/cancelar/` | `editar_conta` | → `ContaDetalhe`; 409 se não `aguardando`/`pendente` |

- **Conta:** `id, espaco {id, nome, tipo}, descricao, valor_centavos, vencimento, status, status_exibido (+ vence, vencida), dias_para_vencer, subgrupo {id, nome}|null, pagador {id, nome, sou_eu}|null, visibilidade, criado_em`.
- **ContaDetalhe:** Conta + `criador {nome, sou_eu}`, `acesso [{id, nome}]` (seleção editável), **`quem_ve [{id, nome}]`** (somente leitura: audiência efetiva da restrita pelo filtro RN06/RN07, considerando criador, pagador, escolhidos e papéis atuais, sem duplicatas; vazio nas demais contas), `historico [{acao, automatica, autor, sou_eu, dados, criado_em}]`, `pode_editar`.
- **Nomes:** em `pagador`, `criador`, `acesso`, `quem_ve` e `opcoes`, membro atual aparece pelo nome ou, se vazio, pelo e-mail; quem saiu ou excluiu a conta aparece como "Ex-membro", nunca pelo e-mail. Vale também para o pagador que já pode ver a conta, sem criar uma listagem geral de membros para ele. No `historico`, `autor` e as pessoas de `dados` vêm resolvidos dos ids gravados: nome, "Pessoa sem nome" ou "Ex-membro", **nunca e-mail**; ação automática tem `autor: null`. Ações em [modelo](../dados/modelo.md#implementação-da-etapa-04).

**Concorrência:** criar revalida vínculo e permissão sob travas compatíveis com saída, remoção, troca de papel e exclusão de usuário. Essas operações travam todas as contas abertas do grupo, inclusive as ainda públicas, antes de avaliar a RN32; uma conversão concorrente para restrita não pode deixá-la órfã. O detalhe trava a conta, consulta a autorização em novo comando e mantém a trava até carregar relações e serializar. POST/PATCH/cancelar mantêm a própria transação até construir a resposta; a exceção de responder a quem acabou de retirar seu próprio acesso reconhece somente a própria operação, sem reler edição posterior de outra pessoa.

### Saída e RN32 (Etapa 04)

`POST /api/grupos/{id}/sair/` aceita corpo opcional `{resolucoes: [...]}` (no máximo 50; ADR 0007), cada item `{lancamento, acao: "acesso", usuarios: [id] (≤ 50)}` ou `{lancamento, acao: "cancelar"}`.

- **409 `conta_restrita_orfa`:** a saída deixaria restrita aberta sem ninguém que a veja. Corpo `{detail, code, contas: [{id, descricao}], pessoas: [{id, nome}]}`; `pessoas` contém somente candidatos atuais elegíveis (admin, membro, observador), excluindo quem sai. `nome` segue a regra de nome/e-mail de membro atual, inclusive para saída do pagador; não é acesso permanente à lista do grupo. Nada muda, nem as resoluções enviadas.
- **400:** resolução de conta que não bloqueia a saída, ou `usuarios` fora de admin/membro/observador do grupo.
- Resoluções e saída na mesma transação; histórico com `motivo: "saida_rn32"`. Nenhum outro endpoint aceita `resolucoes`.
- `DELETE` e `PATCH /api/grupos/{id}/membros/{mid}/`: contrato e respostas **sem mudança**. A remoção cancela as órfãs (`cancelada_automaticamente`) e a troca para pagador preserva o acesso (`acesso_preservado`) sem sinal nenhum ao admin.

**Admin do Django:** lançamentos e históricos continuam somente leitura e obedecem ao filtro central, inclusive para superusuário. A confirmação de exclusão de usuário omite a árvore/contagens de contas e históricos; o bloqueio RN32 usa mensagem genérica. Isso limita a aplicação administrativa, não o acesso direto do operador da infraestrutura ao banco.

## Boleto e Pix (Etapa 05)

| Método e rota | Permissão | Entrada / resultado |
| --- | --- | --- |
| `POST /api/boletos/ler/` | sessão autenticada e CSRF; nenhum acesso a contas | Exatamente um de `{codigo: string}` (até 4096 caracteres) ou `{chave_pix: string}` (até 77). Retorna `{instrumento: {tipo, codigo, chave_pix, beneficiario}, valor_centavos: int\|null, vencimento: date\|null, vencimentos_possiveis: date[], avisos: string[]}`. Preview sem gravação; inválido → 400; sem sessão/CSRF → 403 |
| `POST /api/espacos/{id}/lancamentos/` | `criar_conta`, com as guardas da 04 | Além dos campos já obrigatórios da conta, aceita `instrumento: {codigo}` ou `{chave_pix}`, opcional/nulo. Revalida no backend e grava conta/instrumento/histórico atomicamente; ausente ou nulo = manual |
| `PATCH /api/lancamentos/{id}/` | `editar_conta` | `instrumento` omitido preserva a relação; `{codigo}`/`{chave_pix}` troca e `null` remove explicitamente para manual. Mesmo omitido, instrumento persistido é revalidado contra valor/data finais. Conflito → 400 sem gravação parcial; troca/remoção em paga ou confirmada → 409 |
| `GET /api/lancamentos/{id}/` e respostas de mutação | acesso autorizado à conta | `ContaDetalhe` acrescenta `instrumento: {tipo, codigo, chave_pix, beneficiario}\|null`. Tipo é `boleto_bancario\|boleto_arrecadacao\|pix`. Manual não tem relação e retorna `null` |

O tipo é inferido pela leitura, não confiado à entrada. Não há rota de instrumento por id nem acesso próprio no Django admin; o acesso vem exclusivamente da conta e mantém as guardas de concorrência da 04. Código/chave não são enviados em listas/resumos nem registrados no histórico; a alteração registra apenas tipos antes/depois e `codigo_alterado: true`. Reenvio idêntico não duplica histórico. Conta aguardando com instrumento válido e dados completos passa a pendente na mesma transação; esta etapa não cria aguardando avulsa nem aceita PATCH livre de status.

**Vencimento bancário (Q05-4):** fator 0000 não sugere data; 0001–0999 usa a base legada; 1000–9999 sugere o ciclo reiniciado em 22/02/2025 e também retorna a alternativa legada em `vencimentos_possiveis`. O usuário escolhe explicitamente uma data codificada; ao adicionar/trocar instrumento ambíguo, omitir a data dá 400. Não há escolha por proximidade com o relógio. Arrecadação/Pix/fator zero requerem data informada pelo usuário. Valor aplicável no código prevalece e conflito explícito é rejeitado; zero monetário do boleto significa ausência a preencher, não conta de valor zero. Avisos legíveis usam dd/mm/aaaa, enquanto campos de data do DTO mantêm ISO 8601.

**Pix:** valida TLV/CRC por bytes UTF-8, preserva BR Code completo e não consulta URL dinâmica, DICT ou titularidade. Em QR estático, ID54 ausente pede valor; presente com zero é inválido. No dinâmico, ID54 e txid são ignorados e o valor é informado pelo usuário. Chave avulsa normaliza apresentação; a chave já embutida deve ser canônica para não reescrever o payload. Beneficiário extraído é dado declarado no código, não identidade verificada. [Fontes e limites](../etapas/05-boleto-pix/fontes.md).

**Fronteira textual:** serializers HTTP rejeitam NUL antes da leitura/gravação. A biblioteca pura tem limite conhecido de NUL em campos textuais com CRC recalculado; a Etapa 06 deve validar NUL e Unicode inválido também no worker, que extrai dados fora do DRF. Não registrar o texto integral do PDF ou códigos em erros/logs.

## Autenticação (Etapa 02)

Base **`/api/auth/browser/v1/`**, acessada pela origem web `http://localhost:3000`:

| Método e sufixo | Entrada / resultado |
| --- | --- |
| `GET config` | Configuração pública/provedores disponíveis; inicializa cookie CSRF |
| `POST auth/signup` | JSON `email`, `password`; cria usuário, espaço pessoal e sessão |
| `POST auth/login` | JSON `email`, `password`; cria sessão e rotaciona CSRF |
| `GET auth/session` | Sessão autenticada (200) ou anônima (401) |
| `DELETE auth/session` | Invalida sessão; 401 com `meta.is_authenticated=false` confirma saída |
| `POST auth/password/request` | JSON `email`; resposta genérica, envio assíncrono quando há conta |
| `GET auth/password/reset` | Valida o header `X-Password-Reset-Key` |
| `POST auth/password/reset` | JSON `key`, `password`; troca senha e retorna 401 sem login automático |
| `POST auth/provider/redirect` | Formulário síncrono com `provider=google`, `process=login`, `callback_url` e `csrfmiddlewaretoken` |

Mutações browser exigem CSRF válido (`X-CSRFToken` no JSON). Ler o cookie atual a cada chamada, pois ele muda no login. Sessão usa cookie HttpOnly/SameSite=Lax; Secure e redirecionamento HTTPS com DEBUG desligado. Sem token no localStorage/sessionStorage. Consultas autenticadas no servidor Next encaminham cookies e não usam cache compartilhado.

Google: o `redirect_uri` OAuth continua **`http://localhost:8000/accounts/google/login/callback/`** (`API_PUBLIC_URL`); a origem autorizada é **`http://localhost:3000`**. Depois do handshake, `callback_url` volta a `/entrar/retorno` no frontend, que consulta a sessão. Credenciais vêm exclusivamente do ambiente da API; `SocialApp` não é administrável nem fonte alternativa de credenciais. Cancelamento ou URL de retorno inválida volta à interface sem autenticar.
