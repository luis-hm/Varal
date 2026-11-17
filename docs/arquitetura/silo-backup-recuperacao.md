# Backup local e recuperação do Silo

> **Contém:** configuração do backup local do armazenamento remoto, restauração isolada comprovada e encerramento dos recursos temporários.
> **Origem:** pedido explícito do dono em 16/11/2026 para criar backup e testar a recuperação antes de conectar o Varal. Operações remotas executadas pelo orquestrador via Coolify/MCP e API; este documento não atribui ao agente documental execução remota própria.

Este procedimento complementa a [instalação do Silo](silo-coolify.md). Usa a mesma VPS por restrição de orçamento. Não modifica o S3 de desenvolvimento, não implanta a aplicação Varal e não representa aprovação de CA16/CA18 ou recuperação integrada do aplicativo.

## Referência de backup no Coolify

O volume externo `varal-silo-data`, usado pelo Silo em `/data`, não aparecia no inventário de storage do serviço original. A API de criação de volume para um serviço adiciona um prefixo ao nome, e os registros de serviço não permitem depois editar esse nome. Não foi usado esse caminho para evitar qualquer troca do volume primário.

Foi criada uma **Application de metadados separada**, sem domínio e nunca implantada. Seu storage foi ajustado somente no banco de configuração do Coolify para referenciar o nome exato do volume existente. A definição e o volume do Silo primário foram preservados.

| Item | Valor |
| --- | --- |
| Projeto/ambiente | `Silo` / `production` |
| Application de referência | `silo-backups-nao-implantar` — `3j1xpkufs4zweebhykkmuqpo` |
| Storage de referência | `k8chl2rghzvg3d0mdcpqjkag` |
| Nome exato do volume existente | `varal-silo-data` |
| Mount path registrado | `/data` |
| Schedule | `fj05k9m2fnixytakexpw6irt` |

O [Dockerfile da referência](../../infra/silo/backup-reference.Dockerfile) usa `FROM scratch` e aponta para um executável inexistente. É uma barreira contra execução acidental, não um container de trabalho. O backup nativo é executado pelo Coolify e não depende dessa Application estar rodando.

**Não clicar em Deploy nessa Application. Não excluí-la com `delete_volumes=true` e não apagar seu storage ou schedule para organizar o painel.** Seu registro aponta para o volume real; excluir o schedule também pode excluir os arquivos de backup associados. Alterações de nome, destino, servidor ou storage exigem conferir novamente a referência antes de executar qualquer backup.

## Agenda, consistência e retenção

O [payload de configuração](../../infra/silo/backup-schedule.json) registra os valores aplicados:

| Configuração | Valor |
| --- | --- |
| Frequência | `0 6 * * *`, fuso do servidor conferido como UTC |
| Horário em America/Fortaleza | Todos os dias às 03:00 |
| Parar containers durante o arquivo | `stop_during_backup=true` |
| Retenção por quantidade | Até 7 backups locais |
| Retenção por idade | Até 7 dias |
| Retenção por espaço | 10 GiB no cálculo atual do Coolify |
| Timeout | 600 segundos |
| Aviso de ausência de execução | 1 dia, conforme configuração do schedule e canais disponíveis do Coolify |
| Cópia externa/S3 | Desativada; backup somente local |

O job nativo encontra os containers que usam o mesmo volume, interrompe-os durante a criação do arquivo e tenta retomá-los mesmo em falha. Isso causa indisponibilidade temporária do Silo durante o backup. O arquivo inclui objetos e metadados internos, inclusive `.minio.sys`; não é apenas uma cópia dos PDFs visíveis.

Os limites de retenção atuam sobre backups bem-sucedidos. No algoritmo atual, o limite de espaço pode preservar um único backup mais novo mesmo se ele ultrapassar o valor configurado; não é uma quota rígida do disco nem uma reserva prévia de espaço. Um novo arquivo também precisa de espaço antes da limpeza dos anteriores. Monitorar espaço livre continua necessário.

## Arquivos e proteção local

Diretório escolhido da primeira execução:

```text
/data/coolify/backups/volumes/root-team-0/k8chl2rghzvg3d0mdcpqjkag/
```

Primeiro arquivo examinado:

```text
volume-varal-silo-data-1794878142.tar.gz
```

| Propriedade | Resultado observado |
| --- | --- |
| Tamanho | 15.772 bytes |
| SHA-256 | `c292039be0166505f1ebc6349b6cdd39290f4302f7665f69858f4e6d807c9b21` |
| Permissão do diretório | `0700`, conferida pelo inspector |
| Permissão do primeiro arquivo | `0600`, conferida depois do ajuste |
| Criptografia do arquivo | **Não criptografado**; arquivo gzip/tar |

O job nativo pode criar os arquivos seguintes com modo `0644`; o diretório `0700` restringe o acesso local a eles. Se o diretório for removido/recriado ou mudar de proprietário, conferir novamente as permissões antes de confiar nos próximos arquivos. A proteção do diretório não equivale a criptografia. O conteúdo interno do Silo inclui informações de autenticação/permissões e deve ser tratado como confidencial.

Depois de remover os dois objetos próprios do exercício, foi produzido um segundo arquivo do estado atual da origem, com zero objetos lógicos:

| Propriedade da segunda cópia | Resultado observado |
| --- | --- |
| Nome | `volume-varal-silo-data-1794879322.tar.gz` |
| Tamanho | 17.587 bytes |
| SHA-256 | `b33ce1dad73a810708bfbab2d728e3ccf5296bcdecfadb7a7de43dc3dbb03b5b` |
| Permissões após ajuste | Diretório `0700`; os dois arquivos `0600` |
| Arquivos preservados | Duas cópias, incluindo a primeira usada na restauração |

O inspector confirmou que o diretório manteve `0700` na segunda execução; antes do ajuste, a primeira cópia estava em `0600` e a nova em `0644`. Ambas ficaram em `0600`, e o hash da primeira permaneceu igual. A segunda cópia teve presença, tamanho e hash conferidos; não foi restaurada separadamente. A prova de restauração descrita abaixo usa a primeira cópia produzida pelo mesmo mecanismo.

As credenciais administrativas necessárias à recuperação estão no `infra/.env` ignorado pelo Git, sob `SILO_BACKUP_ADMIN_USER` e `SILO_BACKUP_ADMIN_PASSWORD`, separadas da chave restrita `SILO_PROD_*`. O arquivo local está restrito ao proprietário. Essa configuração administrativa fica fora do arquivo de backup do volume e deve ser preservada separadamente para uma recuperação completa do serviço. Não colocar senhas, cookies, chaves ou URLs assinadas no runbook, Compose, comandos persistidos ou evidências.

## Exercício de restauração isolada

Foram criados somente dois objetos sintéticos de teste na origem: um PDF de 1.437 bytes e um PNG de 102 bytes, nos prefixos `boletos/` e `comprovantes/`. Nenhum documento real de cliente foi usado. Após o backup, foi preparado um volume novo para restaurar o arquivo, preservando o volume original e o arquivo de backup.

| Item do exercício | Valor |
| --- | --- |
| Serviço temporário | `95a8ztfrs3gun4d5cktwd1mr` |
| Componente init | `9hchc7qdvyb7gvuvaizgheoo` |
| Componente clone | `mgznbicjv3fnsty33kb7kqz4` |
| Volume novo | `varal-silo-restore-20261116-6923a0e5` |
| Imagem do clone | `pgsty/silo:RELEASE.2026-11-12T00-00-00Z` |
| Rede efetiva dos componentes | `network_mode: none` |
| Exposição | Sem domínio, rede Docker ou porta publicada no host |

O [template de recuperação](../../infra/silo/compose.restore.yml) e o [script](../../infra/silo/restore-archive.sh) documentam a lógica. Para este exercício, o orquestrador incorporou o script ao comando do init no Coolify e usou `network_mode: none` nos dois componentes. A validação por `mcli` ocorre dentro do clone, por tarefa manual do Coolify; não é necessário expor o clone para a rede.

O Compose **gerado** foi conferido antes de iniciar: backup montado somente leitura e destino apontando exclusivamente para o volume novo. Essa conferência não foi um `docker inspect` direto executado pelo orquestrador. O init exige filename e SHA-256 explícitos, rejeita destino não vazio, links e caminhos inseguros no tar antes de escrever, e não usa seleção silenciosa de `latest`. O clone depende do init terminar com exit 0; o clone iniciou após essa dependência. Não houve leitura de logs do init já parado pelo MCP, que não permite essa consulta.

Marcos observados nos logs, todos em UTC de 17/11/2026 (ainda 16/11 em Fortaleza):

- Origem recebeu parada às `01:15:44.039681612Z` e iniciou novamente às `01:15:46.066636513Z`.
- Clone restaurado iniciou às `01:24:15.948190965Z`.
- A chave de runtime do Varal autenticou por alias `mcli` no clone, em tarefa manual com resultado de sucesso.

A primeira tentativa de cadastrar uma tarefa com comando multilinha de 2.411 caracteres recebeu `ServerError`, sem criação. Uma tarefa curta foi criada e executada; não foi atribuída causa exata à rejeição anterior. A tarefa manual `owe9ff9rjbeldq4bv7wcldy5` permanece desativada, sem agenda automática de testes. O orquestrador executou a validação em comandos curtos com `mcli` dentro do clone; oito execuções de tarefas tiveram status `success` consultado pela API. Esse status pertence às tarefas de validação, sem atribuí-lo à execução nativa do backup de volume.

| Objeto sintético restaurado | Bytes | MIME | SHA-256 conferido com a origem |
| --- | --- | --- | --- |
| PDF | 1.437 | `application/pdf` | `61992bc779e3ee532dac92b9b0bf0f916a7068aa9cfb8ac98f4c7ed2e213498a` |
| PNG | 102 | `image/png` | `5e89762d4d162eea716befa4c8d1d8afd3e37933d9126557f75f0a87aeccf6f9` |

Os dois objetos preservaram `Cache-Control: private, no-store` e o metadado `purpose`. O GET anônimo retornou `403` para ambos. A chave restrita restaurada recebeu `403` em `GetBucketACL` assinado com SigV4 e no acesso a outro bucket. A origem manteve os mesmos hashes depois da restauração. Em seguida, foram removidos somente os dois objetos próprios do exercício: a contagem do bucket ativo voltou a zero, igual ao estado anterior ao teste. O endpoint de prontidão e o painel administrativo da origem responderam HTTPS `200`, com validação TLS.

O agente DevOps também executou 15 casos locais positivos e negativos do script de extração, usando dados sintéticos e diretórios temporários próprios: restauração válida; travessia, caminho absoluto, links, dispositivo, duplicidade e conflito de caminhos; destino não vazio; hash inválido; gzip corrompido; arquivo vazio; nome de volume inseguro; limites de membros e tamanho. Todos passaram. Esses testes locais não foram execuções na VPS.

| Verificação | Estado deste checkpoint |
| --- | --- |
| Schedule nativo configurado e habilitado | Confirmado pela resposta de configuração |
| Primeiro backup solicitado | Resposta de enfileiramento recebida |
| Arquivo nativo localizado e hash/tamanho conferidos | Confirmado pelo inspector somente leitura |
| Permissões locais do primeiro backup | Diretório `0700`, arquivo `0600`; hash preservado |
| Parada/retomada da origem | Confirmadas pelos logs |
| Inicialização do clone após init bem-sucedido | Confirmada pelo início do clone |
| Credencial de runtime preservada no clone | Autenticação `mcli` passou |
| SHA dos dois objetos restaurados | Iguais aos originais; PDF e PNG lidos com a chave de runtime |
| Metadados dos objetos | Tamanho, MIME, Cache-Control e `purpose` preservados |
| Acesso anônimo negado no clone | GET retornou `403` para os dois objetos |
| Recusa de ACL/outro bucket pela chave restrita | Ambas as requisições retornaram `403` |
| Limpeza dos dois objetos próprios na origem | Concluída; bucket ativo com zero objetos, igual à contagem inicial |
| Disponibilidade da origem após o exercício | Prontidão e painel HTTPS `200`, TLS validado |
| Novo backup do estado atual, sem objetos de teste | Segundo arquivo real conferido por nome, tamanho e SHA-256; sem restauração separada |
| Parada dos helpers temporários | Ambos confirmados como `exited` pelo MCP |
| Estado final do Silo primário | `running:healthy`; prontidão e painel HTTPS `200`, TLS validado |

O resumo sanitizado está em [silo-backup-recuperacao-2026-11-16.json](../etapas/11-acabamento-deploy/evidencias/silo-backup-recuperacao-2026-11-16.json), sem credenciais ou chaves dos objetos. A API pública atual não oferece consulta das execuções de backup de **volume**; os endpoints de execuções de backup de banco são de outra funcionalidade. Portanto a resposta `queued` não foi apresentada como `Success` no banco do Coolify. A prova operacional usa o arquivo real, seus bytes/hash, os logs e os resultados consultados das tarefas de validação do clone.

O recorte autorizado de backup local e teste de recuperação do Silo foi concluído. Os helpers temporários foram parados, o volume original foi preservado, e nenhum dos dois arquivos de backup foi apagado. A Application de referência permanece somente como metadados e não deve ser implantada. A conclusão se limita ao armazenamento: permanecem as restrições de disco único, arquivo sem criptografia e ausência de recuperação integrada do Varal, sem aprovação de CA16/CA18.

## Repetir a recuperação

1. Conferir o schedule e o último arquivo disponível. Não iniciar a recuperação a partir de um nome inferido ou arquivo ainda em gravação.
2. Escolher um filename exato e obter seu SHA-256; montar somente o diretório necessário como `/backup`, somente leitura.
3. Provisionar um volume vazio e novo, com prefixo `varal-silo-restore-`. Nunca usar `varal-silo-data` como destino. Conferir o Compose gerado antes de executar.
4. Fornecer o filename, hash esperado, nome do volume e credenciais administrativas originais por variáveis secretas administradas. Não imprimir seus valores.
5. Executar o init e permitir o clone somente após sucesso. Se o init falhar depois de escrever parte do destino, preservar o diagnóstico e usar outro volume novo; não apagar arquivos da origem para repetir.
6. Validar objetos, metadados e permissões dentro do clone. O acesso do `mcli` e o comportamento da chave restrita precisam funcionar com os dados restaurados, sem recriar a chave para esconder uma falha de recuperação.
7. Parar os recursos temporários depois da prova. Remover somente objetos sintéticos identificados como próprios na origem. A retenção do volume recuperado e dos arquivos de backup deve ser uma ação explícita; não limpar volumes indiscriminadamente.

## Limites

- As cópias estão na mesma VPS e no mesmo disco físico visível. Protegem contra alguns erros lógicos, mas podem desaparecer junto com o servidor ou disco. Não há promessa de perda zero ou alta disponibilidade.
- O arquivo não possui criptografia adicional. As permissões locais e o acesso administrativo do Coolify são sua proteção nesta configuração; uma cópia externa futura precisará de tratamento adequado.
- Este backup cobre o volume do Silo e seus metadados internos. O banco PostgreSQL, o journal de exclusões, as filas e a configuração completa do aplicativo Varal não estão incluídos. Ainda não há um ponto de recuperação consistente do aplicativo inteiro.
- O exercício com dois objetos sintéticos não mede tempo de recuperação de um volume cheio. A janela observada de parada/retomada não é uma garantia de RTO, e o cron diário não comprova por si só um RPO máximo.
- Não promover uma cópia antiga a armazenamento ativo de clientes sem reconciliar exclusões, permissões e demais estados atuais do aplicativo. O clone desta prova fica isolado; não assume o lugar do primário.

Referências técnicas primárias: [backup de mounts no Coolify](https://coolify.io/docs/core/persistent-storage/storage-mounts/backups), [implementação do job nativo](https://raw.githubusercontent.com/coollabsio/coolify/v4.x/app/Jobs/VolumeBackupJob.php), [rotas da API](https://raw.githubusercontent.com/coollabsio/coolify/v4.x/routes/api.php) e [tarefas de serviços](https://coolify.io/docs/services/operations/scheduled-tasks).
