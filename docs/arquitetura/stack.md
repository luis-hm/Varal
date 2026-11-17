# Stack e repositório

> **Contém:** tecnologias, versões em uso, estrutura do repositório, variáveis de ambiente e portas.
> **Origem:** `docs/especificacao-varal.md`, seção 9, decisões da Etapa 00, implementação/locks 02–11 e ADR0015; extensões operacionais locais ainda em validação.

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
    ├── api.yml       # api, tipos, infra e Makefile
    └── web.yml       # web, api, infra e Makefile; E2E integrado
```

- `make types` gera os tipos do front a partir do OpenAPI; o CI falha se o tipo gerado diferir do commitado.
- Sem Turborepo nem Nx: só o `web/` é JavaScript.

## Versões em uso

| Peça | Versão | Onde |
| --- | --- | --- |
| Python / uv | 3.12 / 0.13 | `api/pyproject.toml`, `api/uv.lock`, `api/Dockerfile` |
| Django / DRF / drf-spectacular | 6.1.3 / 3.18.3 / 0.30.0 | `api/uv.lock` |
| django-allauth / openapi-spec-validator | 65.22.0 / 0.9.0 | extras `headless-spec,socialaccount`; `api/uv.lock` |
| Celery / cliente Redis Python | 5.7.0 / 8.1.0 | `api/uv.lock` |
| PostgreSQL / Redis | 17 / 7 | `infra/docker-compose.yml` |
| Node / Next.js / React | 22.23.5 / 16.4.6 / 19.3.0 | `web/.nvmrc` (lido pelo CI e pelo `nvm use`), `engines` em `web/package.json`; `make test-web`/`lint`/`types`/`e2e` param com Node < 22 |
| TanStack Query / openapi-typescript / Vitest | 5 / 7 / 4 | `web/package.json` |
| Playwright (`@playwright/test`, Chromium) | 1.65.0 | `web/package.json`, `web/playwright.config.ts`, `make e2e` |
| Lint | ruff (api), ESLint + `tsc` (web) | `make lint` |

PDF textual usa pdfplumber e `django-storages`/S3; Web Push integrado na 09 com `pywebpush==2.3.0`; a etapa 11 acrescenta witness WAL e novas provas locais. Allauth headless já integrado na Etapa 02.

## Serviços e portas (dev)

| Serviço | Porta | Observação |
| --- | --- | --- |
| web | 3000 | `/api/*` é repassado à API (mesma origem: cookies de sessão first-party) |
| api | 8000 | `/api/health/`, `/api/me/`, `/api/auth/browser/v1/…`, `/api/schema/`, `/api/docs/`, `/admin/` e callback OAuth; roda `migrate` ao subir |
| worker / beat | — | `celery -A config worker` / `beat` |
| postgres / redis | internas | |
| minio | 9000 / 9001 | `pgsty/silo` com tag fixa, só local ([ADR 0002](adr/0002-armazenamento-s3-local.md)); iniciado por `make dev` e pronto antes de preparar bucket privado |

## Variáveis de ambiente

Todas em `infra/.env` (não versionado), criado a partir de `infra/.env.example` pelo `make dev`.
`DJANGO_DEBUG`, `DJANGO_SECRET_KEY` (obrigatória com debug desligado), `DJANGO_ALLOWED_HOSTS`, `POSTGRES_*`,
`REDIS_URL`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `SEED_PASSWORD`. No web: `API_INTERNAL_URL`.

PDF/S3: `S3_ENDPOINT_URL` (interno, `http://minio:9000` no Compose), `S3_PUBLIC_ENDPOINT_URL` (navegador, `http://localhost:9000`), `S3_BUCKET_NAME`, `S3_REGION_NAME`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` e `PDF_SPOOL_DIR`. Em desenvolvimento, credenciais AWS vazias usam `MINIO_ROOT_*`; fora de DEBUG use credenciais próprias. `storage-init` prepara o bucket privado idempotentemente após o healthcheck. API e worker compartilham o volume `pdfspool` em `/varal/staging`, não servido por HTTP; o arquivo é enviado ao S3 e analisado no worker. Links são assinados para o endpoint público, com validade de 60 segundos, sem reescrever o host. Estes valores são apenas de desenvolvimento, não uma configuração de produção.

Silo remoto pelo Coolify, autorizado separadamente pelo dono: [operação e Compose](silo-coolify.md). O inventário remoto usa `SILO_PROD_ENDPOINT_URL`, `SILO_PROD_BUCKET_NAME`, `SILO_PROD_REGION_NAME`, `SILO_PROD_ACCESS_KEY_ID` e `SILO_PROD_SECRET_ACCESS_KEY` no `infra/.env` não versionado. Esses nomes não são consumidos pelo Django e não trocam o destino local; serão mapeados explicitamente para `S3_*`/`AWS_*` no deploy futuro. Administração do Silo permanece nas variáveis `SILO_ADMIN_USER`, `SILO_ADMIN_PASSWORD` e `SILO_CONSOLE_URL` do recurso Coolify, separada da chave restrita de runtime. O comando atual `preparar_storage` requer permissões administrativas de criação/ACL; não o executar com a chave restrita sem adequar o bootstrap. A aplicação Varal ainda não foi implantada por essa configuração.

Autenticação: `FRONTEND_URL=http://localhost:3000`, `API_PUBLIC_URL=http://localhost:8000`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` (vazios no exemplo). As duas credenciais são lidas em `SOCIALACCOUNT_PROVIDERS`, sem fonte no admin.

E-mail: `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL`. Localmente usa console: os e-mails aparecem nos logs do **worker**, pois são enviados por Celery após o commit. SMTP é configurável sem mudar código. Testes usam backend em memória e execução eager.

`REDIS_URL` atende ao broker e ao cache Django, com prefixo `varal-cache`; os limites de autenticação compartilham estado entre processos. Fora de DEBUG, cookies são Secure e a API força HTTPS. Antes do deploy, configurar a cadeia de proxies confiáveis: o limite por IP ainda vê o Next como origem; não confiar indiscriminadamente nos headers encaminhados enquanto a porta 8000 estiver exposta.

Só E2E/CI: `ACCOUNT_RATE_LIMIT_SIGNUP` sobrescreve o limite de cadastro do allauth (`ACCOUNT_RATE_LIMITS["signup"]`; o allauth mescla o dicionário aos padrões, então login, `login_failed`, `reset_password` etc. seguem os dele). `make e2e` passa `1000/m/ip` ao serviço `api` e o job `e2e` do `web.yml` define o mesmo valor, porque a suíte cria ~40 contas do mesmo IP. Fora disso fica vazia e vale o padrão (20/m/ip). Não vai no `infra/.env.example` (P5).

## Decisões de implementação

- Modelo de usuário próprio (`contas_usuario.Usuario`, UUID) desde a Etapa 00. Na Etapa 02: campos de domínio, login por e-mail e unicidade sem distinguir maiúsculas; username segue interno para compatibilidade do admin/seed.
- Allauth usa somente cliente browser, com sessão/CSRF, sem confirmação obrigatória de e-mail ou login automático após recuperação. Google com PKCE, sem armazenar tokens e sem vínculo automático por coincidência de e-mail.
- Layout protegido do Next consulta `/api/me/` no servidor, sem cache compartilhado; usa Suspense e `instant=false` porque a sessão real é necessária antes de apresentar o shell.
- `make types` exporta schema composto DRF + allauth por `export_schema`. `make e2e` sobe API/worker e dependências antes dos testes; o Next é iniciado pelo Playwright.
- CI: `api.yml` e `web.yml` disparam por `push`/`pull_request` com filtro de caminhos, ou à mão com `gh workflow run <arquivo> --ref <branch>` (`workflow_dispatch`, só depois que o arquivo estiver na `main`).
- `make limpar-dev` (`limpar_dev`, só com DEBUG) mostra e, após confirmação (`SIM=1` pula), apaga do banco de dev o grupo `x`, os grupos `Teste UI …`, os usuários `burst-*`/`e2e-*@varal.test` e os grupos que ficam sem membros; nunca o `dev`.
- DRF exige autenticação por padrão; rotas públicas (como o health) declaram `AllowAny`.
- `TIME_ZONE = America/Fortaleza` com `USE_TZ = True`: grava em UTC, exibe em Fortaleza (RNF11).

## Notificações — configuração e operação da Etapa 09

`EMAIL_TIMEOUT=10` limita SMTP. Console permanece padrão local; profile opt-in `smtp-test` sobe capturador sem porta pública/relay, aceita só `.invalid`, com filesystem read-only e tmpfs privado/arquivo 0600. Não usar o receptor como SMTP público. Prova integrada isolada validou SMTP/worker reais, sem comprovar SMTP TLS/autenticação externa ou entrega física.

| Variável | Uso/padrão seguro |
| --- | --- |
| `WEBPUSH_ENABLED` | `0`, ativação explícita |
| `WEBPUSH_PUBLIC_KEY` | Chave pública exposta pela configuração autenticada |
| `WEBPUSH_PRIVATE_KEY` | VAPID privada somente no worker via Compose |
| `WEBPUSH_SUBJECT` | Subject VAPID do emissor |
| `WEBPUSH_ALLOWED_HOSTS` | Hosts exatos homologados FCM/Mozilla/Apple; sem wildcard do cliente |
| `WEBPUSH_TIMEOUT_SECONDS` | `10` |
| `NOTIFICACOES_STORAGE_KEY` | Fernet compartilhada somente API/worker; produção exige chave própria |

Em DEBUG, chave local Fernet pode derivar de SECRET_KEY se ausente; isso não é configuração de produção. Serviços com env_file que não precisam dos segredos recebem valores explicitamente vazios no Compose. O operador ainda pode ler o arquivo e `docker compose config` pode imprimir segredos; a verificação usou ambiente temporário com marcadores, emitindo somente booleanos.

Beat diário às 07:00 America/Fortaleza aponta para `apps.notificacoes.tasks.rotina_diaria`: geração/recuperação 08 síncrona antes de avisos 09; recuperação da rotina a cada 300 s com lease/checkpoints, dispatcher a cada 60 s. Manutenção de comprovantes continua 300 s separada. Tasks de entrega têm limites de execução; retries só com falha recuperável comprovada, até três tentativas totais. Estado incerto não é reenfileirado automaticamente.

Transporte Web Push fixa conexão no IP público validado mantendo TLS/SNI/Host originais, sem redirects, proxy herdado ou segunda resolução livre; URL/chaves cifradas e fingerprint HMAC não são logadas. Prova real em rede Docker interna, DB/broker descartáveis e TLS/CA/keys efêmeras validou criptografia, VAPID, pin e falhas selecionadas; resolvedor/CA/porta foram injetados apenas na prova. Não houve provedor público, recepção em navegador real ou espera até 07:00: relógio e intervalo acelerados foram avaliados separadamente. Recursos temporários removidos e volumes/banco normais preservados. Detalhes e pendências no [relatório 09](../etapas/09-notificacoes/relatorio.md).

## Coordenação e arquivos — Etapa 10 concluída

Backend usa barreiraPostgreSQL transacional global curta em namespace de duas chaves separado dos mutexes operacionais; entrada antes do primeiro lock de domínio em mutações/leituras relacionadas, inclusive09 e exclusão antesCollector. NenhumS3/SMTP/push dentro da barreira; mutex operacional de objeto pode cobrir I/O em fase isolada sem locks de domínio. Contenção global é custo aceitoT10-A, desempenho ainda não medido.

ReservaPDF fixa pin independente antes202 com try-lock; worker lê fonte imutável fora do mutex e publica destinoUUID exclusivo apenas apósSHA/tamanho do objeto real. Cleanup dePDF **e comprovante07** usa geração/CAS sem rowlock de intenção duranteS3. Tombstones dePUT incerto permanecem para reconciliação, inclusive escrita tardia; custo de varredura precisa acompanhamento, sem assumir ausência remota por prazo/lease. `total_max_attempts=1` desabilita retry SDK oculto nos clientes de cópia/PDF/comprovantes; novas tentativas de cópia usam capacidade/destino novos.

Prova real isolada Silo/Postgres/Redis/Celery validou retenção apósCASCADE, cópia porfila, bytes/SHA/tamanho, privacidade anônima e cleanup; recursos próprios removidos. Não provaPUT físico tardio, produção, entrega externa ouLGPD11. Recuperação durável de solicitações revarre preparações; task tem limite120s, lease3min e até3tentativas de cópia, sem confundir esse orçamento com retries de avisos09. Estado atual/evidências no [relatório 10](../etapas/10-solicitacao-modo-simples/relatorio.md). P3/P4 e armazenamento/HTTPS de produção continuam11; P11/destino pendente, sem deploy autorizado.

## Extensões operacionais da Etapa 11

Seção derivada da implementação e [ADR0015](adr/0015-exportacao-exclusao-e-prova-local.md), sem reescrever a origem. API produtiva usa **Gunicorn 27.0.1**, fixado em `api/pyproject.toml` e `api/uv.lock`; Next usa build produtivo no laboratório. Node local verificado: **22.23.5**. `make test` recusa Node <22 antes de iniciar Docker; Vitest usa **um worker** para execução serial reproduzível. Isso não transforma falha de teste em sucesso: a integral 03 aprovou API 546/546 em 736 s e falhou na web (148/149, um timeout); foco posterior ARIA 14/14 e lint completo/seletores QA passaram, sem nova aprovação integral neste corte. Tipos duas vezes determinísticos pertencem à rodada 01. Resultados finais ficam no relatório da etapa, não em versão de ferramenta.

### Configuração sensível e fronteiras

| Configuração implementada | Uso |
| --- | --- |
| `JOURNAL_URL`, `JOURNAL_EPOCH` | Writer privado e época esperada; URL sem segredo/query |
| `JOURNAL_CLIENT_KEY_ID`, `JOURNAL_CLIENT_KEY_FILE`; `JOURNAL_RECEIPT_KEY_ID`, `JOURNAL_RECEIPT_KEY_FILE` | Autenticação do cliente e validação de recibos; arquivos privados separados |
| `JOURNAL_RESTORE_KEY_ID/FILE`, `JOURNAL_CHAIN_KEY_ID/FILE`, `JOURNAL_CHECKPOINT_KEY_ID/FILE` | Leitura/verificação de restore, cadeia e checkpoint; cada função com sua chave/ID, nunca chaves no documento/imagem |
| `VARAL_WAL_WITNESS_DIR`, `VARAL_WAL_WITNESS_KEY_FILE`, `VARAL_WAL_WITNESS_EPOCH`, `VARAL_WAL_WITNESS_TIMEOUT` | ACK autenticado de WAL durável antes do transporte; timeout limitado a no máximo 20 s |
| `VARAL_RESTORE_MODE=1` | Manutenção isolada: bloqueia views e transporte/dispatch; comando de reconciliação não abre produto |
| `VARAL_TRUSTED_PROXY_COUNT`, `VARAL_TRUSTED_PROXY_CIDRS` | Topologia implementada aceita 0 ou 1 salto; salto 1 exige CIDRs explícitos. Não copiar configuração local para VPS/CDN desconhecida |
| `ACCOUNT_REAUTHENTICATION_METHODS`, `ACCOUNT_REAUTHENTICATION_TIMEOUT` | Configuração do código: password/code e 300 s; guarda nativa usa comparação estrita |

Runtime PostgreSQL não é role de manutenção/proprietária: migração/restore e permissões elevadas usam ambiente separado. Role runtime não pode alterar R diretamente, desabilitar trigger ou administrar schema; trigger SECURITY DEFINER tem search_path fixo. Credencial S3 restrita ao bucket deve ser distinguida dos smokes anteriores com root sintético. Um fixture com root não prova menor privilégio do runtime. Arquivador WAL cifra segmentos e publica ACK só após persistência; cadeia/checkpoint/recibos e atestado têm domínios MAC separados. HMAC não cifra rede, não autentica usuário browser e não prova frescor contra root que recue tudo.

### E2E e manutenção

`infra/docker-compose.e2e.yml` fornece Redis exclusivo sem portas/persistência, rootfs read-only/tmpfs; API e worker da suíte usam esse Redis. `make e2e`/CI passam `E2E_RN31_ISOLATED=1`, ID do container, projeto `varal`, serviço `redis-e2e` e `--workers=1`. Hook `web/e2e/rn31-isolation.ts` valida labels/mounts/portas/ID antes de remover **somente** `varal:rn31::ip:*` por SCAN/UNLINK. Preserva contadores de usuário/outras chaves; sem FLUSHDB, sem Redis dev. Não aplicar hook ao laboratório produtivo ou usar o resultado como prova do limite entre casos.

Comandos/alvos reais: `make lab11-init`, `lab11-up`, `lab11-down`, `lab11-backup`, `lab11-journal-test`, `lab11-journal-container`, `lab11-proxy-smoke`, `lab11-smtp-smoke`, `lab11-wal-test`, `lab11-wal-smoke`, `lab11-backend-witness-smoke`, `lab11-auth-smoke`, `lab11-s3-smoke`, `lab11-log-sentinels`, `lab11-storage-policy-smoke`. Alvos que recebem laboratório exigem `LAB_DIR` próprio validado; backup exige caminho privado de chave. Não executar contra volumes existentes por adaptação manual. O [runbook](operacao-local.md) descreve ACTIVE_RESTORE, seleção do primário e gates pendentes.

A etapa 11 ainda não tem aceite final. CA08 teve prova real de aceite10→DELETE204→worker/S3/hash/ACL via DjangoClient em processo (sem proxy); CA17 teve SMTP STARTTLS/uma captura aceita e WebPush TLS/VAPID/AES/worker aceito em receptores locais (sem provedor público). CA16 continua bloqueado pela preservação de direitos de aceites posteriores ao target; rejeição negativa passou, caminho positivo está em curso. QA 24 casos teve 18 aprovados/6 falhas (cinco harness e uma ARIA corrigida, aguardando browser). Nenhum desses recortes equivale a fechamento ou deploy. P11 destino remoto ausente; P6 externa e P9 próximo push autorizado.
