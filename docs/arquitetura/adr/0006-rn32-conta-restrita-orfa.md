# ADR 0006 — RN32: conta restrita nunca fica sem quem a veja

> **Contém:** a regra nova RN32 (conta restrita aberta que ficaria invisível para todos), os dois caminhos conforme quem age, como ela convive com RN06 e RN21 e em que etapa entra.
> **Origem:** respostas do dono às Q8 e Q17 da Etapa 04 (chat, 15/11/2026), no mesmo padrão da RN04 (último admin, decisão 4 da Etapa 03).

- **Status:** aceita (15/11/2026); caminhos por quem age definidos na Q17. Casos ligados: [ADR 0007](0007-rn05-excecao-saida-rn32.md) (Q18) e [ADR 0008](0008-rn06-prevalece-sobre-rn07.md) (Q19a).

## Contexto

Pela RN06 levada ao pé da letra (Q6 da Etapa 04), uma conta restrita só é vista por criador, pagador e escolhidos; o admin não entra por ser admin. Se todos eles deixam o grupo, a conta fica no banco sem ninguém que a veja: ninguém paga, edita nem cancela. Bloquear a remoção feita pelo admin revelaria a ele que existe uma conta que ele não vê (Q17).

## Decisão

Nova regra **RN32**:

| ID | Regra |
| --- | --- |
| RN32 | Uma conta restrita aberta (aguardando ou pendente) nunca fica sem ninguém que a veja. **Quando a própria pessoa age** (sair do grupo, excluir a própria conta de usuário), a operação é bloqueada (409) até ela escolher outra pessoa para ver a conta ou cancelá-la. **Quando o admin remove a pessoa**, a remoção nunca é bloqueada: cada conta assim é cancelada automaticamente ("cancelada automaticamente: ficou sem ninguém que pudesse vê-la") e o admin não recebe nenhum sinal dela. |

- **Quem vê depois** é calculado já com a RN21 aplicada: quem sai deixa de ser pagador e sai da lista de escolhidos; o criador que sai deixa de ser membro. Se a pessoa é a pagadora e, tirando-a, a conta fica sem ninguém que veja, também conta.
- **Saída e exclusão própria:** o 409 lista as contas (a pessoa as vê; nada vaza) e orienta o que fazer.
- **Remoção pelo admin:** mesma resposta (status, corpo, tempo aproximado) de uma remoção sem contas órfãs; nada de contagem, nome, valor, badge, total ou histórico visível ao admin. O histórico da conta guarda quem foi removido; o aviso ao removido com a lista do que foi cancelado é da **Etapa 09**.
- **Nunca** escalar a visibilidade para o admin, em nenhuma hipótese (RN06).
- Editar a conta deixando-a sem ninguém que veja é recusado (400, Q19b).
- Conta paga, confirmada ou cancelada não conta.
- Entra na **Etapa 04**, no ponto único `espacos.servicos._desligar` (modo voluntário e modo admin), na guarda `pre_delete` de `Usuario` (a mesma da RN04), em `alterar_papel` (ADR 0008) e na edição, com travas contra concorrência.

## Consequências

- `docs/regras-de-negocio/README.md` lista a RN32 em "Regras acrescentadas por ADR"; a especificação não é editada.
- A matriz liga RF06, RF11, RN06, RN21 e RN32 à Etapa 04.
- Testes `test_rn32_*` cobrem sair, excluir usuário (ORM, queryset e admin do Django), pagador que sai, remoção pelo admin com cancelamento, resposta idêntica ao admin e concorrência.
- A Etapa 09 entrega o aviso ao removido a partir do histórico `cancelada_automaticamente`.
- A privacidade continua: nenhum caminho dá acesso a quem não estava na conta.
