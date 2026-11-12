# API e OpenAPI

> **Contém:** como o contrato da API é gerado, versionado e transformado em tipos do front.
> **Origem:** RNF12 e seção 9 de `docs/especificacao-varal.md`; implementado na Etapa 00.

## Fluxo

1. Cada endpoint é documentado com drf-spectacular (`@extend_schema`, com `OpenApiExample`).
2. `make types` gera `api/openapi.yaml` (`manage.py spectacular --validate`) e, dele, `web/src/types/api.ts` (openapi-typescript).
3. Os dois arquivos são **versionados** e entram no mesmo commit da mudança na API.
4. O CI (`.github/workflows/api.yml`, job `types`) regenera os dois e falha se houver diff.

O front só usa tipos de `@/types/api` (ex.: `components["schemas"]["Health"]`); nada de tipo da API escrito à mão.

## Onde ver

| URL (dev) | O quê |
| --- | --- |
| http://localhost:8000/api/schema/ | Schema OpenAPI (YAML; JSON com `Accept: application/json`) |
| http://localhost:8000/api/docs/ | Swagger UI |
| http://localhost:3000/api/… | Mesma API, via proxy do Next (é o caminho que o front usa) |

## Convenções

- Rotas sob `/api/`, terminando em `/`.
- Autenticação exigida por padrão; rota pública declara `AllowAny`.
- Dinheiro em centavos (`int`), ids UUID, datas ISO 8601 em UTC.

## Endpoints

| Método e rota | Etapa | Descrição |
| --- | --- | --- |
| `GET /api/health/` | 00 | `{"status": "ok"}` se a API alcança o banco |
