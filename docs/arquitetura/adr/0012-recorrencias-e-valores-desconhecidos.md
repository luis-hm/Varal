# ADR 0012 — Recorrências, valor desconhecido e geração privada

> **Contém:** decisões delegadas sobre recorrências mensais, valores desconhecidos e geração privada.
> **Origem:** autorização do dono para decisões/continuidade registrada no PROGRESSO; [Q08-1–10 e D08-1](../../etapas/08-recorrencia-agendador/decisoes.md). Não é reexportação da especificação nem resposta literal do dono.

**Status:** decidido por delegação em 16/11/2026; implementação concluída na Etapa 08.

## Contexto

RN17 exige variável aguardando, mas contas atuais exigem valor positivo. CU09 gera mês corrente e preserva ocorrências ao pausar/encerrar; CU07 diferencia só mês/próximos. Falhas do agendador e alterações de audiência/casa não estão detalhadas. CU04 exige mover/retirar casa das pendentes ao arquivar, limitado pela privacidade RN06 e precedente Q20/04. Conferência da 06 admite PDF válido sem código.

## Decisão

- Valor desconhecido é NULL em aguardando e continua NULL ao cancelar. Pendente/paga/confirmada exigem positivo. Resumos devolvem soma conhecida e quantidade desconhecida do mesmo universo autorizado; nunca fingem que NULL é 0 ou que soma parcial é total completo.
- Competência mensal é imutável e única por recorrência. Criar/retomar gera atual uma vez; rotina 07:00 Fortaleza e catch-up geram só competências cujo vencimento de geração ocorreu em período ativo, com revisão aplicável. Meses inteiramente pausados e anteriores à criação não são preenchidos. Devidas antes de pausar/encerrar continuam recuperáveis. Dia 29–31 usa último dia do mês quando necessário.
- Só mês altera ocorrência. Editar este mês e próximos altera revisão/modelo e campos pedidos nas abertas visíveis/editáveis a partir da competência; finais e históricos permanecem. Cancelar este mês e próximos encerra o futuro e cancela as abertas visíveis/editáveis do corte; pausar/encerrar o modelo isoladamente não cancela existentes. Não apagar valor/evidência já conferidos ao mudar tipo do template.
- Aguardando→pendente exige conferência autorizada de valor/data completos, por código válido ou manual completo, inclusive PDF sem código conhecido. Código não se torna obrigatório no caminho manual. Upload/worker não promovem conta.
- Geração nunca copia instrumento/PDF/comprovante anterior. Retira pagador sem vínculo/elegibilidade; revalida audiência atual. Restrita sem audiência pausa automaticamente, retém competência bloqueada e não amplia visão do admin. Retomada após reparação recupera devidas, mas não cria competências da pausa.
- Arquivar casa atua somente em abertas/modelos visíveis e editáveis, com opção destino ativo ou Sem casa. Invisíveis/finais guardam referência histórica sem sinal ao admin. Nova ocorrência de modelo com casa arquivada nasce Sem casa; a dívida não desaparece por perda de agrupamento.

## Consequências e reversão

A migração NULL requer adaptar contratos, filtros, totais e UI. A recuperação pode criar ocorrências vencidas de meses ativos antigos, com histórico e sem duplicação. Revisões/atividade devem persistir para não reconstruir passado pelo estado atual. Pausa por falta de audiência mantém obrigação privada bloqueada sem caminho privilegiado de admin. Fallback Sem casa preserva cobrança, mas exige reatribuição explícita se desejado.

Reversão exige migrações/regras prospectivas sem inventar valor, apagar competências ou expor contas. Atualizar derivados/modelo/matriz junto da 08; não editar a especificação de origem. A 09 entrega avisos; esta decisão não envia notificações nem antecipa RN20/10. Canvas deve ser lido antes da UI, sem alterações por este registro.

## Complemento Q08-8/9 — Gestão pessoal e primeira cobrança conferida

Decidido por delegação em 16/11/2026 a partir das pré-leituras frontend/backend da 08, sem nova consulta de canvas por este agente.

A gestão pessoal fica acessível por ação Recorrências em Contas, no espaço selecionado, usando a mesma Folha de lista/modelo do grupo. A entrada independe de existir ocorrência visível e alcança pausadas/encerradas. Repete no detalhe abre o modelo só quando a API autoriza vê-lo; não inferir gestão pela visibilidade da ocorrência. É composição delegada de tela, sem nova rota/frame ou mudança de status no Doop.

Repetir todo mês após 06/M02 salva atomicamente modelo, competência atual e **uma única** ocorrência contendo a cobrança confirmada e seu instrumento/PDF. O modelo nunca guarda esses dados reutilizáveis. Não salvar avulsa antes de criar outra ocorrência. Bloco inicial explicitamente conferido é opcional: fixa exige valor do modelo igual ao conferido; variável mantém NULL no modelo e pode confirmar a primeira aguardando→pendente na mesma transação, enquanto futuras continuam NULL. Dia das próximas pode diferir do vencimento inicial, com resumo explícito; não reescrever data confirmada.

Vencimento inicial de outro mês, inclusive codificado, gera erro claro no modo recorrente e preserva formulário/documento. Alternativa é salvar sem repetir ou configurar modelo em ação separada explicitamente apresentada como geração do mês atual. Nunca alterar código/data, mudar competência ou gerar conta extra silenciosa. Criação/retry usa identidade da operação, não deduplicação por descrição. Rollback é integral e não elimina arquivo/draft ainda válido.

Consequências: nova entrada contextual ocupa espaço em Contas, mas impede recorrências pessoais inacessíveis; restrição de mês limita o atalho, mas evita dupla obrigação. Reversão futura pode mover entrada mantendo acesso equivalente ou adicionar competência inicial escolhida por regra explícita; não modifica registros/documentos existentes. Integrar spec/contratos/CA/plano junto da 08, sem editar origem ou alegar que os frames já desenhavam todos os estados.


### Precisão de compatibilidade — D08-1

NULL é permitido apenas em aguardando/cancelada, sem obrigar toda conta aguardando a ter valor desconhecido. Valores positivos já gravados permanecem operacionais e com o mesmo status. A geração variável nova usa NULL; nenhuma migração apaga, desloca ou transforma o valor legado em estimativa.


### Reingresso — Q08-10

A autoridade de criador depende do UUID e do vínculo/papel atuais, sem prendê-la à participação original. Reingresso elegível recupera gestão, com retomada explícita da pausa. Pagador/escolhidos removidos não são restaurados por reingresso ou revisão antiga. Não se altera o acesso de contas/históricos anteriores nem se amplia a visibilidade ao admin.
