# CU01 — Cadastrar-se e entrar

> **Contém:** o caso de uso CU01: ator, fluxos, pós-condição e RNs.
> **Origem:** `docs/especificacao-varal.md`, seção 6, CU01.

- **Ator:** Usuário. **Pré-condição:** nenhuma.
- **Fluxo principal:**
  1. O usuário escolhe e-mail e senha ou Google.
  2. O sistema valida os dados e cria a conta.
  3. O sistema cria o espaço pessoal e abre o Início.
- **Alternativos:** e-mail já cadastrado → oferece entrar ou recuperar a senha. Chegou por convite → após o cadastro, entra direto no grupo (CU03).
- **Pós-condição:** usuário autenticado com espaço pessoal. **RN:** RN03.

Volta para o [índice dos casos de uso](README.md).
