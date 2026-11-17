# Documentação do Varal

> **Contém:** o índice da documentação e qual arquivo responde a qual pergunta.
> **Origem:** estrutura criada na Etapa 00 a partir de `especificacao-varal.md`.

Sessão nova começa por [PROGRESSO.md](PROGRESSO.md). Cada agente lê **só** os docs que a spec da sua etapa cita.

**Fonte mais forte: o documento "Varal — Ajustes"** (Claude Docs, doc `ce521944-15d6-44a5-b70c-f0790e03de41`), lido sempre ao vivo pelo conector claude.ai Claude Docs. Vale mais que a especificação; um item escrito lá já conta como aprovação do dono do projeto. Só se marcam itens como feitos (" — feito na etapa NN"); nunca se apagam nem se reescrevem.

| Pergunta | Arquivo |
| --- | --- |
| O que o dono do projeto pediu para mudar? | "Varal — Ajustes" (Claude Docs `ce521944-15d6-44a5-b70c-f0790e03de41`, ao vivo) |
| Em que etapa estamos? O que foi decidido? | [PROGRESSO.md](PROGRESSO.md) |
| Quais são as etapas e o que cada uma cobre? | [etapas/README.md](etapas/README.md) |
| O que a etapa NN entrega e como se aceita? | `etapas/NN-slug/spec.md`, `plano.md`, `tarefas.md`, `relatorio.md` |
| O que a etapa 10 entregou? | [Solicitação e modo simples](etapas/10-solicitacao-modo-simples/spec.md), [plano](etapas/10-solicitacao-modo-simples/plano.md), [tarefas](etapas/10-solicitacao-modo-simples/tarefas.md), [decisões](etapas/10-solicitacao-modo-simples/decisoes.md) e [ADR0014](arquitetura/adr/0014-solicitacao-e-sincronizacao-privada.md) |
| O que a etapa 11 deve entregar e qual seu estado? | [Spec](etapas/11-acabamento-deploy/spec.md), [plano](etapas/11-acabamento-deploy/plano.md), [tarefas](etapas/11-acabamento-deploy/tarefas.md), [decisões](etapas/11-acabamento-deploy/decisoes.md) e [relatório](etapas/11-acabamento-deploy/relatorio.md) |
| Como exportar/excluir e recuperar sem ressuscitar dados? | [ADR0015](arquitetura/adr/0015-exportacao-exclusao-e-prova-local.md) e [protocolo do journal](arquitetura/protocolo-journal.md) |
| Qual RF vira qual CU, RN, tela, etapa e teste? | [matriz-rastreabilidade.md](matriz-rastreabilidade.md) |
| Para que serve o produto? O que está no MVP? | [produto/visao-e-escopo.md](produto/visao-e-escopo.md) |
| Quais correções e mudanças surgiram no teste inicial do dono? | [Correções de 16/11/2026](produto/correcoes-teste-inicial-2026-11-16.md): retorno à aba, contas sem mês obrigatório, grupos livres e cadastro por destino; análise ainda sem implementação |
| Quem usa e com que papel? | [produto/atores-e-personas.md](produto/atores-e-personas.md) |
| Requisitos funcionais (RF01–RF25) | [requisitos/funcionais.md](requisitos/funcionais.md) |
| Requisitos não funcionais (RNF01–RNF12) | [requisitos/nao-funcionais.md](requisitos/nao-funcionais.md) |
| Como funciona o caso de uso CUxx? | [casos-de-uso/](casos-de-uso/README.md) (um arquivo por CU) |
| Qual é a regra RNxx? Como muda o status? | [regras-de-negocio/README.md](regras-de-negocio/README.md) |
| Quais entidades e campos existem? | [dados/modelo.md](dados/modelo.md) |
| Como as peças conversam? | [arquitetura/visao-geral.md](arquitetura/visao-geral.md) |
| Que versões, portas e variáveis de ambiente? | [arquitetura/stack.md](arquitetura/stack.md) |
| Como operar o laboratório/primário restaurado sem contornar os gates? | [Runbook de operação local](arquitetura/operacao-local.md) (ACTIVE_RESTORE, backup, journal/WAL, ledger/direitos e limites P11) |
| Como operar o Silo remoto no Coolify e quais são seus limites? | [Silo na VPS](arquitetura/silo-coolify.md) e [Compose](../infra/silo/compose.coolify.yml); separado do laboratório e do desenvolvimento |
| Como funciona o backup local do Silo e como testar sua recuperação? | [Backup e recuperação do Silo](arquitetura/silo-backup-recuperacao.md), [agenda](../infra/silo/backup-schedule.json) e [template isolado](../infra/silo/compose.restore.yml) |
| Como planejamos usar IA para ler boletos e evitar erros recorrentes? | [Plano de IA para boletos](arquitetura/ia-boletos.md) e [pesquisa oficial Gemini](arquitetura/pesquisa-gemini-boletos.md); proposta ainda não implementada |
| Como publicar HMG/develop e preparar produção/main no Coolify? | [Varal no Coolify](arquitetura/coolify-varal.md), [Compose](../infra/deploy/compose.coolify.yml) e workflows `deploy-hmg.yml`/`deploy-prod.yml`; produção permanece bloqueada |
| Por que decidimos X? | [arquitetura/adr/](arquitetura/adr/) |
| Onde está a tela/componente no Doop? Como fica no desktop? | [design/README.md](design/README.md) (inclui a regra responsiva) |
| Quais cores, fontes, raios? | [design/tokens.md](design/tokens.md) |
| Como anima? | [design/movimento.md](design/movimento.md) |
| Como gerar e versionar o OpenAPI e os tipos? | [api/README.md](api/README.md) |
| O texto original completo | [especificacao-varal.md](especificacao-varal.md) (cópia da origem, doc `c3529f9b-eb78-41e6-aa80-2a31957e189e`; **não editar**, só reexportar) |

## Regras

- Docs mudam no **mesmo commit** que o código que os afeta.
- Mudar uma regra da especificação exige ADR em `arquitetura/adr/`, linha no log do `PROGRESSO.md` e aprovação do dono do projeto.
- Os arquivos de `produto/`, `requisitos/`, `casos-de-uso/`, `regras-de-negocio/` e `dados/` são cópias literais de trechos da especificação; os diagramas foram recriados em Mermaid.
