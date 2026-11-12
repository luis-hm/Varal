# CU10 — Solicitar pagamento

> **Contém:** o caso de uso CU10: ator, fluxos, pós-condição e RNs.
> **Origem:** `docs/especificacao-varal.md`, seção 6, CU10.

- **Ator:** Usuário (dono do espaço pessoal). **Pré-condição:** conta pessoal pendente e participação em pelo menos um grupo.
- **Fluxo principal:**
  1. No detalhe da conta pessoal, toca em "Pedir para alguém pagar".
  2. Escolhe o grupo e o pagador, e pode deixar uma mensagem.
  3. O sistema cria a solicitação no grupo e avisa o pagador.
- **Pós-condição:** a conta aparece no grupo; quando paga lá, a original fica Paga no pessoal. **RN:** RN20.

Volta para o [índice dos casos de uso](README.md).
