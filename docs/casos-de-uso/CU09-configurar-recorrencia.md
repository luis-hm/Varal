# CU09 — Configurar recorrência

> **Contém:** o caso de uso CU09: ator, fluxos, pós-condição e RNs.
> **Origem:** `docs/especificacao-varal.md`, seção 6, CU09.

- **Ator:** Membro ou Admin. **Pré-condição:** espaço selecionado.
- **Fluxo principal:**
  1. O usuário informa descrição, dia de vencimento, subgrupo e pagador.
  2. Escolhe valor fixo (ex.: aluguel) ou variável (ex.: luz).
  3. O sistema salva o modelo e gera a ocorrência do mês atual.
- **Alternativos:** pausar ou encerrar a recorrência → as ocorrências já geradas continuam.
- **Pós-condição:** modelo ativo. **RN:** RN17, RN18, RN23.

Volta para o [índice dos casos de uso](README.md).
