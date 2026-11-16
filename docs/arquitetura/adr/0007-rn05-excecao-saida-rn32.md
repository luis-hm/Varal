# ADR 0007 — Exceção à RN05 na saída barrada pela RN32

> **Contém:** a única exceção à RN05 (quem não pode editar resolve, ao sair, a conta restrita que só ele vê), seus limites e onde é checada.
> **Origem:** resposta do dono à Q18 da Etapa 04 (chat, 15/11/2026); RN05 da especificação; RN32 ([ADR 0006](0006-rn32-conta-restrita-orfa.md)).

- **Status:** aceita (15/11/2026)

## Contexto

Pela RN32, sair do grupo sendo o último que vê uma restrita aberta é bloqueado até escolher outra pessoa para ver ou cancelar. Se essa pessoa é observador escolhido, ou pagador de papel pagador com o criador já fora, a RN05 não deixa ela editar nem cancelar, e o admin não vê a conta (RN06). Ela ficaria presa no grupo.

## Decisão

| Regra | Exceção |
| --- | --- |
| RN05 | Quem é a **última pessoa que vê** uma conta restrita aberta pode, **só dentro da própria saída do grupo barrada pela RN32**, fazer uma de duas ações nessa conta: acrescentar alguém em "Quem vê" ou cancelá-la. Toda vez fica no histórico. |

- Não é permissão permanente: fora da saída, a RN05 vale inteira (observador recebe 403 numa conta que vê e 404 numa que não vê). Sem isso, um observador poderia abrir a conta privada de outra pessoa.
- Só vale para as contas que barram a saída; qualquer outra dá 400.
- Resolução e saída acontecem na mesma transação: se ainda sobrar conta órfã, nada muda.
- Histórico com o autor (quem sai) e o motivo `saida_rn32`.
- Não vale para a exclusão da própria conta de usuário (Etapa 11): ali a pessoa sai antes dos grupos.

## Consequências

- `POST /api/grupos/{id}/sair/` aceita `resolucoes`; nenhum outro endpoint aceita. Detalhe no [plano da Etapa 04](../../etapas/04-contas/plano.md).
- `docs/regras-de-negocio/README.md` registra a exceção; a especificação não é editada.
- Testes `test_rn05_rn32_excecao_so_na_saida` e `test_rn05_fora_da_saida_observador_403_404`.
