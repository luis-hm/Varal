# Spec — Etapa 08 (Recorrência e agendador)

> **Contém:** fontes obrigatórias, corte delegado e critérios da recorrência mensal e casa arquivada.
> **Origem:** RF18/RF19, CU04/CU07/CU09/CU12, RN11/RN17/RN18/RN21/RN22/RN23/RN32; [decisões](decisoes.md), [ADR 0012](../../arquitetura/adr/0012-recorrencias-e-valores-desconhecidos.md) e delegação vigente do dono.

Etapa 08 aberta em 16/11/2026, após a conclusão e integração local da Etapa 07. Decisões Q08-1–10 fechadas por delegação; implementação concluída. A fonte exige modelo mensal fixo/variável, ocorrência do mês atual ao criar, demais no primeiro dia do mês, rotina diária às 07:00 Fortaleza, dia 29/30/31 ajustado ao último do mês curto e preservação das ocorrências ao pausar/encerrar. CU07 exige só este mês/próximos; CU04 pede mover pendentes ou confirmar sem casa ao arquivar (adiado da 04).

Corte decidido Q08-1/2: ocorrência por `(recorrencia,competencia)` única no banco; competência não muda se vencimento for editado. Fixa nasce pendente/valor positivo; variável nasce aguardando com **valor NULL**, nunca zero/valor anterior inventado. Cancelar variável desconhecida preserva NULL; paga/confirmada/pendente exigem valor conhecido positivo. Totais/UI distinguem valor conhecido e a definir, sem apresentar NULL como cobrança grátis.

Modelo guarda espaço, autor, descrição, dia, tipo/valor, casa, pagador e visibilidade/escolhidos; revalida membros/acesso ao gerar. Não copia instrumento, código, PDF, emissão ou comprovante de mês anterior. Valor positivo legado em aguardando é preservado sem promoção ou estimativa; zero/negativo são sempre recusados (D08-1). Variável só passa a pendente por conferência explícita de valor/data completos, por código ou manual completo, inclusive PDF válido sem código conhecido conforme 06; mero upload/fim de tarefa não é confirmação.

Decisão Q08-3 de edição: só mês altera ocorrência; próximos altera ocorrência selecionada e modelo/abertas futuras aplicáveis, preservando pagas/confirmadas/canceladas e histórico. Pausa/encerramento não apagam nem cancelam automaticamente o já gerado. Recuperar meses ativos perdidos em lotes; não gerar meses pausados por inferência ao retomar. Sem audiência válida, pausar modelo e preservar competência devida bloqueada; jamais conceder visão a admin (Q08-5).

Arquivar casa opera somente sobre contas/recorrências que o admin já pode ver; confirmação/lista/contagem não revela restritas. Contas invisíveis podem manter referência arquivada com nome conforme precedente da 04. Nova ocorrência com casa arquivada nasce Sem casa, com histórico privado e sem descartar cobrança (Q08-6).

| CA | Dado / Quando / Então | Verificação |
| --- | --- | --- |
| CA01 | Dado um modelo válido, quando criado, então gerar o mês atual uma vez, mesmo depois do vencimento; fixa nasce pendente/valor positivo e variável aguardando/NULL. | RF18/RN17 + migração/regressões |
| CA02 | Dada uma competência devida, quando workers/retry/beat concorrem, então gerar uma única ocorrência e histórico, revalidando autorização/estado sob trava. | RF19/idempotência/concorrência |
| CA03 | Dado dia 29–31, quando gerar em fevereiro comum/bissexto ou mês de 30 dias, então ajustar ao último dia válido; rotina/competência usam Fortaleza inclusive na virada UTC. | RN23/RNF11 |
| CA04 | Dada execução perdida em período ativo, quando recuperar após pausa/encerramento/retomada, então gerar competências devidas sem reescrever já geradas ou preencher meses pausados. | CU09/CU12 e recuperação |
| CA05 | Dada uma ocorrência recorrente, quando editar só mês ou próximos, então respeitar o corte/escopo, preservar finais/histórico/competência/id e alterar modelo apenas no escopo próximos. | CU07/RN22 |
| CA06 | Dado valor NULL, quando listar, resumir, cancelar ou tentar pagar, então mostrar valor a definir e total conhecido/quantidade indefinida; cancelar preserva NULL e pagar exige valor completo. | RN11/RN17 + UI/tipos/totais |
| CA07 | Dada mudança de papel/pagador, casa ou visibilidade durante a geração, quando criar ocorrência, então revalidar sem conta órfã/acesso novo ao admin e sem copiar instrumento/arquivo antigo. Reingresso usa UUID/papel atuais, sem restaurar pagador/escolhidos revogados ou retomar automaticamente (Q08-10). | RN01/RN06/RN21/RN32 |
| CA08 | Dada casa com contas/modelos visíveis, quando arquivar com destino/sem casa, então registrar apenas alterações autorizadas, não revelar invisíveis em resposta/contagem e conservar tudo em rollback. | CU04/RN06/RN22 |
| CA09 | Dados os frames 10/D04, 05/M01, 06/M02, 07/D03 e RecurringRow/guia, quando usar recorrentes/criação/edição, então manter estados reais e acessíveis em mobile e desktop. | E2E/Doop em 390×844 e 1440×900 |
| CA10 | Dada a implementação integrada, quando ocorrer a validação final, então test/lint/types/E2E e segurança devem estar verdes, beat real/catch-up demonstrados e docs/matriz devem registrar resultados reais. | QA/segurança/relatório |
| CA11 | Dado um espaço pessoal ou de grupo sem ocorrências visíveis, quando abrir Recorrências em Contas, então acessar modelos visíveis inclusive pausados/encerrados e gerir somente conforme ações autorizadas. Repete no detalhe só abre modelo autorizado. | Q08-8; API, UI e E2E nas duas larguras |
| CA12 | Dada uma cobrança do mês atual conferida com código/PDF próprio, quando habilitar Repetir todo mês e salvar/repetir o comando, então criar atomicamente modelo e uma única ocorrência, com documento só nessa ocorrência; variável inicial confirmada fica pendente e futuras ficam aguardando/NULL. Falha reverte tudo preservando o draft válido. | Q08-9; transação, retry e UI |
| CA13 | Dado vencimento inicial fora do mês atual em Fortaleza ou valor fixo divergente do conferido, quando salvar com repetição, então recusar com erro de campo preservando formulário/PDF, sem alterar código/data ou criar conta extra; desligar repetição permite salvar avulsa. | Q08-9; negativos API/UI |

RN18 fornece dados/evento de boleto ausente D−5 para a 09; não enviar push/e-mail na 08 nem mudar RN19 pela janela visual RN13. Ajustes atuais: dono informou no chat que não há pendentes; P6 externa sem categoria. Perfil/deploy P10/P11 não bloqueiam 08.

## Triagem consolidada em 16/11/2026

Q08-1–10 estão decididas por delegação em [decisoes.md](decisoes.md) e no [ADR 0012](../../arquitetura/adr/0012-recorrencias-e-valores-desconhecidos.md). A implementação está concluída; D08-1 preserva valor positivo legado em aguardando e Q08-10 rege reingresso. CA04 inclui recuperar competências devidas enquanto ativa mesmo após pausa/encerramento, usando revisão do mês; nunca preencher competências da pausa. CA05 diferencia cancelar este mês e próximos (encerra futuro e cancela abertas visíveis/editáveis do corte) de pausar/encerrar modelo (preserva geradas); finais e invisíveis não são reescritas. CA06 preserva NULL inclusive cancelada e exige soma conhecida+quantidade desconhecida. CA07 inclui pausa automática privada e competência bloqueada sem audiência, pagador inelegível NULL e fallback Sem casa. CA08 não mostra sinais/contagens de invisíveis. Conferência manual completa, inclusive PDF sem código conhecido, é válida para sair de aguardando; upload sozinho não é. Não copiar instrumento/PDF de outro mês.

## Complemento delegado Q08-8/9 — Gestão pessoal e cobrança conferida

Contas oferece Recorrências para o espaço selecionado, inclusive pessoal, abrindo a mesma Folha de lista/modelo da gestão do grupo sem nova rota/frame. Entrada continua acessível sem ocorrência; Repete abre o modelo apenas se flag da API autoriza, sem ampliar ACL.

Repetir todo mês em 06/M02 cria modelo+competência atual+uma única ocorrência atomicamente, preservando somente nessa ocorrência os dados/instrumento/PDF já conferidos. Template nunca os guarda. Variável conserva NULL no modelo e pode confirmar a primeira aguardando→pendente na mesma transação; futuras ficam NULL. Fixa exige valor do modelo igual ao conferido. Resumo diferencia cobrança atual e dia/tipo das próximas, sem reescrever data.

CA01 passa a cobrir criação direta e criação a partir de conferência, idempotência sem conta avulsa duplicada, vínculo PDF/rollback integral e variável inicial confirmada com futuras NULL. Vencimento inicial de outro mês em Fortaleza recusa repetição com erro claro e preserva formulário; usuário pode salvar sem repetir, nunca recebe competência extra/data alterada silenciosamente. CA09 inclui gestão pessoal acessível para pausar/retomar/encerrar mesmo sem ocorrências visíveis e linha Repete respeitando acesso próprio ao modelo. Decisões de tela/contrato delegadas, não transcrição literal de fonte ou implementação entregue.

## Fora de escopo

Transporte de push/e-mail e entrega do aviso RN18 ficam na Etapa 09; solicitação e modo simples na 10; Perfil e implantação na 11. Não editar a especificação de origem, reintroduzir categoria ou alterar o canvas. P6, P10 e P11 permanecem registradas no PROGRESSO.

## Contrato implementado

A API recebe `valor_tipo: fixo|variavel`, `dia_vencimento`, `chave_idempotencia` UUID e `ocorrencia_inicial` opcional. Retorna `recorrencia` e `ocorrencia`; retry idêntico retorna a mesma criação, entrada divergente com a mesma chave dá 409. A confirmação de aguardando usa `confirmar_chegada`; edição/cancelamento recebem `escopo: mes|proximos`. CU04 exige `destino_subgrupo` explícito, UUID ou null. Ver [API](../../api/README.md#recorrências-e-valores-desconhecidos-etapa-08) e [modelo](../../dados/modelo.md#implementação-da-etapa-08). Evidências parciais e pendências no [relatório](relatorio.md).
