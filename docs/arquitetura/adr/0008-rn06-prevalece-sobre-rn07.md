# ADR 0008 — Acesso explícito (RN06) prevalece sobre a perda por papel (RN07)

> **Contém:** a precedência entre RN06 e RN07 e o que acontece ao trocar o papel de alguém para pagador.
> **Origem:** resposta do dono à Q19a da Etapa 04 (chat, 15/11/2026); RN06 e RN07 da especificação; RN32 ([ADR 0006](0006-rn32-conta-restrita-orfa.md)).

- **Status:** aceita (15/11/2026)

## Contexto

Pela RN07 o pagador só vê as contas em que é o pagador. Trocar para pagador o papel de quem é o único que vê uma restrita aberta (como criador ou escolhido) deixaria a conta sem ninguém (RN32). Bloquear ou cancelar revelaria a conta ao admin que faz a troca.

## Decisão

| Regra | Precedência |
| --- | --- |
| RN06 × RN07 | O acesso explícito a uma conta restrita ("Quem vê", tabela `lancamento_acesso`) vale mais que a perda automática por papel. Um pagador que está em "Quem vê" de uma restrita continua vendo essa conta. |

- **Troca de papel para pagador:** não bloqueia e não cancela. Se a troca faria a pessoa perder a visão de uma restrita aberta que só ela vê, ela é incluída em `lancamento_acesso` e o histórico registra (`acesso_preservado`). A troca acontece, a conta sobrevive, nada vaza: o admin recebe a mesma resposta de uma troca sem esse efeito.
- Contas de visibilidade `grupo` seguem só a RN07.
- Novos escolhidos continuam sendo admin, membro ou observador; quem já está em "Quem vê" e virou pagador continua válido.
- Nunca dá acesso ao admin.

## Consequências

- `acesso.lancamentos_visiveis` e `quem_ve`: papel pagador vê `pagador=usuario` ou restrita com `usuario ∈ acesso`.
- `espacos.servicos.alterar_papel` ganha a preservação, com as travas da RN32.
- `docs/regras-de-negocio/README.md` registra a precedência; a especificação não é editada.
- Testes `test_rn06_rn07_alterar_papel_preserva_acesso` e `test_rn06_rn07_acesso_explicito_prevalece`.
