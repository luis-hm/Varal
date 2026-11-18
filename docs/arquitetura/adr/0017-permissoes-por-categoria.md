# ADR 0017 — Permissões por categoria (COR-10)

> **Contém:** a proposta de política para o admin definir o que cada membro pode fazer em cada categoria.
> **Origem:** COR-10 e DEC-04/08/09/10 de [correções do teste inicial](../../produto/correcoes-teste-inicial-2026-11-16.md#9-cor-10--permissões-por-categoria-configuradas-pelo-admin).

- **Status:** aceita (18/11/2026, aprovada pelo dono no chat) e implementada na Etapa 12.

## Contexto

O dono pediu que o admin configure, por categoria, quem pode ver, cadastrar, editar, pagar e gerenciar recorrências. Hoje a permissão vem só do papel no grupo (`api/apps/espacos/acesso.py`: `PERMISSOES`, `pode`, `_ve`) e da visibilidade da conta (RN02/RN06/RN07, ADR 0008).

## Proposta

1. **Sem configuração, nada muda.** Categoria nova ou existente nasce no modo "padrão do papel": vale exatamente a regra de hoje. Nenhuma migração abre ou fecha acesso.
2. O admin pode mudar uma categoria para **"personalizada"**. Aí cada membro (papéis `membro` e `observador`) tem um conjunto de capacidades naquela categoria:
   `ver`, `criar`, `editar`, `pagar` (pagar qualquer conta da categoria), `recorrencias`.
   - `pagar` sem `ver` é inválido (a API recusa). `criar`, `editar` e `recorrencias` exigem `ver`.
   - Ao ligar "personalizada", a tela já vem preenchida com o padrão do papel de cada pessoa (o admin vê o que vai valer antes de salvar; nada amplo é aplicado em silêncio).
   - **Pode ampliar o papel** (ex.: observador com `criar` em "Internet"), porque o dono pediu "sem promover a admin do grupo inteiro".
3. Sempre valem, em qualquer modo:
   - admin e dono: tudo (inclusive gerenciar a categoria e as permissões); continuam sem ver restritas de que não participam (Q6/ADR 0008).
   - criador e pagador atribuído sempre veem a conta; o pagador atribuído sempre pode pagá-la (RN07).
   - conta **restrita** continua restrita: `ver` na categoria **não** abre restritas; a restrição é por conta (ADR 0008).
   - papel `pagador` (modo simples) não é afetado: só vê o que paga.
   - pré-condições continuam (conta paga/cancelada, boleto aguardando conferência, RN14–RN16).
4. **Sem categoria** não é personalizável (fica no padrão do papel).
5. Revogação vale na próxima consulta/ação; não recolhe arquivos já baixados nem URLs assinadas já emitidas (expiram sozinhas).
6. Toda alteração grava histórico (autor, categoria, data, antes/depois) e usa `versao` para detectar edição concorrente (409).

## Implementação

- Observador sem concessão continua sem criar; com `criar`/`recorrencias` em alguma categoria, passa pela checagem do espaço e o serviço confere a categoria exata. Na Nova conta, o grupo do observador só aparece a partir das telas daquele grupo.
- `Subgrupo.personalizada=False` volta à regra anterior; as linhas de `PermissaoCategoria` são apagadas ao desligar.
- Consultas de contas usam `EXISTS` (não join) na checagem de categoria, porque são travadas com `FOR UPDATE`.
- Lacunas fechadas após a revisão de segurança (18/11/2026), a confirmar pelo dono (Q12-4 da etapa 12):
  - mudar o papel nunca deixa concessão acima do novo papel (membro → observador fica só com `ver`); promover não amplia nada; virar pagador apaga as concessões;
  - pôr a si mesmo como pagador exige `pagar` na categoria (senão `criar`/`editar` virariam pagamento);
  - pedir para alguém pagar exige `criar` sem categoria (a cópia nasce sem categoria);
  - "cancelar os próximos" deixa abertas as ocorrências de categorias sem `editar`;
  - quem entra no grupo depois que a categoria foi personalizada começa sem acesso a ela;
  - a geração automática de uma recorrência continua mesmo se o criador perder `recorrencias` (só a próxima ação manual é barrada).

## Consequências

- Modelo novo `PermissaoCategoria(subgrupo, membro, ver, criar, editar, pagar, recorrencias)` e `Subgrupo.personalizada`, `Subgrupo.versao`.
- `_ve`, `pode`, `pode_pagar`, `lancamentos.servicos.criar/editar`, recorrências, solicitações, downloads, avisos e resumos passam por uma função única de autorização por categoria.
- Plano de execução e testes: [handoff da etapa 12](../../etapas/12-correcoes-teste/handoff-codex.md#2-cor-10--permissões-por-categoria).
- Como desfazer: desligar "personalizada" em todas as categorias volta à regra atual; remover o modelo por migração reversa.
