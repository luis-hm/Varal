# ADR 0006 — RN32: conta restrita nunca fica sem quem a veja

> **Contém:** a regra nova RN32 (bloqueio quando uma conta restrita aberta ficaria invisível para todos), como ela convive com RN06 e RN21 e em que etapa entra.
> **Origem:** resposta do dono à Q8 da Etapa 04 (chat, 15/11/2026), no mesmo padrão da RN04 (último admin, decisão 4 da Etapa 03).

- **Status:** aceita (15/11/2026); casos de borda abertos nas Q17–Q19 da [spec da Etapa 04](../../etapas/04-contas/spec.md#perguntas-novas-abertas).

## Contexto

Pela RN06 levada ao pé da letra (Q6 da Etapa 04), uma conta restrita só é vista por criador, pagador e escolhidos; o admin não entra por ser admin. Se todos eles deixam o grupo, a conta fica no banco sem ninguém que a veja: ninguém paga, edita nem cancela.

## Decisão

Nova regra **RN32**:

| ID | Regra |
| --- | --- |
| RN32 | Uma conta restrita aberta (aguardando ou pendente) nunca fica sem ninguém que a veja. Se sair do grupo, ser removido ou excluir a própria conta de usuário deixaria uma conta assim sem nenhum membro que a veja (RN06 e RN07), a operação é bloqueada (409) até a pessoa escolher outra pessoa para ver a conta ou cancelá-la. |

- **Quem vê depois** é calculado já com a RN21 aplicada: quem sai deixa de ser pagador e sai da lista de escolhidos; o criador que sai deixa de ser membro. Logo, se a pessoa é a pagadora e, tirando-a, a conta fica sem ninguém que veja, também bloqueia.
- Conta paga, confirmada ou cancelada não bloqueia.
- Entra na **Etapa 04**, no ponto único `espacos.servicos._desligar` e na guarda `pre_delete` de `Usuario` (a mesma da RN04), com travas contra concorrência.

## Consequências

- `docs/regras-de-negocio/README.md` lista a RN32 em "Regras acrescentadas por ADR"; a especificação não é editada.
- A matriz liga RF06, RF11, RN06, RN21 e RN32 à Etapa 04.
- Testes `test_rn32_*` cobrem sair, remover, excluir usuário (ORM, queryset e admin do Django), pagador que sai e concorrência.
- A mensagem do 409 orienta o que fazer (escolher outra pessoa para ver ou cancelar).
- A privacidade continua: o bloqueio não dá acesso a ninguém. Como responder ao admin que remove alguém sem ver as contas que bloqueiam é a Q17.
