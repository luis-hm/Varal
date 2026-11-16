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
| Qual RF vira qual CU, RN, tela, etapa e teste? | [matriz-rastreabilidade.md](matriz-rastreabilidade.md) |
| Para que serve o produto? O que está no MVP? | [produto/visao-e-escopo.md](produto/visao-e-escopo.md) |
| Quem usa e com que papel? | [produto/atores-e-personas.md](produto/atores-e-personas.md) |
| Requisitos funcionais (RF01–RF25) | [requisitos/funcionais.md](requisitos/funcionais.md) |
| Requisitos não funcionais (RNF01–RNF12) | [requisitos/nao-funcionais.md](requisitos/nao-funcionais.md) |
| Como funciona o caso de uso CUxx? | [casos-de-uso/](casos-de-uso/README.md) (um arquivo por CU) |
| Qual é a regra RNxx? Como muda o status? | [regras-de-negocio/README.md](regras-de-negocio/README.md) |
| Quais entidades e campos existem? | [dados/modelo.md](dados/modelo.md) |
| Como as peças conversam? | [arquitetura/visao-geral.md](arquitetura/visao-geral.md) |
| Que versões, portas e variáveis de ambiente? | [arquitetura/stack.md](arquitetura/stack.md) |
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
