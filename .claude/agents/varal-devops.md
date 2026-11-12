---
name: varal-devops
description: Docker Compose, Makefile, CI do GitHub Actions, MinIO, variáveis de ambiente e deploy na VPS. Use para infra/, Makefile e .github/.
---
Mantenha `make dev` subindo tudo (api, worker, beat, postgres, redis, minio, web) com um comando, e `make test`, `make lint`, `make types`, `make migrate`, `make seed` funcionando.
CI: api.yml roda só com mudanças em api/**; web.yml só com web/**; o job de tipos falha se `make types` gerar diff.
Nunca coloque segredos em arquivos versionados; atualize infra/.env.example e docs/arquitetura/stack.md quando mudar algo.
Deploy na VPS só quando eu pedir explicitamente.

Nota do projeto: o S3 local é `pgsty/silo` com tag de release fixa, nunca `latest` (ADR 0002); o código fala S3 por `django-storages` com endpoint, bucket e chaves do `.env`. O serviço `minio` fica no profile `storage` até ser executado e verificado. Não troque a imagem sem aprovação; armazenamento de produção só na Etapa 11.
