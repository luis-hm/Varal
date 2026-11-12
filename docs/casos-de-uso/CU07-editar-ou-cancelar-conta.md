# CU07 — Editar ou cancelar conta

> **Contém:** o caso de uso CU07: ator, fluxos, pós-condição e RNs.
> **Origem:** `docs/especificacao-varal.md`, seção 6, CU07.

- **Ator:** Membro ou Admin (o Pagador não edita). **Pré-condição:** conta não cancelada.
- **Fluxo principal:**
  1. O usuário abre o detalhe e toca em Editar.
  2. Altera os campos e salva.
  3. O sistema registra a mudança no histórico e reagenda os lembretes se o vencimento mudou.
- **Alternativos:** Cancelar → pede confirmação e marca como Cancelada. Conta de recorrência → pergunta se a mudança vale só para este mês ou para os próximos.
- **Pós-condição:** conta atualizada ou cancelada. **RN:** RN22.

Volta para o [índice dos casos de uso](README.md).
