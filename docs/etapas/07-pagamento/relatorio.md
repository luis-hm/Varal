# Relatório — Etapa 07 (Pagamento)

> **Contém:** implementação presente, decisões, evidências disponíveis e pendências para fechar pagamento/comprovante/progresso.
> **Origem:** spec/plano/decisões07 e ADR0011, contrato OpenAPI/código atual, relatos backend/frontend/segurança e coordenação do orquestrador em16/11/2026; evidências finais consolidadas em16/11/2026.

## Estado

**Concluída; definição de pronto cumprida, pronta para commit/merge local.** Branch `etapa/07-pagamento`, após a06 em `4391b3d` e merge local `b21bd83`. Dono delegou decisões e continuidade entre etapas; não há novo pedido genérico de aprovação. Interface integrada; testes, lint, tipos, provas reais de comprovantes e segurança final aprovados. E2E integral final aprovado:107 passaram,3 skips previstos, status `passed` e exit0 em6,9min. Sem commit/push da07 por este registro e sem deploy.

## Implementação presente

- RF15/RN14: pagamento integral UUID/centavos/data civil em Fortaleza, valor esperado conferido sob trava, uma marca ativa e histórico atômico. Data não futura; alteração efetiva de valor com marca ativa exige undo.
- RF16/RN15: upload próprio do comprovante, spool privado e validação assíncrona isolada, originais JPEG/PNG/PDF até5MiB, imagens até20MP sem animação. Alias S3 privado com MIME validado, tentativaUUID e assinatura60s; worker só altera documento. Um arquivo por marca, anexo posterior ao autor/admin com acesso e permissão atual de pagar; vínculo/promover confirmada atômicos.
- RF17/RN16: undo por UUID exato, autor/admin visível; autor agora observador conserva apenas essa exceção. Marca, evento e evidência histórica permanecem. Não há troca/remoção isolada ou retorno a draft. Reabre pendente, limpa pagador sem vínculo atual e protege RN32 com409 atômico.
- Detalhe entrega marca ativa, lista histórica de pagamentos/referências de comprovante e flags de ações. Visibilidade atual da conta rege leitura ativa/histórica, inclusive para uploader/admin. Leituras e escritas seguram admins → membro → conta até serializar; admin invisível não ganha acesso.
- Q12/Q23/Q04-37: `pagas_qtd` em resumo/PorCasa, `contas_atribuidas_qtd` em membros e filtro coletivo `pagador=ex_membro`/`opcoes.ex_membro`. Sem pagador continua separado. Contagens só pelo visível, canceladas fora. Início/Grupo usam mês atual em Fortaleza; lista aceita mês explícito, sempre pelo vencimento e não pela data da marca.
- EventoPagamento único por marca persiste na mesma transação; anexo não duplica e undo não apaga. Transporte na09 deve revalidar destinatário, acesso e marca ativa antes de consumir/descartar/entregar. Evento não significa aviso enviado.
- Migrações `pagamentos.0001`/`lancamentos.0002` aplicadas no banco local, sem alteração pendente segundo `makemigrations --check`; API/worker/beat recriados sem remover volumes, conforme backend. Manutenção de comprovantes a cada300s (D07-1), distinta do agendador mensal08.

## Decisões e referência visual

Q07-1–11/[ADR0011](../../arquitetura/adr/0011-pagamento-e-evidencia.md) consolidam corte integral, exceção estrita de undo, original/EXIF com aviso, evidência privada histórica, anexação, métricas, reabertura e evento07→09. São decisões delegadas, não regras literais inventadas da origem. D07-1 registra frequência operacional e enum `pendente|lendo|valido|invalido|erro`; não são estados novos da conta.

Frontend leu guia/tokens/`varal-ui`, HTML e screenshots08/M03,09/M04,07/D03,02/D02,10/D04; frames draft usados por delegaçãoQ07-10 sem alterar canvas/status. Entregou folha/data/comprovante, aviso sobre original/metadados e confirmação responsiva. Confirmação usa “Pagamento registrado.”; barras usam proporção real, não largura ilustrativa do frame. QA comparou capturas e exercitou o fluxo em390×844/1440×900. Modal desktop corrigido para480×520 centralizado; janela1440×500 mantém ação acessível com altura limitada a468px. Mobile usa folha fullscreen. QA desativou animações somente nas duas capturas finais e confirmou check completo no sucesso mobile; a captura anterior durante animação foi substituída. Q07-11 mantém casa sem contas como “0 contas em mês”, sem barra/fração0 de0; com contas, “X de Y pagas em mês”. Tokens tipográficos e fixture Nome foram corrigidos durante validação.

## Evidências disponíveis

| Verificação | Resultado confirmado |
| --- | --- |
| `make test` | 413 pytest e91 Vitest verdes no comando; após ajuste mínimo de estado vazio, suíte web completa93/93 verde |
| Tipos / lint | Duas gerações determinísticas de tipos e lint integral verdes |
| QA direcionado | 21 backend +métrica isolada e5 pytest QA verdes; são evidências direcionadas, não somadas à suíte integral |
| Arquivos reais | Silo/Celery com PNG/PDF originais, bytes/MIME, URL assinada e limpeza verdes; sem assinatura/assinatura expirada negadas. Prova independente usou3s acelerados; E2E confere contrato de60s |
| Foco pagamento / legenda | 10/10 E2E pagamento e6/6 regressões de legenda verdes |
| Segurança final Astra | Interface/backend integrados sem bloqueantes; B07-1 tem regressão concorrente paga/confirmada verde |
| E2E integral final | 107 passaram,3 skips previstos, status `passed`, exit0 em6,9min; lint final exit0 |

Rodada E2E anterior:101 aprovados,3 skips previstos e6 falhas de expectativas legadas; correções aplicadas e foco de regressões verde. Essa rodada não conta como aprovação integral. A execução final acima terminou aprovada. Backend413/tipos2x são da rodada anterior; após a correção de legenda, repetiram-se web93/93, focos e lint/E2E, sem alegar nova execução backend.

Falha transitória anterior de bind mount em storage-init teve causa não confirmada; serviços foram validados depois e as provas reais de arquivo passaram. Testes de subprocesso incluem limites de tempo/memória; o caso com1MiB não caracteriza capacidade operacional sob carga.

## Handoff

Resumo final em `/tmp/varal-qa07-e2e-final.{json,log}`; QA confirmou capturas finais e runner/Next encerrados; matriz atualizada. Documentação e auditoria consolidadas; resta commit/merge local pelo orquestrador, sem push. P6 permanece administrativa externa; P10/P11 específicos da11 continuam sem resposta e não bloqueiam07.

## Ajustes e fora de escopo

Conferência atual dos Ajustes: dono declarou no chat “no varal ajustes n tem nenhum pendente”, sem conector/leitura remota/reexportação alegados. Nenhum item remoto a marcar como “— feito na etapa07” foi identificado nessa declaração. A declaração atual foi preservada na revisão documental; se houver itens novos, quem marca é dono/Claude Code.

Sem pagamento bancário real, parcial, prova de autenticidade, OCR de comprovante, RN20 antes da10, transporte de notificações antes da09, reexportação manual da especificação, push ou autorização de VPS por silêncio. RN30/exportação/exclusão integra-se na11; P6 permanece externa e sem categoria pelo ADR0005.
