# CU05 — Cadastrar conta

> **Contém:** o caso de uso CU05: ator, fluxos, pós-condição e RNs.
> **Origem:** `docs/especificacao-varal.md`, seção 6, CU05.

- **Ator:** Membro (ou dono, no pessoal). **Pré-condição:** espaço selecionado.
- **Fluxo principal:**
  1. O usuário escolhe: enviar o PDF do boleto, colar o código, Pix ou digitar.
  2. O sistema lê o PDF ou o código, valida e preenche código, valor, data de emissão, vencimento e beneficiário.
  3. O usuário confere e informa descrição, subgrupo, pagador, categoria e visibilidade.
  4. Opcionalmente, marca "Repetir todo mês" (segue para CU09).
  5. O sistema salva e agenda os lembretes.
- **Alternativos:** código inválido → mostra o erro e mantém o campo. Boleto de concessionária → pede o vencimento. Pix dinâmico sem valor → pede o valor. PDF sem texto ou sem código válido → guarda o arquivo e pede para colar o código.
- **Pós-condição:** conta Pendente no espaço. **RN:** RN01, RN06, RN08 a RN11, RN25 a RN28.

Volta para o [índice dos casos de uso](README.md).
