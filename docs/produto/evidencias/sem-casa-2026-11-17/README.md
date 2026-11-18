# Evidências — contas sem casa e filtros

Diagnóstico consolidado em 17/11/2026 para [COR-07](../../correcoes-teste-inicial-2026-11-16.md#6-cor-07--diagnóstico-real-de-sem-casa-e-filtros). Não é uma correção entregue nem validação integral da Etapa 11.

## Método e resultados

- [Script API](reproduzir-api.py): cria usuário, grupo e três contas fictícias dentro de transação revertida; executa endpoints reais pelo `APIClient` com autenticação de teste. Não acessa contas existentes nem envia arquivos. Usa o ambiente local de desenvolvimento, não produção. O rollback é conferido por consulta ao UUID sintético após sair da transação; callbacks de commit não são executados.
- [Resultado API](resultado-api.json): POST 201; lista e filtro do próprio pagador incluem a conta sem casa; casa específica a exclui e limpar a recupera; mês separa novembro/dezembro; resumo omite a parcela sem casa em `por_casa`; `subgrupo=nenhum` retorna 400; mês vazio não oferece opções. Modo simples retorna as três abertas, inclusive dezembro. Todas as asserções do script passaram, exit 0, em duas execuções (a segunda acrescentou mês vazio/modo simples).
- [Fixture de interface](reproduzir-interface.tsx.fixture): monta `GrupoPagina`/`ContasPagina` reais com React Testing Library/Vitest; servidor e navegação são simulados, CSS/layout de browser não são medidos. Três asserções reproduzem lacunas de acesso, card com ação de edição e filtro ativo oculto. Conjunto executado duas vezes: **3 falhas em ambas**, exit 1, 10,48 s e 17,20 s. Antes dele, o caso isolado de grupo sem casa também falhou (21,94 s incluindo inicialização; teste 0,832 s).
- [Metadados](resultado-diagnostico.json): resultados, limites e hashes das fontes inspecionadas. Nenhuma credencial ou dado real foi capturado.

O comando executado para a API foi `docker compose -f infra/docker-compose.yml exec -T api python - < /tmp/varal-diagnostico-sem-casa.py` (cópia preservada acima). O de interface foi `cd web && npm test -- src/components/groups/sem-casa.diagnostico.test.tsx`. O arquivo temporário foi removido de `web/` depois da execução; sua cópia fica fora da descoberta automática de testes.

A fixture é instrumento de diagnóstico do comportamento atual. O segundo caso confirma a abertura de “Editar casa” antes de mostrar que não houve navegação; na implementação, substituir essa caracterização por uma regressão que confira a rota e as contas esperadas após clicar. Os demais casos também devem ser adaptados ao desenho aprovado, sem prender a solução ao texto ou ao elemento atuais.

## Repetir no desenvolvimento local

Na raiz do repositório, com os serviços locais já ativos:

```sh
docker compose -f infra/docker-compose.yml exec -T api python - < docs/produto/evidencias/sem-casa-2026-11-17/reproduzir-api.py
```

Para reproduzir as falhas de interface sem deixar teste deliberadamente vermelho na suíte normal, execute em um shell próprio:

```sh
diagnostico=$(mktemp --suffix=.test.tsx web/diagnostico-sem-casa.XXXXXX)
trap 'rm -f "$diagnostico"' EXIT
cp docs/produto/evidencias/sem-casa-2026-11-17/reproduzir-interface.tsx.fixture "$diagnostico"
(cd web && npm test -- "${diagnostico#web/}")
```

O resultado esperado no código diagnosticado é falha nas três asserções descritas. Não interpretar exit 1 como infraestrutura indisponível nem exit 0 da API como prova de que a experiência está correta.

## Conclusão delimitada

Não houve perda da conta sem casa no fluxo manual testado. Há falta de representação/acesso na página e no resumo por casas, ausência de filtro dedicado a casa nula e um defeito reproduzido que esconde controles de filtros ainda ativos. O mês obrigatório também exclui contas fora do período. A combinação exata do teste do dono não foi recuperada.

Uma regressão de ponta a ponta “criar sem classificação → achar no grupo → filtrar por mim → abrir/pagar → limpar filtros em mês vazio” teria exposto essas lacunas antes. A suíte existente cobre peças isoladas, mas isso não garantiu esse percurso. Correção do produto, revisão visual e validação em navegador ficam registradas no backlog.
