# Plano — Etapa 10 (concluída)

> **Contém:** dados, contratos, protocolo técnico ratificado e ownership da implementação10.
> **Origem:** spec/decisoes/ADR0014 integrados, Q10-1–14 e T10-A–E ratificados pelo orquestrador; `/tmp/varal-10-arquitetura.md` e planos backend/boletos/frontend10.

Etapa aberta em16/11/2026 em `etapa/10-solicitacao-modo-simples`, após commit09 `4e04ddf`/merge local `56337ed`. Q10-1–14 triadas e T10-A–E ratificados, sem novo ok genérico pela delegação existente. Backend/frontend/boletos integrados e congelados para QA. Evidências dirigidas e limites no [relatório](relatorio.md); API/web integrais aprovadas (506 pytest e 127 Vitest), tipos determinísticos e lint verdes; E2E integral aprovado (143 testes e três skips previstos), 14 CAs consolidados com limites no relatório. Foco visual/retorno nas duas larguras passou após correções. Auditoria Q10-15–18/D10-1/2 sem perguntas novas. Ajustes sem pendentes atestados pelo dono no chat, sem conector remoto. P10 resolvida por delegação para11, sem inventar frame; P11/destino e P6 externa permanecem.

## Ordem e ownership

1. Orquestrador fechou/integrou09 e abriu10; docs integrou os documentos e registrou triagem/ratificação. Conferir contratos reais ao implementar, sem novo ok genérico.
2. **Backend único dono** de `api/apps/solicitacoes/`, coordenador/par/causas/eventos/API e integrações em pagamentos/lancamentos/espacos/recorrencias/notificacoes/auth-delete/config, migrações e testes cruzados. Publica domínio, define fases e contrato dehelpersPDF. Não dividir coordenação entre agentes.
3. **`/root/boletos_10` somente** `api/apps/boletos/`, helpers/pins/intenção/cópia/cleanup, migrações e testesPDF acordados. Não autoriza grupo/publica conta; alterações fora desse ownership são repassadas ao backend. Agentes preservam edições alheias.
4. Schema/tipos reais gerados pelo orquestrador; **frontend integrado ao contrato real**, sem DTO manual. Usa leituraDoop/guia atual documentada e confere proveniência antes daUI. QA→segurança→auditoria→docs/commits locais, sempush/deploy.

## Dados e contrato

`Solicitacao`: UUID, origem/cópia/solicitante anuláveis semCASCADE da origem/usuário, destino/pagador inicial, estados preparando/ativa/quitada/encerrada/falhou, snapshot financeiro privado mínimo confirmado, nonce/hash, revisão/tentativa/lease/datas. Unique parcial de solicitação viva por origem; tombstone e chave estável preservam idempotência terminal. `ParPagamento` privado guarda marcas exatas e causa única, sem referências pessoais noDTO/histórico/admin/erros do grupo. `EventoSolicitacao` único por ativação para pagador inicial, durável e varrível mesmo com falha dobroker. Pins/writers/intençãoPDF independem doCASCADE; nenhum snapshot financeiro em storage deUI ou registro operacional de pin.

| Contrato implementado | Efeito |
| --- | --- |
| GET `/api/lancamentos/{origem}/solicitacoes/opcoes/` | Grupos admin/membro atuais com pagadores elegíveis; origem pessoal pendente do dono |
| POST `/api/lancamentos/{origem}/solicitacoes/` | `{nonce,grupo_id,pagador_id,mensagem?,confirmar_compartilhamento:true,versao_compartilhamento}`; mensagem até500, hash64; rejeita campos desconhecidos. Sempre202 com `{id,nonce,estado,pode_cancelar,copia_id}`; cópia só se atualmente visível |
| GET/DELETE `/api/lancamentos/{origem}/solicitacoes/nonce/{nonce}/` | GET200 recupera,404 não autoriza nonce novo. DELETE204 cria tombstone ou encerra preparação;409 se já processada. Apenas dono da origem pessoal |
| Detalhe pessoal | `pode_solicitar`, `versao_compartilhamento`, `solicitacao_ativa`; cópia local só `mensagem_solicitacao`. Pagamento inclui boolean `derivado`, não ids da outra ponta |
| GET `/api/espacos/{id}/lancamentos/simples/?pagas=true` | `{abertas_qtd,pagas_mes_qtd,itens}`. Padrão abertas de todos meses por vencimento,id; pagas=true seleciona paga/confirmada por vencimento no mês civil atual. Sem paginação própria nesta projeção; contagens completas do visível. Item inclui instrumento/PDF/pode_pagar autorizados |

Nonce/hash/tombstone reais substituem nomes preliminares como chave_idempotencia e GET porid. DTO vem do schema/tipos gerados. Sem endpoint genérico de sincronização. ResultadoPDF do destino é minimizado, sem extração privada da origem.

## T10-A: coordenação antes de qualquer lock de domínio

Helper central do backend, barreiraPostgreSQL transacional global curta em namespace distinto dos mutexes operacionais. Nested calls reutilizam contexto. Ordem: coordenador; admins de todos grupos e membros em ordem global consistente; espaços pessoais; casas; recorrências/competências; contas; solicitação/par/marcas/documentos; eventos/notificações/entregas. Mutexnonce em posição fixa anterior às entidades protegidas. Sob barreira descobrir/reler fechamento completo antes de travar entidades; pré-leitura só localiza/autoriza entrada, sem revelar ponta invisível. Revalidar regras/ACL após locks e serializar resposta autorizada ainda protegida.

Inventário obrigatório: reservar/ativar/cancelar; pagar/anexar/undo07; editar/cancelar04; bulk/modelo/geração08; papel/saída/remoção/RN32/casa; vínculo/substituiçãoPDF06; detalhe/documento/comprovante com locks; central/materialização/consumo09 e fases curtas de reservar/iniciar entrega com domínio. Finalização de transporte só operacional não começa a adquirir domínio depois de entrega/filho. Delete entra antesCollector/guardas/sinais, incluindoModel.delete/QuerySet.delete/admin suportados; integração de integridade10, sem entregarLGPD11 ou apagar dados reais.

Não inserir barreira só dentro deconta_travada, histórico ou hook de segunda ponta. Extrair primitivas07 que operam em contexto já coordenado. Barreira acaba no commit externo antesS3/parser/SMTP/push/HTTP. Advisory transacional deatomic interno não se libera antes doatomic externo; fases operacionais precisam ser realmente isoladas. Custo de contenção global não medido, avaliação11; evolução preserva invariantes.

## T10-B/C: PDF, fases e limpeza

1. Reserva revalida documento publicado/imutável e versão sob domínio, prepara operações necessárias e adquire pin com **try-lock** do objeto. Se ocupado, rollback integral/retrySQL curto limitado, sem esperar redeS3 ou retornar202 sem pin. Nenhuma nova trava de domínio depois do mutex operacional. Pin e reserva commitados juntos antes202; referência independe de linhaDocumento/usuário/origem.
2. Worker inicia faseSQL curta coordenada: valida reserva e grava token/lease, destinoUUID novo por tentativa e intençãowriter durável anterior aoPUT. Sai de todas travas de domínio.
3. GETfonte **fora do mutex da fonte**, usando pin+imutabilidade/limites; não travar fonte e destino juntos. PUT/verificação sob somente mutex operacional do destino e capacidade vigente. SHA/tamanho conferem bytes realmente armazenados, semETag presumido; nome retornado porstorage.save precisa corresponder à chave exclusiva.
4. Encerra mutex/transação operacional por inteiro; nova fase coordenada revalida token/estado/ACL, publica conta/documento/vínculo/evento duravelmente e só depois libera pin. Original viva paga/cancelada revoga reserva; exclusão física pode concluir snapshot já aceito com autorNULL e pagador/audiência atuais válidos, sem recriar pessoal. Perda comum de papel de solicitante vivo impede ativação.
5. Cleanup pré-lê identidade, toma mutex e reconsulta intenção/referências/pins/writers, sem coordenador/rowlock de domínio ou intenção duranteS3. Finaliza geração observada porCAS curto; upsert renova intenção sem esperar mutex com domínio travado. Protegida permanece pendente/reagendável. Token verifica antesPUT sob mutex comum; lease expirado não prova fim deupload. ErroS3 ambíguo mantém reconciliação/intenção/tombstone contra objeto tardio.

Identidade efetiva do mutex é comum a writer06/pin/cleanup; helpers compartilhados07–09 não mudam unilateralmente. Intenção/writer independentes deCASCADE sobrevivem crashpósPUT. Worker antigo nunca publica/apaga tentativa atual. Fonte só perdepin após destino durável ou abandono seguro; exclusão pessoal11 preserva objeto próprio legítimo do grupo. URLs privadas curtas seguem06/07, nunca assinatura da fonte ao destinatário.

## T10-D/E: eventos eUI

Pagamento cria marcas/eventos por marca e causa compartilhada atomicamente; original ficaPaga, comprovante só grupo. Undo exato reabre par seRN16/RN32 permitem; conflito409 integral. Pagar/cancelar original aberta encerra reserva/cópia aberta, inclusive capacidadeRN20 após saída sem leitura extra. Cancelar cópia deixa original pendente; undo manual não ressuscita. Guardas financeiras valem também embulk08/vínculoPDF, no-op permitido.

09 comunica por causa canônica/destinatário, contexto escolhido atomicamente com par completo: pessoal existente/autorizado preferido, senão grupo autorizado. Constraint de causa/destinatário e entregas poraviso/canal/filho evita duplicação independente da ordem dosworkers; preserva os doisEventosPagamento/consumo. Sem fallback tardio que ressuscite aviso revogado. EventoSolicitacao separado só na ativação; perda relevante revoga terminalmente antes de reentrada/polling. Transporte fora da barreira.

Frontend usa mesmo nonce/hash no retry e resolve operação anterior antes de mudar corpo/chave; reload recupera origem própria+nonce ou abandona comtombstone. Corpo financeiro confirmado só em memória; armazenamento local somente marcador opaco porusuário/origem, sem mensagem/valor/código/PDF. Troca de sessão reautoriza recuperação e limpaUI. Q10-11–14 preservados: shellpróprio somente modo simples comGrupos/logout real, contagens reais completas/NULL, grupo explícito e audiência deduplicada,202preparando distinto de sucesso, fechar não cancela e Cancelar preparação separado. Mesmo app/API/ACL/componentes07, semPerfil novo ou frame inventado. Capturas atuais são draft; comparação390×844/1440×900 futura obrigatória.

Provas futuras: duas conexõesPostgreSQL com barreiras; reservaHTTP versusGET/cleanup sem esperarI/O; pinrollback/CASCADE antesworker; crashpósPUT/token tardio/CASgeração/retornoS3ambíguo; eventos em ordem inversa; respostaPOST perdida/reload/POSTtardio apóstombstone; CAs01–14 e checks finais reais. Nenhuma dessas provas10 foi declarada executada nesta abertura.
