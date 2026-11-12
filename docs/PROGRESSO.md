# Progresso

> **Contém:** o estado de cada etapa, as decisões pendentes e o log de mudanças (memória entre sessões).
> **Origem:** mantido pelo agente `varal-docs` ao fim de cada etapa; toda sessão nova começa lendo este arquivo.

## Etapas

| Nº | Etapa | Status | Branch | Concluída em | Relatório |
| --- | --- | --- | --- | --- | --- |
| 00 | Fundação | concluída | `etapa/00-fundacao` | 12/11/2026 | [relatorio](etapas/00-fundacao/relatorio.md) |
| 01 | Design system no código | pendente | — | — | — |
| 02 | Autenticação | pendente | — | — | — |
| 03 | Espaços e grupos | pendente | — | — | — |
| 04 | Contas (núcleo) | pendente | — | — | — |
| 05 | Boleto e Pix | pendente | — | — | — |
| 06 | PDF do boleto | pendente | — | — | — |
| 07 | Pagamento | pendente | — | — | — |
| 08 | Recorrência e agendador | pendente | — | — | — |
| 09 | Notificações | pendente | — | — | — |
| 10 | Solicitação e modo simples | pendente | — | — | — |
| 11 | Acabamento e deploy | pendente | — | — | — |

## Decisões pendentes

Divergências entre as fontes da verdade ou bloqueios. Não escolher sozinho: perguntar ao dono do projeto.

| # | Assunto | Fontes | Bloqueia |
| --- | --- | --- | --- |
| D1 | Altura do botão: 52 px (especificação §10 e guia `varal-ui`) ou 48 px (descrição do componente Button no Doop)? | spec × Doop | Etapa 01 |
| D2 | `StatusBadge` no Doop não tem variante `cancelada`, mas RN12 grava "Cancelada". Como uma conta cancelada aparece? | spec × Doop | Etapa 01 (ou 04) |
| D3 | O canvas tem NavItem, SideNav e o frame "D02 · Início" (desktop 1440×900), fora da especificação (13 telas, 14 componentes) e da tabela de etapas. O layout desktop entra no MVP? Em qual etapa? | spec × Doop | Etapa 01 |
| D4 | As imagens oficiais da MinIO (`minio/minio` no Docker Hub e `quay.io/minio/minio`) não estão mais disponíveis. O compose aponta provisoriamente para `pgsty/minio` (build comunitário do mesmo código), atrás do profile `storage`, ainda não executado. Aprovar essa imagem ou escolher outro armazenamento S3? | decisão "MinIO" × disponibilidade | Etapa 06 |
| D5 | RNF04 (exclusão e exportação de dados, LGPD) não está em nenhuma etapa. Em qual entra? | spec × plano de etapas | — |
| D6 | O `/etapa` cria a branch a partir da `main`, mas a Etapa 00 está só na `etapa/00-fundacao` (sem merge, por regra). Fazer o merge antes da Etapa 01? | fluxo | Etapa 01 |

## Log

Ordem cronológica inversa.

### 12/11/2026 — Etapa 00 (Fundação)

- Criados: estrutura do monorepo, docs quebrados da especificação (cópia literal, diagramas em Mermaid), matriz de rastreabilidade, 7 subagentes, comandos `/etapa` e `/status`, `CLAUDE.md`.
- Esqueleto: Django 6.1 + DRF + drf-spectacular (`/api/health/`, `/api/schema/`, `/api/docs/`), Celery com tarefa `ping`, Next.js 16 chamando o healthcheck via proxy `/api`, Compose, Makefile, CI.
- Decisões: usuário próprio (`contas_usuario.Usuario`, UUID) desde já; DRF autenticado por padrão; proxy same-origin `/api` no Next; MinIO opcional (profile `storage`) até D4; nginx adiado para a Etapa 11 (deploy).
- Conectores: Claude Docs não foi necessário (a especificação já existia em `docs/`); Doop funcionando (canvas, guia `varal-ui`, tokens e componentes lidos).
- Verificação local ok (`make dev`, `make test`, `make lint`, `make types`, `make seed`); CI não rodou no GitHub (sem remoto). Relatório escrito em `etapas/00-fundacao/relatorio.md`; etapa concluída.
