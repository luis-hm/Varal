# ADR0014 — Solicitação e sincronização privada entre contas

> **Contém:** decisões de solicitação/sincronização privada Q10-1–14 e protocolo técnico T10-A–E.
> **Origem:** autorização expressa do dono e Q10-1–14, com precisão da reserva/exclusão ratificada pelo orquestrador. Não é resposta literal do dono nem reexportação da origem.

**Estado:** aceito por delegação em16/11/2026 e integrado ao abrir10, após commit09 `4e04ddf`/merge local `56337ed`. Backend/PDF em implementação; nenhum teste10 declarado. Detalhes e reversão em [decisões10](../../etapas/10-solicitacao-modo-simples/decisoes.md).

## Contexto

CU10/RN20 criam cópia de pessoal no grupo e propagam pagamento/cancelamento, mas não definem todas as direções, audiência, edição, concorrência ou exclusão em voo. RN05 limita criação a membro/admin; RN01/02/06 preservam espaços e visibilidade. RN16 reserva undo a autor/admin visível. Arquivos são assíncronos/privados eRN30/11 deve apagar pessoal sem destruir evidência legítima do grupo.

## Decisão

1. Dono de pessoal pendente só solicita como admin/membro atual do grupo; pagador atual elegível. Cópia distinta inicialmente restrita ao solicitante+pagador, sem casa/recorrência/ACL pessoal. Confirmação explicita campos e arquivo inteiro/metadados compartilhados. Nunca expororigem_id/links/IDs de marcas pessoais no grupo, inclusive histórico/admin.
2. Uma solicitação viva por original, abrangendo preparação/ativa/quitada, com chave idempotente/hash e tombstone. Snapshot financeiro imutável; impedir alteração efetiva de valor/data/instrumento/PDF de ambos os lados enquanto vivo, inclusivebulk08. Dados/ACL locais não sincronizam.
3. Pagar cópia cria marca derivadaPaga de igual valor/data na original viva, com causa/alvos exatos e transação única. Comprovante continua só no grupo; anexo direto à marca derivada pessoal é recusado. Original excluída não é recriada.
4. Undo autorizado da cópia desfaz somente derivada exata ainda ativa; conflito/RN32 recusa tudo. Undo direto da derivada pessoal exige visão/RN16 atual na cópia. Autor-observador segue exceção restrita07, sem conceder novo acesso.
5. Pagar original manualmente cancela cópia aberta ou reserva e encerra. Cancelar original aberta faz o mesmo, mesmo após saída do grupo, como capacidadeRN20 estrita que não expõe destino. Cópia já paga/confirmada não é sobrescrita. Cancelar cópia deixa original pendente; undo manual pessoal posterior não reabre pedido.
6. Reserva aceita é autorização durável apenas do snapshot/destino/audiência inicial confirmados. Pin privado e independente da linha pessoal é persistido antes202; S3 só worker, destino próprio íntegro antes de liberar fonte/publicar conta pagável. Cancelar/pagar original viva revoga preparação. Excluir fisicamente original/usuário desacopla sincronização e pode concluir transferência já aceita, usando autorNULL e audiência/pagador atuais válidos. Perda comum de papel do solicitante vivo impede ativação; ausência de audiência nunca abre acesso ao admin.
7. Cleanup consulta referências/pins e capacidades de writers; intenção persistente apóscommit, chaves/tentativas imutáveis e recuperação impedem lateworker publicar ou apagar arquivo atual. ExclusãoRN30/11 preserva cópia e objeto do grupo e não apaga fonte ainda pinada antes de conclusão/abandono seguro. Isto é contrato explícito de dados/privacidade, sem conclusão jurídica.
8. EventoSolicitacao nasce na ativação para pagador inicial e usa09. Pagamentos do par conservam eventos por marca, ligados por causa;09 deduplica comunicação por causa/destinatário/canal e sempre autoriza o contexto escolhido. Modo simples reutiliza API/ACL/flags/arquivos/pagamentos, sem novos direitos.

## Consequências e reversão

Restringir criação/audiência reduz compartilhamento acidental, mas exige edição posterior para ampliar. Congelar cobrança impede correções rápidas sem encerrar/refazer. Undo pessoal sincronizado pode depender de resolução no grupo. Reserva durável retém fonte temporariamente e preserva conteúdo previamente compartilhado após exclusão pessoal; nunca preserva licença para alterar snapshot, destino ou recriar pessoal.

Reversão requer nova política e migração de relações/ledgers/objetos, preservando históricos e eventos consumidos. Conteúdo já compartilhado não é recolhível. Atualizar derivadosRN05/RN16/RN20, modelo, matriz e contratoRN30/11 junto da implementação; não editar especificação de origem. LeituraDoop e validação real permanecem obrigatórias; este ADR não implementa10/LGPD, não implementa Perfil nem autoriza deploy e não executa testes/serviços.


## Complemento de composição e estados — Q10-11–14

Após leitura atual12/M06/13/D05 pelo orquestrador e inspeção local das capturas pelo decisor (`/tmp/varal-doop10/LEITURA.md`), a delegação resolve o conflito da regra responsiva geral com13/D05: **somente o modo simples** usa cabeçalho próprio sem TabBar/SideNav, mantendo uma rota, API/ACL e componentes responsivos. Acrescentar Grupos e Sair da conta com navegação/auth existentes, sem Perfil novo. Os frames continuam draft; isto não aprova nem altera canvas/fonte.

Contagem e copy descrevem abertas visíveis, não capacidade de pagar: **N contas em aberto**, NULL **Valor a definir**, aguardando **Aguardando conferência**. Faixa de pagas inclui paga/confirmada visíveis por vencimento no mês atual e o explicita no texto; não concede ação sem flag. Pedido acomoda escolha explícita do grupo elegível, audiência inicial restrita e aviso do PDF inteiro. Preparação202 fica acompanhável no detalhe pessoal; fechar UI não cancela reserva aceita, cancelamento é explícito e sucesso depende de ativação, sem promessa de aviso entregue.

Trocas: menos uniformidade de shell e mais controles/texto que os frames, em favor de saída segura, contagem verdadeira e compartilhamento consciente. Reversão da apresentação exige nova decisão de tela, mas não migração; alterar semântica da reserva/audiência continua sujeito às consequências de dados já registradas. Ver detalhes/casos contra em Q10-11–14. P10 resolvida por delegação expressa para composição com componentes existentes na11; P11/destino permanece pendente e P6 externa. Nenhuma implementação/teste/serviço foi realizado.

## Complemento técnico ratificado — T10-A–E

Orquestrador ratificou a revisão `/tmp/varal-10-arquitetura.md`; detalhes operacionais/ownership e reversão nas [decisões10](../../etapas/10-solicitacao-modo-simples/decisoes.md). São escolhas técnicas dentro deQ10-1–14, sem regra de negócio nova ou implementação alegada.

- **T10-A:** único coordenador do backend, barreiraPostgreSQL global transacional curta em namespace próprio antes de qualquer trava de domínio; inclui leituras09, alterações04/07/08, saída/RN32, vínculoPDF e delete antesCollector/guardas. Descoberta completa sob barreira e hierarquia global determinística; não entrar tardiamente por helper de segunda ponta. Liberação no commit externo antesI/O. Contenção é custo assumido não medido; sharding futuro preserva invariantes.
- **T10-B:** reserva+pin independente deCASCADE antes202, try-lockHTTP com rollback/retrySQL limitado sem espera deS3. GETfonte imutável fora mutex, sob retenção do pin. FaseSQL de capacidade/intenção antecedePUT; cada tentativa tem destinoUUID novo. PUT/verificação somente sob mutex operacional do destino, fora locks de domínio, depois nova fase coordenada para publicação.
- **T10-C:** cleanup toma mutex antes de avaliar referências/pins/writers e não segura rowlock duranteS3. Intenção renovável por geração finaliza somente porCAS da versão observada; fonte protegida mantém pendência. Intenção dewriter anterior aoPUT, token sob mutex, digest/tamanho do destino real e reconciliação de respostas ambíguas impedem publicação/órfão tardios. Não considerar lease como prova de fim deupload nem mudar mutex compartilhado06–09 unilateralmente.
- **T10-D:** causa canônica escolhe contexto autorizado por destinatário atomicamente com par completo, pessoal preferido se existente/visível; senão grupo autorizado. Preserva ambosEventosPagamento/consumo, uma comunicação por causa/destinatário e entregas09 porcanal. Ordem de workers não muda resultado; sem fallback tardio após revogação.
- **T10-E:** recuperação por origem própria+nonce e abandono autenticado com tombstone inclusive anterior à criação. GET404 não eliminaPOST atrasado. Mesmo nonce/hash nos retries, chave nova só após resolver anterior; memória contém corpo confirmado e storage local somente marcador opaco por usuário/origem, sem snapshot financeiro.

Backend possui `solicitacoes`/coordenador/par/eventos/API e demais integrações; especialistaPDF apenasboletos/helpers/migrações/testesPDF, sem publicar domínio. Frontend aguarda schema/tipos gerados. Nenhum protocolo permite locks de domínio duranteS3/transporte ou uso da relação para ler ponta invisível. Q10-11–14 permanecem, incluindo exceção limitada do shell, contagens completas reais, seleção de grupo e202 sem sucesso antecipado.

Reversão técnica preserva ledgers, tokens/gerações, pins e causas já consumidas; conteúdo já compartilhado não se recolhe. Testes futuros de barreiras, S3/cleanup, tombstone e deduplicação precisam comprovar as invariantes; todas14CAs continuam não executadas. Etapa09 concluída e integrada em `56337ed`; este ADR está integrado na abertura10, sem resultado10 antecipado. P10 resolvida por delegação expressa para composiçãoPerfil11 com componentes existentes; P11/destino e P6 externa permanecem. Implementação10 em execução; esta atualização documental não executa testes/serviços, envio externo ou push.

## Implementação integrada — fotografia em validação

Código e tipos presentes, backend/frontend/boletos congelados paraQA. Contrato usa `nonce` e hash `versao_compartilhamento`; POST202 mesmo semPDF, recuperação/abandono por origem própria+nonce. Causa canônica09 preserva marcas/eventos. Projeção pessoal de marca e undo usa autorNULL/Sistema, sem ator do grupo no histórico; boolean público `derivado` é calculado, sem relação pessoal noDTO do grupo.

Cleanup de comprovantes07 também segue intenção versionada/CAS sem rowlock duranteS3, com tombstone incerto; `total_max_attempts=1` evita retry oculto (B10-pre1). Frontend mantém grupo consentido fixo diante de refetch (B10-final1). São precisões técnicas das decisões já delegadas, sem nova concessão de direitos. Segurança em leitura sem bloqueantes após correções, sem substituirQA.

[Relatório10 em validação](../../etapas/10-solicitacao-modo-simples/relatorio.md) atribui rodadas dirigidas/provaSilo/Postgres/Celery isolada, sem somar resultados ou declarar integral10. A prova não cobrePUT físico remoto tardio ouLGPD11. E2E/visual/checks finais pendentes;14CAs não encerrados. Sem push/deploy ou fechamento antecipado.
