# API e OpenAPI

> **Contém:** endpoints, sessão/CSRF e geração do contrato composto e dos tipos do frontend.
> **Origem:** RNF12, seção 9 de `docs/especificacao-varal.md` e implementação das Etapas 00, 02 e 03.

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
| `GET /api/grupos/{id}/` | `ver_grupo` (pagador 403) | `meu_papel`, `membros [{id, nome, email, papel, sou_eu}]`, `casas` não arquivadas. `email` é `null` para não admin quando o membro tem nome (RNF04) |
| `POST /api/grupos/{id}/sair/` | participante | 204; 409 |
| `POST /api/grupos/{id}/convites/` | `gerenciar_grupo` | `{papel}` → `{id, url, expira_em, papel}`; `url` com o token **só aqui** |
| `GET /api/grupos/{id}/convites/` | `gerenciar_grupo` | pendentes `[{id, papel, criado_em, expira_em, criado_por_nome}]` |
| `DELETE /api/grupos/{id}/convites/{cid}/` | `gerenciar_grupo` | 204 (revoga) |
| `PATCH` / `DELETE /api/grupos/{id}/membros/{mid}/` | `gerenciar_grupo` | `{papel}` / remove; 409. Admin que deixa de ser admin perde os convites pendentes que gerou |
| `POST /api/grupos/{id}/subgrupos/` | `gerenciar_grupo` | `{nome}` → 201 |
| `PATCH /api/grupos/{id}/subgrupos/{sid}/` | `gerenciar_grupo` | `{nome?, arquivado?}` |
| `GET /api/convites/{token}/` | público | `{grupo_nome, papel, expira_em}`; 410 igual para expirado, usado, revogado ou inexistente |
| `POST /api/convites/{token}/aceitar/` | autenticado; throttle `convite_aceite` 10/h por usuário | 201 `{grupo_id, papel}`; 410; 409 já membro; 429 |

O token de convite não aparece em log do Django nem do `next dev`; o access log de produção fica na P4.

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
