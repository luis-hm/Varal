# Stack e repositório

> **Contém:** tecnologias, versões em uso, estrutura do repositório, variáveis de ambiente e portas.
> **Origem:** `docs/especificacao-varal.md`, seção 9, decisões da Etapa 00 e implementação/locks da Etapa 02.

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
    └── web.yml       # web/**; api/** também dispara E2E integrado
```

- `make types` gera os tipos do front a partir do OpenAPI; o CI falha se o tipo gerado diferir do commitado.
- Sem Turborepo nem Nx: só o `web/` é JavaScript.

## Versões em uso (Etapa 02)

| Peça | Versão | Onde |
| --- | --- | --- |
| Python / uv | 3.12 / 0.13 | `api/pyproject.toml`, `api/uv.lock`, `api/Dockerfile` |
| Django / DRF / drf-spectacular | 6.1.3 / 3.18.3 / 0.30.0 | `api/uv.lock` |
| django-allauth / openapi-spec-validator | 65.22.0 / 0.9.0 | extras `headless-spec,socialaccount`; `api/uv.lock` |
| Celery / cliente Redis Python | 5.7.0 / 8.1.0 | `api/uv.lock` |
| PostgreSQL / Redis | 17 / 7 | `infra/docker-compose.yml` |
| Node / Next.js / React | 22 / 16.4.6 / 19.3.0 | `web/` |
| TanStack Query / openapi-typescript / Vitest | 5 / 7 / 4 | `web/package.json` |
| Playwright (`@playwright/test`, Chromium) | 1.65.0 | `web/package.json`, `web/playwright.config.ts`, `make e2e` |
| Lint | ruff (api), ESLint + `tsc` (web) | `make lint` |

Entram nas suas etapas: pdfplumber e `django-storages` com endpoint, bucket e chaves do `.env` (06), Web Push (09). Allauth headless já integrado na Etapa 02.

## Serviços e portas (dev)

| Serviço | Porta | Observação |
| --- | --- | --- |
| web | 3000 | `/api/*` é repassado à API (mesma origem: cookies de sessão first-party) |
| api | 8000 | `/api/health/`, `/api/me/`, `/api/auth/browser/v1/…`, `/api/schema/`, `/api/docs/`, `/admin/` e callback OAuth; roda `migrate` ao subir |
| worker / beat | — | `celery -A config worker` / `beat` |
| postgres / redis | internas | |
| minio | 9000 / 9001 | `pgsty/silo` com tag fixa, só local ([ADR 0002](adr/0002-armazenamento-s3-local.md)); profile `storage` até ser executado e verificado |

## Variáveis de ambiente

Todas em `infra/.env` (não versionado), criado a partir de `infra/.env.example` pelo `make dev`.
`DJANGO_DEBUG`, `DJANGO_SECRET_KEY` (obrigatória com debug desligado), `DJANGO_ALLOWED_HOSTS`, `POSTGRES_*`,
`REDIS_URL`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `SEED_PASSWORD`. No web: `API_INTERNAL_URL`.

Autenticação: `FRONTEND_URL=http://localhost:3000`, `API_PUBLIC_URL=http://localhost:8000`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` (vazios no exemplo). As duas credenciais são lidas em `SOCIALACCOUNT_PROVIDERS`, sem fonte no admin.

E-mail: `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL`. Localmente usa console: os e-mails aparecem nos logs do **worker**, pois são enviados por Celery após o commit. SMTP é configurável sem mudar código. Testes usam backend em memória e execução eager.

`REDIS_URL` atende ao broker e ao cache Django, com prefixo `varal-cache`; os limites de autenticação compartilham estado entre processos. Fora de DEBUG, cookies são Secure e a API força HTTPS. Antes do deploy, configurar a cadeia de proxies confiáveis: o limite por IP ainda vê o Next como origem; não confiar indiscriminadamente nos headers encaminhados enquanto a porta 8000 estiver exposta.

## Decisões de implementação

- Modelo de usuário próprio (`contas_usuario.Usuario`, UUID) desde a Etapa 00. Na Etapa 02: campos de domínio, login por e-mail e unicidade sem distinguir maiúsculas; username segue interno para compatibilidade do admin/seed.
- Allauth usa somente cliente browser, com sessão/CSRF, sem confirmação obrigatória de e-mail ou login automático após recuperação. Google com PKCE, sem armazenar tokens e sem vínculo automático por coincidência de e-mail.
- Layout protegido do Next consulta `/api/me/` no servidor, sem cache compartilhado; usa Suspense e `instant=false` porque a sessão real é necessária antes de apresentar o shell.
- `make types` exporta schema composto DRF + allauth por `export_schema`. `make e2e` sobe API/worker e dependências antes dos testes; o Next é iniciado pelo Playwright.
- DRF exige autenticação por padrão; rotas públicas (como o health) declaram `AllowAny`.
- `TIME_ZONE = America/Fortaleza` com `USE_TZ = True`: grava em UTC, exibe em Fortaleza (RNF11).
