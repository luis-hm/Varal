# Etapas

> **Contém:** a sequência de etapas do MVP, o que cada uma cobre e as telas do Doop envolvidas.
> **Origem:** plano de construção do projeto (prompt de fundação, seção 9).

Cada etapa é uma fatia vertical que funciona de ponta a ponta. Execução: comando `/etapa` (ver `.claude/commands/etapa.md`).
Estado atual: [PROGRESSO.md](../PROGRESSO.md).

| Nº | Etapa | Cobre | Telas do Doop |
| --- | --- | --- | --- |
| 00 | Fundação | Estrutura, docs, agentes, comandos, Docker, Makefile, CI, CLAUDE.md | — |
| 01 | Design system no código | Tokens → CSS, fontes, Icon (29 ícones) e componentes base: Button, Chip, Field, StatusBadge, TopBar, TabItem, TabBar | Logo, Paleta e tipografia, Ícones, página Componentes |
| 02 | Autenticação | RF01–RF03, CU01, RN03; login e-mail/senha e **Google** (allauth headless), espaço pessoal automático | 01 · Entrar |
| 03 | Espaços e grupos | RF04–RF07, CU02–CU04, RN01–RN07, RN21, RN24; filtro central de acesso | 10 · Grupo, 11 · Convidar membro |
| 04 | Contas (núcleo) | RF10–RF13, CU06–CU07, RN11–RN13, RN22; lançamento manual, lista, filtros, detalhe, histórico, status calculado | 02 · Início, 03 · Contas, 07 · Detalhe |
| 05 | Boleto e Pix | RF08, RF09, RF14, RN08–RN10; parsers da linha digitável e do BR Code; copiar código | (campos em 06 · Conferir) |
| 06 | PDF do boleto | RF23–RF25, RN25–RN29, CU05; upload para MinIO, leitura assíncrona com pdfplumber, conferência, download por URL assinada | 05 · Nova conta, 06 · Conferir conta, 07 · Detalhe (PDF) |
| 07 | Pagamento | RF15–RF17, CU08, RN14–RN16; marcar paga, comprovante, desfazer | 08 · Marcar como paga, 09 · Conta paga |
| 08 | Recorrência e agendador | RF18–RF19, CU09, CU12, RN17, RN18, RN23; Celery beat diário às 7h | (no 10 · Grupo e no 05) |
| 09 | Notificações | RF20, RN19, RNF07, RNF10; Web Push + e-mail, central de avisos | 04 · Avisos |
| 10 | Solicitação e modo simples | RF21–RF22, CU10–CU11, RN20 | 12 · Pedir para alguém pagar, 13 · Modo simples |
| 11 | Acabamento e deploy | Animações finais, acessibilidade (auditoria), PWA instalável, RNF05, deploy na VPS (só com ok explícito) | todas |

## Pasta de cada etapa

`docs/etapas/NN-slug/` nasce quando a etapa começa, escrita pelo agente `varal-docs`:

| Arquivo | Quando | Responde |
| --- | --- | --- |
| `spec.md` | início | escopo, RF/CU/RN/telas, critérios de aceite (Dado/Quando/Então), fora de escopo |
| `plano.md` | início | o que cada agente faz, contratos de API, migrações |
| `tarefas.md` | início | checklist ordenada com o agente responsável |
| `relatorio.md` | fim | o que foi feito, decisões, desvios, pendências |
