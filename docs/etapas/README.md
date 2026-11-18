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
| 04 | Contas (núcleo) — **entrega em 15/11; revisão concluída em 16/11/2026** ([relatório](04-contas/relatorio.md)) | RF10–RF13, CU05 (manual), CU06–CU07, RN11–RN13, RN21, RN22, **RN32 ([ADR 0006](../arquitetura/adr/0006-rn32-conta-restrita-orfa.md))**, ADR 0005, 0007, 0008 e 0009; lançamento manual, lista, filtros (inclui "Canceladas", D2), detalhe, histórico, status calculado; audiência efetiva, privacidade no admin e serialização das operações concorrentes | 02 · Início ↔ D02, 03 · Contas e 07 · Detalhe ↔ D03 |
| 05 | Boleto e Pix — **concluída em 16/11/2026** ([relatório](05-boleto-pix/relatorio.md)) | RF08, RF09, RF14, RN08–RN10; parsers da linha digitável e do BR Code, instrumento e conferência, copiar código | 05/M01, 06/M02 e 07/D03 |
| 06 | PDF do boleto — **concluída em 16/11/2026** ([relatório](06-pdf-boleto/relatorio.md)) | RF23–RF25, RN25–RN29, CU05; upload para o S3 local (`pgsty/silo` via `django-storages`, [ADR 0002](../arquitetura/adr/0002-armazenamento-s3-local.md)), leitura assíncrona com pdfplumber, conferência, download por URL assinada | 05 · Nova conta ↔ M01, 06 · Conferir conta ↔ M02, 07 · Detalhe (PDF) ↔ D03 |
| 07 | Pagamento — **concluída em 16/11/2026** ([relatório](07-pagamento/relatorio.md)) | RF15–RF17, CU08, RN14–RN16; marcar paga, comprovante, desfazer (RN16: o admin só desfaz em conta que vê, Q21 da 04); barra de pagas e conta "pagas" do varal (Q12/Q23 da 04) | 08 · Marcar como paga ↔ M03, 09 · Conta paga ↔ M04 |
| 08 | Recorrência e agendador — **concluída em 16/11/2026** ([relatório](08-recorrencia-agendador/relatorio.md)) | RF18–RF19, CU09, CU12, RN17, RN18, RN23; Celery beat diário às 7h | (no 10 · Grupo ↔ D04 e no 05 ↔ M01) |
| 09 | Notificações — **concluída em 16/11/2026** ([relatório](09-notificacoes/relatorio.md)) | RF20, RN19, RNF07, RNF10; Web Push + e-mail, central de avisos; aviso ao admin da RN21; aviso ao removido das contas canceladas pela RN32 ([ADR 0006](../arquitetura/adr/0006-rn32-conta-restrita-orfa.md), a partir do histórico `cancelada_automaticamente`); RN19/RN21: o admin só é avisado de contas que vê (Q21 da 04) | 04 · Avisos ↔ D06 |
| 10 | Solicitação e modo simples — **concluída em 16/11/2026** ([relatório](10-solicitacao-modo-simples/relatorio.md)) | RF21–RF22, CU10–CU11, RN20; Q10-1–14/T10-A–E e [ADR0014](../arquitetura/adr/0014-solicitacao-e-sincronizacao-privada.md), cópia privada/sincronização e mesmaAPI/ACL no modo simples | 12 · Pedir para alguém pagar ↔ M06, 13 · Modo simples ↔ D05 |
| 11 | Acabamento e deploy — **em validação local, sem fechamento (16/11/2026)** ([spec](11-acabamento-deploy/spec.md), [plano](11-acabamento-deploy/plano.md), [tarefas](11-acabamento-deploy/tarefas.md), [decisões](11-acabamento-deploy/decisoes.md), [relatório](11-acabamento-deploy/relatorio.md)) | Animações finais, acessibilidade (auditoria), PWA instalável, RNF05, **RNF04/RN30 (LGPD, [ADR 0003](../arquitetura/adr/0003-rn30-exportar-e-excluir-dados.md))**, [ADR0015](../arquitetura/adr/0015-exportacao-exclusao-e-prova-local.md), exportação/exclusão, laboratório produtivo local e implantação remota dependente de destino/condições P11 | todas; Perfil sem frame dedicado: P10 resolvida por delegação expressa para compor com `varal-ui`/componentes existentes, sem alterar canvas; deploy efetivo mantém a dependência concreta P11; CA01–18 sem fechamento integrado; restauração ACL/direitos comprovada no recorte, desempenho/E2E final pendentes |
| 12 | Correções do teste inicial — **em andamento** ([spec](12-correcoes-teste/spec.md), [decisões](12-correcoes-teste/decisoes.md), [handoff](12-correcoes-teste/handoff-codex.md)) | COR-01–12 de [correções do teste inicial](../produto/correcoes-teste-inicial-2026-11-16.md); categorias com ícone ([ADR 0016](../arquitetura/adr/0016-categorias-com-icone.md)); permissões por categoria ([ADR 0017](../arquitetura/adr/0017-permissoes-por-categoria.md), proposta) | 02/D02, 03/D03, 05/M01, 07/D03, 10/D04; Perfil sem frame dedicado |

## Pasta de cada etapa

`docs/etapas/NN-slug/` nasce quando a etapa começa, escrita pelo agente `varal-docs`:

| Arquivo | Quando | Responde |
| --- | --- | --- |
| `spec.md` | início | escopo, RF/CU/RN/telas, critérios de aceite (Dado/Quando/Então), fora de escopo |
| `plano.md` | início | o que cada agente faz, contratos de API, migrações |
| `tarefas.md` | início | checklist ordenada com o agente responsável |
| `decisoes.md` | durante | decisões tomadas sem o dono (motivo, como desfazer) e perguntas ao dono com a resposta; mantido pelo `varal-decisor` |
| `relatorio.md` | fim | o que foi feito, desvios, pendências; linka `decisoes.md` e lista as perguntas abertas |
