# ADR 0002 — Armazenamento S3 local com pgsty/silo e django-storages

> **Contém:** a escolha do armazenamento de arquivos (PDFs e comprovantes) no ambiente local e como o código fala com ele.
> **Origem:** decisão D4 do documento "Varal — Ajustes" (Claude Docs `ce521944-15d6-44a5-b70c-f0790e03de41`), respondida em 12/11/2026.

- **Status:** aceita (12/11/2026)

## Contexto

A especificação (seção 9) pede armazenamento compatível com S3, com MinIO no desenvolvimento e na VPS. As imagens oficiais `minio/minio` (Docker Hub) e `quay.io/minio/minio` deixaram de estar disponíveis.

## Decisão

- **Local:** imagem `pgsty/silo` (continuação do `pgsty/minio`, compatível com a API S3 e com as variáveis `MINIO_*`), sempre com **tag de release fixa** (hoje `RELEASE.2026-11-12T00-00-00Z`), nunca `latest`. Uso só no ambiente local.
- **Código:** fala S3 por `django-storages`, com endpoint, bucket e chaves vindos do `.env`. Trocar de provedor não muda código.
- **Produção:** decidida na Etapa 11.

## Consequências

- A Etapa 06 está desbloqueada; é ela que instala `django-storages`, cria o bucket e as variáveis no `infra/.env.example`.
- O serviço `minio` do Compose fica no profile `storage` até ser executado e verificado uma vez (a checagem de segurança do agente bloqueou rodar a imagem na Etapa 00; o dono do projeto precisa liberar ou subir manualmente).
- Atualizar a tag é uma mudança explícita no `infra/docker-compose.yml`.
