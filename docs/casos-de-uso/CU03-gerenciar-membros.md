# CU03 — Gerenciar membros

> **Contém:** o caso de uso CU03: ator, fluxos, pós-condição e RNs.
> **Origem:** `docs/especificacao-varal.md`, seção 6, CU03.

- **Ator:** Admin. **Pré-condição:** grupo existente.
- **Fluxo principal:**
  1. O admin gera um convite escolhendo o papel (Admin, Membro, Pagador ou Observador).
  2. O convidado abre o link, entra ou se cadastra e aceita.
  3. O sistema adiciona o membro com o papel do convite.
- **Alternativos:** convite expirado ou já usado → pede um novo. Alterar papel ou remover membro → o sistema bloqueia se o grupo ficaria sem admin.
- **Pós-condição:** membro no grupo com papel definido. **RN:** RN04, RN05, RN21, RN24.

Volta para o [índice dos casos de uso](README.md).
