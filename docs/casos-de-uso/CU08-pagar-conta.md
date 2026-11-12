# CU08 — Pagar conta

> **Contém:** o caso de uso CU08: ator, fluxos, pós-condição e RNs.
> **Origem:** `docs/especificacao-varal.md`, seção 6, CU08.

- **Ator:** Pagador, Membro ou Admin. **Pré-condição:** conta Pendente (inclui vence em breve e vencida).
- **Fluxo principal:**
  1. O usuário toca em "Copiar código" ou "Baixar PDF" e paga no app do banco, fora do Varal.
  2. Volta e toca em "Marcar como paga", informando a data.
  3. Opcionalmente, anexa a foto ou o PDF do comprovante.
  4. O sistema muda o status e avisa o criador da conta.
- **Alternativos:** desfazer pagamento → só quem marcou ou um admin; o status volta a ser calculado pela data.
- **Pós-condição:** conta Paga, ou Confirmada se houver comprovante. **RN:** RN14 a RN16, RN29.

Volta para o [índice dos casos de uso](README.md).
