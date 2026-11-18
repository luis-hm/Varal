# ADR 0016 — Categorias com ícone no lugar de casas

> **Contém:** a troca do conceito "casa" por "categoria" dentro do grupo, o campo `icone` e o que isso muda em relação ao ADR 0005.
> **Origem:** DEC-01 do dono (17/11/2026) em [correções do teste inicial](../../produto/correcoes-teste-inicial-2026-11-16.md#12-decisões-para-a-próxima-conversa) e o pedido do dono no chat de 18/11/2026 ("os subgrupos não vão ser só casas, e sim uma ideia de categoria, com ícones").

- **Status:** aceita (18/11/2026)

## Contexto

O teste inicial mostrou que "casa" prende o grupo à ideia de família/imóvel. O dono quer organizar livremente ("Contas de luz", "Internet", "Carro") e escolher um ícone para cada uma. O ADR 0005 tirou do MVP a *categoria de orçamento* (v3), que é outra coisa.

## Decisão

- A tabela `espacos_subgrupo` continua sendo a entidade; a UI chama de **categoria**. API e tipos mantêm os nomes `subgrupo`, `casas` e `por_casa` (compatibilidade; renomear é só código e pode ser feito depois).
- Campo novo `Subgrupo.icone`, lista fechada `Icone` (`casa, luz, agua, internet, telefone, carro, mercado, saude, educacao, cartao, trabalho, lazer, pet, contas`), padrão `casa`. Migração `0007_subgrupo_icone` (casas existentes ficam com o ícone `casa`; nada é apagado nem remapeado, DEC-02).
- Categoria continua **opcional** na conta. Contas sem categoria aparecem como "Sem categoria" no resumo do grupo, no filtro (`subgrupo=nenhum`) e têm tela própria (`/grupos/{id}/categorias/sem-categoria`).
- O ADR 0005 continua valendo para a categoria de orçamento (v3): nenhum `lancamento.categoria_id`.

## Consequências

- Telas: Grupo (cards de categoria com ícone), Contas da categoria (COR-11), Nova conta (chips com ícone), Início ("Por categoria"), Recorrências.
- Permissão por categoria (COR-10) é decisão separada: [ADR 0017](0017-permissoes-por-categoria.md), ainda proposta.
- Como desfazer: remover o campo `icone` por migração reversa; a UI volta a dizer "casa".
