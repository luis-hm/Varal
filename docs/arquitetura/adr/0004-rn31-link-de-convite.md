# ADR 0004 — RN31: link de convite como credencial portadora

> **Contém:** a regra nova RN31 (geração, guarda, uso, revogação, limite e exibição do link de convite) e em que etapa ela entra.
> **Origem:** decisão 3 do ok do dono à Etapa 03, dada no chat em 14/11/2026; guia `varal-ui` (seção "Link de convite") e frames 11 · Convidar membro e M05 do canvas Doop `k0kB5dc-Vo`. Limite por usuário: decisão do orquestrador, a confirmar com o dono no relatório da Etapa 03.

- **Status:** aceita (14/11/2026); limite de aceite por usuário a confirmar.

## Contexto

RF05 e RN24 dizem que o convite é um link, expira em 7 dias e vale uma vez, mas não dizem como o link é protegido. Quem tem o link entra no grupo e vê dados financeiros: é uma credencial portadora, como uma senha. O frame antigo mostrava um código curto (`7KQ2-M9PX`), adivinhável. Um limite por IP hoje não funciona: a API vê o IP do Next para todo mundo (pendência P3), então viraria um limite global.

## Decisão

Nova regra **RN31**:

| ID | Regra |
| --- | --- |
| RN31 | O link de convite carrega um token aleatório de no mínimo 128 bits (`secrets.token_urlsafe(32)`); o banco guarda só o hash (SHA-256), nunca o token. O link é mostrado inteiro uma única vez, na criação; vale uma vez, expira em 7 dias (RN24) e o admin pode revogá-lo enquanto pendente. O aceite tem limite de tentativas: 10 por usuário por hora (e 10 por IP por hora quando a cadeia de proxies estiver configurada). Na tela o link aparece sempre encurtado, com reticências no meio (`varal.app/c/9fKq2mXb…R4dT`); copiar e compartilhar usam o link inteiro. |

- Entra na **Etapa 03**. O limite por IP entra com a P3 (Etapa 11).
- Hash sem sal: o token já tem entropia alta; a busca é pelo hash, sem comparação de segredo em texto.
- Convite inexistente, expirado, usado ou revogado recebem a mesma resposta (pedir um novo).

## Consequências

- `docs/regras-de-negocio/README.md` lista a RN31 em "Regras acrescentadas por ADR"; a especificação não é editada.
- A matriz liga RF05/CU03 e RN31 à Etapa 03.
- `Convite` tem `token_hash` e `revogado_em`; o token não aparece em coluna, log, admin do Django nem resposta posterior à criação.
- Fechar ou trocar o papel na folha do convite sem usar o link revoga o convite gerado, para não acumular links pendentes.
- P3 no PROGRESSO ganha: ativar também o limite de aceite por IP.
- Em aberto (Q1 da spec da Etapa 03): `token_urlsafe(32)` gera 256 bits, não 128; mantido por atender ao mínimo.
