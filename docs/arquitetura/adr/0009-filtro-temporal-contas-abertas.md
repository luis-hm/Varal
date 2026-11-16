# ADR 0009 — Prazo das contas abertas separado do status exibido

> **Contém:** o critério temporal comum aos filtros e contagens, sem substituir o selo de uma conta aguardando boleto.
> **Origem:** Q04-26 respondida pelo dono em 15/11/2026; Q04-17/Q04-35 fechadas pelo Codex sob delegação expressa do dono, com conferência atual dos Ajustes fornecida no chat. [Registro](../../etapas/04-contas/decisoes.md#conferência-atual-e-decisões-delegadas-do-codex-15112026).

- **Status:** aceita por decisão delegada do Codex (15/11/2026), não resposta literal do dono à Q04-35.

## Contexto

O dono determinou na Q04-26 que toda conta aberta vencida ou dentro da janela da RN13 entra em Precisa de atenção, inclusive `aguardando`, mantendo seu selo real. A implementação passou a contar aguardando vencida no Início, mas o filtro Vencidas da lista ainda incluía apenas pendente. O mesmo conceito apresentava números diferentes.

## Decisão

- Conta aberta é `pendente` ou `aguardando`. Paga, confirmada e cancelada não entram nesse conjunto.
- Nos filtros e nas contagens temporais, vencida é qualquer conta aberta com `vencimento < hoje`. Dentro da janela é qualquer aberta com `hoje <= vencimento <= hoje + janela_alerta_dias`.
- Hoje é a data civil em America/Fortaleza, como na RNF11. Os limites da janela da RN13 permanecem inclusivos.
- O selo continua representando o estado da conta: `aguardando` permanece Aguardando. Somente `pendente` recebe `status_exibido=vence|vencida` pela data; nenhum status novo é gravado.
- Lista, filtro Vencidas, contagens correspondentes e resumo usam o mesmo critério temporal, respeitando seus períodos já definidos: lista pelo mês consultado, números do Início pelo mês corrente, Precisa de atenção com vencidas de qualquer mês. Cada consulta parte apenas das contas visíveis ao usuário.

## Consequências

- Um card Aguardando pode aparecer no filtro Vencidas: o filtro informa o prazo, o selo informa que ainda falta o boleto.
- Atualizar consultas, contrato documentado e testes da Q04-35 com pendente/aguardando antes de hoje, hoje, no último dia da janela e depois dela; conferir exclusão de estados fechados e restritas invisíveis.
- Não antecipar fluxo de criação de aguardando: a recorrência variável da Etapa 08 é sua origem prevista. As etapas anteriores suportam leitura de registros existentes.
- Reversão exige alterar consultas e documentação; não há migração nem mudança de significado do status gravado.
