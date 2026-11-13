# Progresso

> **Contém:** o estado de cada etapa, as decisões (pendentes e resolvidas) e o log de mudanças (memória entre sessões).
> **Origem:** mantido pelo agente `varal-docs` ao fim de cada etapa; toda sessão nova começa lendo este arquivo.

## Etapas

| Nº | Etapa | Status | Branch | Concluída em | Relatório |
| --- | --- | --- | --- | --- | --- |
| 00 | Fundação | concluída | `etapa/00-fundacao` | 12/11/2026 | [relatorio](etapas/00-fundacao/relatorio.md) |
| 01 | Design system no código | concluída | `etapa/01-design-system` | 12/11/2026 | [relatorio](etapas/01-design-system/relatorio.md) |
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

## Decisões

Divergências entre as fontes da verdade ou bloqueios. Não escolher sozinho: perguntar ao dono do projeto.
Respostas vêm do documento "Varal — Ajustes" (Claude Docs `ce521944-15d6-44a5-b70c-f0790e03de41`).

### Pendentes

| # | Assunto | Bloqueia |
| --- | --- | --- |
| P1 | Rodar uma vez o serviço `minio` (`pgsty/silo`) para verificar o comando e as variáveis: a checagem de segurança do agente bloqueou executar a imagem. O dono do projeto sobe manualmente (`docker compose -f infra/docker-compose.yml --profile storage up -d minio`) ou libera a permissão. | Etapa 06 |
| P2 | Ativar a integração WSL do Docker Desktop e rodar `make test` e `make lint` (CA17 da Etapa 01). | Merge da Etapa 01 na `main` |

### Resolvidas

| # | Pergunta | Resposta (12/11/2026) | Onde |
| --- | --- | --- | --- |
| D1 | Altura do botão: 52 ou 48 px? | **52 px.** O CSS do Button no Doop já era 52 px; a descrição foi corrigida. | Etapa 01 |
| D2 | Como aparece uma conta cancelada? | StatusBadge ganhou `cancelada` (ícone `fechar`, texto "Cancelada", fundo branco, borda `--color-line`, texto `--color-ink-muted`). Sai do Início, das listas padrão, dos totais e dos lembretes; só no filtro "Canceladas" e no histórico; no card, valor riscado e opacidade reduzida. | Etapa 01 (selo), 04 (filtro e regras); [design](design/README.md#conta-cancelada-d2) |
| D3 | Desktop entra no MVP? | **Sim** (seção 12 da especificação reexportada). Shell responsivo (SideNav, NavItem, troca em 1024px) na Etapa 01; cada tela nas duas versões na mesma etapa da mobile. | [design](design/README.md#regra-responsiva), [etapas](etapas/README.md) |
| D4 | Qual armazenamento S3? | `pgsty/silo` com tag fixa, só local; código via `django-storages` com config no `.env`; produção na Etapa 11. Etapa 06 desbloqueada. | [ADR 0002](arquitetura/adr/0002-armazenamento-s3-local.md) |
| D5 | Onde entra o RNF04 (LGPD)? | Etapa 11, como regra nova **RN30** (exportar JSON; excluir conta com autor "Ex-membro" nos grupos). Tela Perfil não existe no Doop: parar e pedir. | [ADR 0003](arquitetura/adr/0003-rn30-exportar-e-excluir-dados.md) |
| D6 | Merge da Etapa 00 na main? | Merge local feito agora (`--no-ff`). Daqui em diante, rodar `/etapa` aprova a etapa anterior e faz o merge local dela antes da branch nova. Push só com pedido. | `.claude/commands/etapa.md` |

## Log

Ordem cronológica inversa.

### 12/11/2026 — Etapa 01 (Design system no código)

- Tokens do Doop em `tokens.css` (com bloco "fora do Doop": 4 medidas de texto e 5 sombras via `color-mix`), fontes por `next/font/google`, logo e favicon.
- Componentes: Icon (29), Button 52px (D1), Chip, Field, StatusBadge com `cancelada` (D2), TopBar, TabBar/TabItem, SideNav/NavItem; AppShell com troca em 1024px (D3); animações `press` e `badge-pulse` com reduced motion.
- Vitrine `/dev/componentes` (404 em produção) e páginas "Em breve" em `/`, `/contas`, `/grupos`, `/avisos`, `/perfil`.
- Playwright 1.65.0, `make e2e`, job `e2e` no `web.yml`. Vitest 29/29, ESLint e `tsc` limpos, Playwright 26/26.
- CA17 parcial: `make test`/`make lint` sem Docker no WSL (P2). Sete desvios deliberados aguardam confirmação do dono ([relatório](etapas/01-design-system/relatorio.md#desvios-deliberados-pedir-confirmação-ao-dono)).
- Ajuste pendente para a Etapa 02: variáveis do Google (allauth).

### 12/11/2026 — Etapa 00 (ajustes do documento "Varal — Ajustes")

- Aplicados os 11 itens e as decisões D1–D6: documento de ajustes como fonte mais forte (CLAUDE.md, docs/README.md); `/etapa` lê os ajustes, faz a revisão de ajustes antes do relatório e o merge local da etapa anterior; especificação reexportada (seção 12 ganhou as telas desktop); páginas e frames desktop do Doop, regra responsiva, componentes NavItem/SideNav e animações modal-pop, slide-in e scan em `docs/design/`; agentes de frontend e QA nas duas resoluções; matriz com frame mobile ↔ desktop.
- Regras: **RN30** (LGPD) criada pelo [ADR 0003](arquitetura/adr/0003-rn30-exportar-e-excluir-dados.md); armazenamento S3 local pelo [ADR 0002](arquitetura/adr/0002-armazenamento-s3-local.md).
- Etapa 01 passa a incluir NavItem, SideNav, o shell responsivo e o StatusBadge `cancelada`; Etapa 11 inclui RNF04/RN30 e o armazenamento de produção.
- Merge local de `etapa/00-fundacao` na `main` (`--no-ff`), sem push.

### 12/11/2026 — Etapa 00 (Fundação)

- Criados: estrutura do monorepo, docs quebrados da especificação (cópia literal, diagramas em Mermaid), matriz de rastreabilidade, 7 subagentes, comandos `/etapa` e `/status`, `CLAUDE.md`.
- Esqueleto: Django 6.1 + DRF + drf-spectacular (`/api/health/`, `/api/schema/`, `/api/docs/`), Celery com tarefa `ping`, Next.js 16 chamando o healthcheck via proxy `/api`, Compose, Makefile, CI.
- Decisões: usuário próprio (`contas_usuario.Usuario`, UUID) desde já; DRF autenticado por padrão; proxy same-origin `/api` no Next; MinIO opcional (profile `storage`) até D4; nginx adiado para a Etapa 11 (deploy).
- Conectores: Claude Docs não foi necessário (a especificação já existia em `docs/`); Doop funcionando (canvas, guia `varal-ui`, tokens e componentes lidos).
- Verificação local ok (`make dev`, `make test`, `make lint`, `make types`, `make seed`); CI não rodou no GitHub (sem remoto). Relatório escrito em `etapas/00-fundacao/relatorio.md`; etapa concluída.
