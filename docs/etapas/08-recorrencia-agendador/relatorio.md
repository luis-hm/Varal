# Relatório — Etapa 08 (Recorrência e agendador)

> **Contém:** entrega concluída, validação final e histórico dos desvios resolvidos.
> **Origem:** [spec](spec.md), [tarefas](tarefas.md), [Q08-1–10 e D08-1](decisoes.md), código/schema gerados e relatos backend/frontend/devops/QA de 16/11/2026.

**Concluída em 16/11/2026, pronta para commit e merge locais.** Abertura após commit `098b934` da Etapa 07 e merge local `2599655`; branch `etapa/08-recorrencia-agendador`. Não há commit/merge final da 08 nem push neste relatório.

## Implementação integrada

- Recorrencia, revisões, competências devidas e operação idempotente; criação gera a competência atual, rotina recupera devidas sem duplicar/preencher meses pausados. Fixa nasce pendente; variável nova nasce aguardando/NULL. Dias curtos e competência civil usam Fortaleza.
- Criação com `chave_idempotencia` e `ocorrencia_inicial` integra uma única conta com código/PDF próprios; retry idêntico preserva identidade, entrada divergente com a mesma chave dá 409. Mês inicial inválido e conflito de valor/data revertem sem eliminar draft válido. Modelo/futuras nunca reutilizam documento, código ou valor variável anterior.
- Confirmação explícita `confirmar_chegada`, edição/cancelamento `mes|proximos`, ações pausar/retomar/encerrar e arquivamento de casa com `destino_subgrupo` explícito. Operações respeitam visibilidade própria de modelo/conta; finais/invisíveis e históricos são preservados.
- Migrações `lancamentos.0003–0004` e `recorrencias.0001–0003` aplicadas no desenvolvimento. D08-1 preserva valor positivo legado em aguardando; NULL só em aguardando/cancelada, zero/negativos recusados. Q08-10 mantém criador por UUID/papel atuais e não restaura pagador/escolhidos removidos nem retoma modelo automaticamente. A coluna experimental de participação foi removida pela nova `0003`, sem reescrever migrações aplicadas.
- Tipos gerados, clientes/hooks e Folha comum de gestão pessoal/grupo integrados; Recorrências em Contas independe de ocorrência, Repete respeita autorização do modelo. Totais distinguem soma conhecida e quantidade a definir. Frontend consultou frames/guia Doop em leitura; composições delegadas não alteram status dos frames.

## Validação e evidências

| Verificação | Resultado comprovado | Limite |
| --- | --- | --- |
| Backend direcionado | 25 testes verdes: 21 de recorrências e quatro regressões de contas/casa/boleto; ruff check/format verdes nos arquivos alterados; configuração e migrações verificadas | Não é suíte integral; rodadas intermediárias falhas foram corrigidas e não contam como aprovação |
| QA complementar backend | 12 testes verdes de constraints SQL zero/negativo, chave divergente e rollback de mês inválido preservando draft PDF | Reexecução após corrigir fixture de configuração; não somar à suíte integral |
| Frontend após B08-3 | 101/101 Vitest, TypeScript e ESLint direcionado verdes após a correção final | Substitui 99/99 anteriores; testes de componente não equivalem à aprovação visual/E2E |
| Contrato | Duas gerações de tipos passaram, sem diferenças | API/produto congelados durante os ajustes finais dos testes E2E |
| Suíte atual após B08-4 | 448 pytest e tipos duas vezes verdes; web parou em 100/101 por teste antigo assíncrono de foco Clipboard | Runner terminou failed; o resultado anterior de 446 pytest precede duas regressões novas e não é o total atual |
| Revalidação web | Após corrigir somente o teste Clipboard com espera assíncrona, foco 2/2 e web 101/101, lint/tsc verdes | Produto intacto após os 448 pytest; foco/seleção continuam exigidos pelo teste |
| Validação final | Lint e E2E integrais verdes, ambos exit 0; 123 passaram e 3 skips previstos, 126 casos no total | Runner final status passed; substitui como resultado final as rodadas interrompidas/reprovadas abaixo |
| Correção de checks | Fixture/import/formatação do arquivo QA corrigidos; Ruff e os 12 testes QA repetidos verdes; lint final verde | Não somar os 12 repetidos à suíte |
| E2E integral, primeira rodada concluída | 118 passaram, 3 skips previstos, 3 falharam; todos os 14 novos passaram juntos | Rodada reprovada, não aprovação integral. Duas expectativas antigas de Ver todas em grupos e um helper de alvo checkbox foram corrigidos somente nos testes, preservando prova real de rótulo/foco |
| Agendador real | Beat e worker em banco/fila isolados publicaram/consumiram a tarefa real; catch-up e reinício mantiveram junho, julho, outubro e novembro únicos, sem agosto/setembro pausados | Intervalo curto de prova; agenda diária verificada separadamente com relógio Celery: 06:59 não devida, 07:00 devida, timezone America/Fortaleza. Não houve espera de disparo diário real |
| Recursos da prova | Serviços normais reiniciados/saudáveis; banco, fila e containers temporários removidos, volumes normais preservados | Prova local, sem produção ou transporte de avisos |

As contagens direcionadas são evidências separadas, não parcelas a adicionar à suíte integral. Logs temporários dos agentes sustentam esta consolidação; o estado durável está neste relatório e nos arquivos do repositório.

## Segurança e desvios corrigidos

**B08-3 fechado por reauditoria em leitura.** RecorrenciasFolha e ContaFolha passaram a comparar a edição com uma base capturada na abertura do formulário, preservando flags de autorização atuais. Refetch não vira intenção de alterar ACL, valor, dia/data, casa ou pagador; dois testes de regressão exigem payload apenas dos campos alterados, inclusive no escopo próximos. Audiência-base pública é normalizada sem apagar concessões latentes. Segurança não identificou novo bloqueante no delta; B08-1/B08-2 continuam corrigidos. Esse parecer não substitui QA/visual nem executou testes.

O foco anterior interrompido, com oito passes parciais, continua sem aprovação e foi sucedido pela rodada integral acima. Ruff inicialmente falhou apenas no arquivo de testes QA e passou após correção; o runner daquela rodada mantém status failed. O runner E2E também terminou failed pelas três falhas descritas. Nenhum desses estados é convertido em sucesso pela aprovação dos testes novos.

**B08-4 corrigido e delta reavaliado pela segurança, sem bloqueante.** Geração automática é ação do sistema por classificação central de `Historico.automatica`, usada pelo serializer e formatter; criação manual com autor excluído continua Ex-membro. Duas regressões de API passaram; não houve mudança de schema, migração, ACL ou reescrita de dados. Auditoria de decisões anterior permanece válida, pois o delta aplica a regra de autoria já vigente. Esse parecer de segurança do delta é distinto do resultado do QA.

A repetição lint/E2E anterior foi interrompida por solicitação da orquestração antes do patch B08-4, com exit -15 conhecido e processos próprios encerrados. Não conta como aprovação. A pipeline completa posterior passou 448 pytest/tipos duas vezes e parou no teste web Clipboard; a correção apenas desse teste foi revalidada separadamente. A repetição final de lint/E2E sobre produto congelado terminou passed/exit 0, com 123 aprovados e 3 skips previstos.

## Fechamento e continuidade

Resultado final: **448 pytest, 101 Vitest, duas gerações de tipos determinísticas, lint verde e E2E 123 aprovados/3 skips previstos**. Os 448 pytest são posteriores a B08-4; os 101 Vitest foram revalidados após espera assíncrona apenas no teste Clipboard, mantendo foco/seleção. Segurança encerrou B08-1–4, sem bloqueantes; decisões auditadas sem pendências. Prova operacional real do agendador permanece válida, com os limites descritos acima. A matriz e as evidências visuais/operacionais são consolidadas pelo QA sem alterar as contagens finais.

O dono atestou no chat não haver Ajustes pendentes também no fechamento. Não houve leitura/marcação por conector nem reexportação. Itens a marcar como “ — feito na etapa 08”: nenhum pendente identificado pela declaração vigente. P6 continua administrativa externa; P10/Perfil e P11/implantação permanecem sem resposta no [PROGRESSO](../../PROGRESSO.md), específicas da 11. Canvas e especificação de origem preservados.

Próximo passo autorizado: commit e merge locais da Etapa 08, registrando os hashes somente após executados; depois abertura da Etapa 09 para notificações/RN18, conforme delegação vigente. Este relatório não afirma que commit/merge da 08 já ocorreram. Sem push e sem autorização de implantação por silêncio.
