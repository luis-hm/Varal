# Stack e repositório

> **Contém:** tecnologias, versões em uso, estrutura do repositório, variáveis de ambiente e portas.
> **Origem:** `docs/especificacao-varal.md`, seção 9, mais as decisões da Etapa 00.

## Da especificação

| Camada | Tecnologia |
| --- | --- |
| Backend | Django, Django REST Framework, drf-spectacular (OpenAPI), django-allauth headless |
| Tarefas | Celery, Celery beat, Redis |
| Banco | PostgreSQL |
| Leitura de boleto e Pix | Parser próprio da linha digitável (Febraban) e do BR Code (EMV); pdfplumber no MVP para PDF com texto; OCR na v2 |
| Front | Next.js (App Router), TanStack Query, openapi-typescript, PWA com Web Push |
| Arquivos | Armazenamento compatível com S3 (MinIO na VPS) |
| Deploy | Docker Compose: API, worker, beat, Postgres, Redis e Next |

### Repositório

```
varal/
├── api/              # Django + DRF + Celery
├── web/              # Next.js
│   └── src/types/api.ts   # gerado do OpenAPI
├── infra/            # docker-compose, nginx, .env.example
├── docs/             # este documento, ADRs
├── Makefile          # make dev, make types, make test
└── .github/workflows/
    ├── api.yml       # roda só se api/** mudar
    └── web.yml       # roda só se web/** mudar
```

- `make types` gera os tipos do front a partir do OpenAPI; o CI falha se o tipo gerado diferir do commitado.
- Sem Turborepo nem Nx: só o `web/` é JavaScript.

## Versões em uso (Etapa 00)

| Peça | Versão | Onde |
| --- | --- | --- |
| Python / uv | 3.12 / 0.13 | `api/pyproject.toml`, `api/uv.lock`, `api/Dockerfile` |
| Django / DRF / drf-spectacular | 6.1 / 3.18 / 0.30 | `api/` |
| Celery (+ Redis) | 5.7 | `api/config/celery.py` |
| PostgreSQL / Redis | 17 / 7 | `infra/docker-compose.yml` |
| Node / Next.js / React | 22 / 16.4 / 19.3 | `web/` |
| TanStack Query / openapi-typescript / Vitest | 5 / 7 / 4 | `web/package.json` |
| Playwright (`@playwright/test`, Chromium) | 1.65.0 | `web/package.json`, `web/playwright.config.ts`, `make e2e` |
| Lint | ruff (api), ESLint + `tsc` (web) | `make lint` |

Entram nas suas etapas: django-allauth headless (02), pdfplumber e `django-storages` com endpoint, bucket e chaves do `.env` (06), Web Push (09).

## Serviços e portas (dev)

| Serviço | Porta | Observação |
| --- | --- | --- |
| web | 3000 | `/api/*` é repassado à API (mesma origem: cookies de sessão first-party) |
| api | 8000 | `/api/health/`, `/api/schema/`, `/api/docs/` (Swagger), `/admin/`; roda `migrate` ao subir |
| worker / beat | — | `celery -A config worker` / `beat` |
| postgres / redis | internas | |
| minio | 9000 / 9001 | `pgsty/silo` com tag fixa, só local ([ADR 0002](adr/0002-armazenamento-s3-local.md)); profile `storage` até ser executado e verificado |

## Variáveis de ambiente

Todas em `infra/.env` (não versionado), criado a partir de `infra/.env.example` pelo `make dev`.
`DJANGO_DEBUG`, `DJANGO_SECRET_KEY` (obrigatória com debug desligado), `DJANGO_ALLOWED_HOSTS`, `POSTGRES_*`,
`REDIS_URL`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `SEED_PASSWORD`. No web: `API_INTERNAL_URL`.

## Decisões de implementação

- Modelo de usuário próprio (`contas_usuario.Usuario`, UUID, e-mail único) desde a Etapa 00, porque trocar `AUTH_USER_MODEL` depois exige refazer migrações. Os campos de domínio entram na Etapa 02.
- DRF exige autenticação por padrão; rotas públicas (como o health) declaram `AllowAny`.
- `TIME_ZONE = America/Fortaleza` com `USE_TZ = True`: grava em UTC, exibe em Fortaleza (RNF11).
