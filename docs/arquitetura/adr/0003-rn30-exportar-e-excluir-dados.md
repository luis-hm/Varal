# ADR 0003 — RN30: exportar e excluir os dados do usuário (LGPD)

> **Contém:** a regra nova RN30, que detalha o RNF04 (LGPD), e em que etapa ela entra.
> **Origem:** decisão D5 do documento "Varal — Ajustes" (Claude Docs `ce521944-15d6-44a5-b70c-f0790e03de41`), respondida em 12/11/2026.

- **Status:** aceita (12/11/2026)

## Contexto

O RNF04 pede exclusão da conta e exportação dos dados conforme a LGPD, mas não estava em nenhuma etapa nem detalhado em regra de negócio.

## Decisão

Nova regra **RN30**:

| ID | Regra |
| --- | --- |
| RN30 | **Exportar:** o usuário baixa um JSON com os próprios dados (perfil, contas do espaço pessoal, participações em grupos, avisos) e links assinados dos PDFs dele. **Excluir conta:** apaga o espaço pessoal e os arquivos dele; nos grupos, as contas criadas por ele ficam no grupo com o autor exibido como "Ex-membro"; se for o único admin de um grupo, precisa passar a administração antes. |

- Entra na **Etapa 11**, antes do deploy, quando todas as entidades já existem.
- A tela Perfil ainda não existe no Doop: ao chegar na Etapa 11, **parar e pedir a tela** ao dono do projeto.

## Consequências

- `docs/regras-de-negocio/README.md` lista a RN30 em "Regras acrescentadas por ADR"; a especificação não é editada.
- A matriz liga RNF04 e RN30 à Etapa 11.
- A exclusão convive com RN04 (grupo sempre com admin) e RN22 (contas não são apagadas, só mudam de autor exibido).
