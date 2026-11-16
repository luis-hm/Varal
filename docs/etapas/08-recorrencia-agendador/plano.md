# Plano — Etapa 08 (Recorrência e agendador)

> **Contém:** contrato implementado e organização da entrega concluída de recorrência/casas.
> **Origem:** [spec da Etapa 08](spec.md), RF18/RF19/CU04/CU07/CU09/CU12 e [Q08-1–10](decisoes.md) fechadas por delegação.

1. Abertura e triagem concluídas: Etapa 07 integrada localmente; Q08-1–10 e ADR 0012 fechados por delegação. Ajustes sem pendentes conforme declaração vigente do dono no chat, sem conector ou reexportação.
2. Backend cria Recorrencia, revisão/cursor efetivo e vínculo de competência em Lancamento; adapta constraints/serializers/serviços de dinheiro desconhecido, geração e CU04. Gerar não é bypass de permissão: regras de espaço/papéis/visibilidade permanecem centrais.
3. DevOps configura Celery beat diário 07:00 America/Fortaleza e comando de recuperação. Transações/unicidade protegem duplicidade mesmo com mais de um disparo.
4. Gerar tipos; frontend lê 05/M01, 06/M02, 07/D03, 10/D04 e RecurringRow e estados de edição/detalhe relevantes; QA→segurança→decisor→docs e commits locais sem push.

Modelo implementado: Recorrencia UUID/espaço/autor SET_NULL/descrição/dia 1–31/valor_tipo/valor_centavos?/casa?/pagador?/visibilidade/acesso/estado ativa-pausada-encerrada e controle de competências ativas. Lancamento acrescenta recorrencia/competencia e unicidade parcial; NULL monetário só nos estados desconhecidos permitidos. Modelo não armazena instrumento reutilizável. Encerrar é terminal salvo decisão explícita; não DELETE histórico.

Contrato integrado em `openapi.yaml` e `web/src/types/api.ts`: `valor_tipo: fixo|variavel`, `dia_vencimento`, `chave_idempotencia` UUID e `ocorrencia_inicial` opcional; criação retorna `recorrencia` e `ocorrencia`. Não há DTO paralelo. A implementação está concluída; detalhes em [API](../../api/README.md#recorrências-e-valores-desconhecidos-etapa-08).

| Contrato implementado | Guarda/efeito |
| --- | --- |
| GET/POST `/api/espacos/{id}/recorrencias/` | Lista só visíveis; criar exige criar_conta, valida template e gera mês atual atomicamente |
| PATCH `/api/recorrencias/{id}/` e ações pausar/retomar/encerrar | Editar modelo já visível, revalidar estado/permissão sob trava; existentes preservadas |
| PATCH/cancelar lançamento com `escopo: mes|proximos` | Competência alvo define corte; não atualizar finais/anteriores ou modelo no escopo mês; sem interpretar encerrar como delete/cancelar tudo |
| Arquivar subgrupo com opção mover/sem casa | Só universo visível/editável e destino do mesmo grupo; nenhuma consulta/resposta revela restrita |
| Tarefa/comando gerar até competência atual | Trava/revalida modelo e membros, usa único `(recorrencia,competencia)` e checkpoint só após commit; batches recuperam falha sem duplicar |

Ordem de travas deve compatibilizar geração/edição com admins/membro/contas da 04 e pagamento 07. Pausa concorrente à geração decide por estado sob trava; retry não gera além do checkpoint confirmado. Guardar janelas/cursor de atividade para não preencher meses pausados ao retomar. Mudança de pagador/papel atual não transforma modelo restrito em público; ninguém visível é caso explícito de pausa/erro controlado, não permissão de admin inventada.

API/UI expõem valor NULL como a definir; resumos/listas/PorCasa acrescentam `valores_indefinidos_qtd` sobre o mesmo universo visível. A soma inclui só valores conhecidos e sua legenda vira total conhecido quando houver desconhecidos, nunca total completo silenciosamente parcial. Cancelada desconhecida conserva NULL; bills variáveis antigas não são atualizadas com o valor de outra competência. PDF manual/código novo seguem conferência/autorização existentes; tarefa não promove status só por existir arquivo. Eventos/derivação D−5 ficam prontos para 09, sem transporte antecipado.

## Precisões Q08-8/9 para implementação

- Frontend: ação Recorrências em Contas abre a mesma Folha de lista/modelo em qualquer espaço selecionado, inclusive pessoal e sem ocorrências. Repete no detalhe abre diretamente só quando `pode_ver_recorrencia`; ações do modelo dependem das flags próprias. Não criar nova rota/frame ou duplicar consultas/componentes.
- Backend: criação do modelo aceita bloco opcional de ocorrência inicial conferida, separado do template. Um serviço/transação cria modelo, competência atual e uma única conta com instrumento/PDF dela, reaproveitando validação/travas 05/06. Sem salvar avulsa antes. Reenvio da mesma operação/entrada é idempotente; chave reutilizada com outra entrada/espaço retorna 409. Documento não entra no template nem em futuras competências; rollback integral conserva draft anterior.
- Fixa exige valor confirmado igual ao do modelo. Variável mantém NULL no template e confirma explicitamente a primeira aguardando→pendente na mesma transação; sem bloco permanece NULL. Resumo mostra data/valor atuais e dia/tipo futuros, sem alterar data confirmada.
- Vencimento inicial fora do mês atual em Fortaleza gera erro de campo preservando formulário/PDF. Não ajustar código/data nem criar ocorrência extra. Desligar repetição permite salvar avulsa; configurar modelo separado é outra ação explícita que informa geração do mês atual. Cobrir esse negativo e futuras NULL/ausência de cópia de documentos nos CA01/CA09/CA11–CA13.

## Precisões da implementação

D08-1 mantém positivos legados em aguardando sem apagar/promover dados; NULL só é aceito em aguardando/cancelada. Q08-10 usa autoria por UUID e vínculo/papel atuais; a coluna experimental de participação foi removida por `recorrencias.0003`, preservando migrações aplicadas. Geração atrasada não restaura pagador/escolhidos revogados. Agenda materializa competências em lotes de 120 por cursor, revisões e obrigações persistidas; pausa materializa devidas e retomada reposiciona cursor no mês atual, sem preencher meses pausados. Não há tabela de intervalos separada nem versão otimista de modelo.

Tarefa `apps.recorrencias.tasks.gerar_recorrencias` e comando `python manage.py recuperar_recorrencias` compartilham a execução idempotente. Beat usa 07:00 em America/Fortaleza; a manutenção de comprovantes permanece a cada 300 s. Prova real usou banco/fila descartáveis e intervalo curto, com verificação separada da agenda 07:00, sem afirmar espera real até esse horário.
