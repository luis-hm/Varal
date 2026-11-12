# Documentação do Varal

> **Contém:** o índice da documentação e qual arquivo responde a qual pergunta.
> **Origem:** estrutura criada na Etapa 00 a partir de `especificacao-varal.md`.

Sessão nova começa por [PROGRESSO.md](PROGRESSO.md). Cada agente lê **só** os docs que a spec da sua etapa cita.

| Pergunta | Arquivo |
| --- | --- |
| Em que etapa estamos? O que falta decidir? | [PROGRESSO.md](PROGRESSO.md) |
| Quais são as etapas e o que cada uma cobre? | [etapas/README.md](etapas/README.md) |
| O que a etapa NN entrega e como se aceita? | `etapas/NN-slug/spec.md`, `plano.md`, `tarefas.md`, `relatorio.md` |
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
| Onde está a tela/componente no Doop? | [design/README.md](design/README.md) |
| Quais cores, fontes, raios? | [design/tokens.md](design/tokens.md) |
| Como anima? | [design/movimento.md](design/movimento.md) |
| Como gerar e versionar o OpenAPI e os tipos? | [api/README.md](api/README.md) |
| O texto original completo | [especificacao-varal.md](especificacao-varal.md) (origem; **não editar**) |

## Regras

- Docs mudam no **mesmo commit** que o código que os afeta.
- Mudar uma regra da especificação exige ADR em `arquitetura/adr/`, linha no log do `PROGRESSO.md` e aprovação do dono do projeto.
- Os arquivos de `produto/`, `requisitos/`, `casos-de-uso/`, `regras-de-negocio/` e `dados/` são cópias literais de trechos da especificação; os diagramas foram recriados em Mermaid.
