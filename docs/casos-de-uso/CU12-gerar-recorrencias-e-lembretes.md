# CU12 — Gerar recorrências e lembretes

> **Contém:** o caso de uso CU12: ator, fluxos, pós-condição e RNs.
> **Origem:** `docs/especificacao-varal.md`, seção 6, CU12.

- **Ator:** Sistema (agendador). **Gatilho:** execução diária às 7h (America/Fortaleza).
- **Fluxo principal:**
  1. Gera as ocorrências das recorrências que entram no mês.
  2. Identifica recorrências variáveis ainda sem boleto a 5 dias do vencimento.
  3. Calcula os lembretes do dia (3 dias antes, no dia e 1 dia depois).
  4. Envia por push e e-mail e registra cada envio.
- **Alternativos:** falha no envio → tenta de novo até 3 vezes, sem duplicar o aviso.
- **Pós-condição:** ocorrências criadas e lembretes enviados uma única vez. **RN:** RN17 a RN19.

Volta para o [índice dos casos de uso](README.md).
