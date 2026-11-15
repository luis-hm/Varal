# Etapas

> **Contém:** a sequência de etapas do MVP, o que cada uma cobre e as telas do Doop envolvidas.
> **Origem:** plano de construção do projeto (prompt de fundação, seção 9).

Cada etapa é uma fatia vertical que funciona de ponta a ponta. Execução: comando `/etapa` (ver `.claude/commands/etapa.md`).
Estado atual: [PROGRESSO.md](../PROGRESSO.md).

**Toda tela é entregue nas duas versões (mobile e desktop) na mesma etapa**, conforme a equivalência em [design/README.md](../design/README.md#telas-mobile-página-02--desktop-página-03).
Itens do documento "Varal — Ajustes" que tocam uma etapa futura entram na spec dela.

| Nº | Etapa | Cobre | Telas do Doop |
| --- | --- | --- | --- |
| 00 | Fundação | Estrutura, docs, agentes, comandos, Docker, Makefile, CI, CLAUDE.md | — |
| 01 | Design system no código | Tokens → CSS, fontes, Icon (29 ícones) e componentes base: Button (52px), Chip, Field, StatusBadge (com `cancelada`), TopBar, TabItem, TabBar, **NavItem, SideNav** e o **shell responsivo** (TabBar < 1024px, SideNav ≥ 1024px) | Logo, Paleta e tipografia, Ícones, página Componentes |
| 02 | Autenticação | RF01–RF03, CU01, RN03; login e-mail/senha e **Google** (allauth headless), espaço pessoal automático | 01 · Entrar ↔ D01 |
| 03 | Espaços e grupos | RF04–RF07, CU02–CU04, RN01–RN07, RN21, RN24, **RN31 (link de convite, [ADR 0004](../arquitetura/adr/0004-rn31-link-de-convite.md))**; filtro central de acesso | 10 · Grupo ↔ D04, 11 · Convidar membro ↔ M05 |
| 04 | Contas (núcleo) | RF10–RF13, CU06–CU07, RN11–RN13, RN22; lançamento manual, lista, filtros (inclui "Canceladas", D2), detalhe, histórico, status calculado; conta cancelada fora do Início, listas padrão, totais e lembretes | 02 · Início ↔ D02, 03 · Contas e 07 · Detalhe ↔ D03 |
| 05 | Boleto e Pix | RF08, RF09, RF14, RN08–RN10; parsers da linha digitável e do BR Code; copiar código | (campos em 06 · Conferir ↔ M02) |
| 06 | PDF do boleto | RF23–RF25, RN25–RN29, CU05; upload para o S3 local (`pgsty/silo` via `django-storages`, [ADR 0002](../arquitetura/adr/0002-armazenamento-s3-local.md)), leitura assíncrona com pdfplumber, conferência, download por URL assinada | 05 · Nova conta ↔ M01, 06 · Conferir conta ↔ M02, 07 · Detalhe (PDF) ↔ D03 |
| 07 | Pagamento | RF15–RF17, CU08, RN14–RN16; marcar paga, comprovante, desfazer | 08 · Marcar como paga ↔ M03, 09 · Conta paga ↔ M04 |
| 08 | Recorrência e agendador | RF18–RF19, CU09, CU12, RN17, RN18, RN23; Celery beat diário às 7h | (no 10 · Grupo ↔ D04 e no 05 ↔ M01) |
| 09 | Notificações | RF20, RN19, RNF07, RNF10; Web Push + e-mail, central de avisos | 04 · Avisos ↔ D06 |
| 10 | Solicitação e modo simples | RF21–RF22, CU10–CU11, RN20 | 12 · Pedir para alguém pagar ↔ M06, 13 · Modo simples ↔ D05 |
| 11 | Acabamento e deploy | Animações finais, acessibilidade (auditoria), PWA instalável, RNF05, **RNF04/RN30 (LGPD, [ADR 0003](../arquitetura/adr/0003-rn30-exportar-e-excluir-dados.md))**, armazenamento de produção, deploy na VPS (só com ok explícito) | todas; tela Perfil ainda não existe no Doop: **parar e pedir** |

## Pasta de cada etapa

`docs/etapas/NN-slug/` nasce quando a etapa começa, escrita pelo agente `varal-docs`:

| Arquivo | Quando | Responde |
| --- | --- | --- |
| `spec.md` | início | escopo, RF/CU/RN/telas, critérios de aceite (Dado/Quando/Então), fora de escopo |
| `plano.md` | início | o que cada agente faz, contratos de API, migrações |
| `tarefas.md` | início | checklist ordenada com o agente responsável |
| `relatorio.md` | fim | o que foi feito, decisões, desvios, pendências |
