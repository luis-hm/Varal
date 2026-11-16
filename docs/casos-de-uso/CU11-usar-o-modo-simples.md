# CU11 — Usar o modo simples

> **Contém:** o caso de uso CU11: ator, fluxos, pós-condição e RNs.
> **Origem:** `docs/especificacao-varal.md`, seção 6, CU11; decisões delegadas Q10-11–14/Q04-23/Q10-15/Q04-29/Q10-17 e implementação da etapa 10 concluída.

- **Ator:** Pagador. **Pré-condição:** papel de Pagador em algum grupo.
- **Fluxo principal:**
  1. Ao entrar, o pagador vê só a lista do que pagar, ordenada por vencimento.
  2. Toca em "Copiar código" ou "Baixar PDF" e paga no banco.
  3. Toca em "Já paguei" e, se quiser, tira foto do comprovante.
- **Pós-condição:** igual ao CU08. **RN:** RN07, RN14, RN15.

Na implementação10, a lista contém todas as abertas visíveis, com ações conforme recursos e permissão atual. Pagas/confirmadas usam vencimento no mês civil de Fortaleza. O título abre o detalhe autorizado (RF13/CU06/RF25), com retorno ao mesmo recorte; a saída reutiliza RF06/CU03/RN04/RN21/RN32. O shell próprio mantém Grupos e logout. Não concede editar contas (RF12) ou gerenciar casas (RF07). Estado de QA no [relatório10](../etapas/10-solicitacao-modo-simples/relatorio.md).

Volta para o [índice dos casos de uso](README.md).
