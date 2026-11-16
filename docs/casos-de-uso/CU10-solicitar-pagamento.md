# CU10 — Solicitar pagamento

> **Contém:** o caso de uso CU10: ator, fluxos, pós-condição e RNs.
> **Origem:** `docs/especificacao-varal.md`, seção 6, CU10; ADR0014 e decisões delegadas10, implementação concluída.

- **Ator:** Usuário (dono do espaço pessoal). **Pré-condição:** conta pessoal pendente e participação em pelo menos um grupo.
- **Fluxo principal:**
  1. No detalhe da conta pessoal, toca em "Pedir para alguém pagar".
  2. Escolhe o grupo e o pagador, e pode deixar uma mensagem.
  3. O sistema cria a solicitação no grupo e avisa o pagador.
- **Pós-condição:** a conta aparece no grupo; quando paga lá, a original fica Paga no pessoal. **RN:** RN20.

Na implementação10, solicitar exige vínculo atual admin/membro e pagador elegível, confirmação da cópia restrita e dos campos/PDF integral. O aceite202 indica preparação; só ativação indica pedido criado. Fechar não cancela e a recuperação usa a mesma origem própria+nonce. Nenhum dado exclusivo do pessoal aparece no grupo. Estado de QA e limites no [relatório10](../etapas/10-solicitacao-modo-simples/relatorio.md).

Volta para o [índice dos casos de uso](README.md).
