# Silo na VPS pelo Coolify

> **Contém:** configuração do armazenamento remoto autorizado pelo dono, correção do proxy, operação e verificações pendentes.
> **Origem:** pedido explícito no chat em 16/11/2026 para configurar o Silo pelo MCP do Coolify; Compose aplicado e verificações HTTP/TLS relatados pelo orquestrador.

Esta instalação é independente do laboratório da Etapa 11 e do S3 de desenvolvimento. A autorização cobre o armazenamento Silo; não equivale a deploy da aplicação Varal nem a conclusão dos critérios da etapa. O [ADR 0002](adr/0002-armazenamento-s3-local.md) continua descrevendo o armazenamento local.

## Identificação

| Item | Valor |
| --- | --- |
| Projeto Coolify | `Silo` — `tfm66xpdqaadkbncvaied6vj` |
| Ambiente | `production` |
| Servidor | `VPS` — `bg4nlylaxjqyw9izakbwaqfy` |
| Serviço | `wtowjxrirnltc2qcfwrlr5zp` |
| Componente | `silo` — `rm9ohvt4tya9ocsjyxeub497` |
| Imagem fixada | `pgsty/silo:RELEASE.2026-11-12T00-00-00Z` |
| Console | `https://silo-admin.codehub.systems` → porta interna `9001` |
| API S3 | `https://arquivos.codehub.systems` → porta interna `9000` |
| Rede do proxy | rede externa Docker `coolify` |
| Dados | volume externo Docker `varal-silo-data` → `/data` |
| Bucket do Varal | `varal-arquivos`, privado |

O [Compose versionado](../../infra/silo/compose.coolify.yml) contém a configuração reproduzível sem credenciais. Não publica portas do Silo no host. O proxy existente termina HTTPS e encaminha cada domínio à porta interna correspondente.

## Instalação e configuração

1. Na VPS selecionada, criar o volume apenas se ele ainda não existir: `docker volume create varal-silo-data`. Conferir o volume com `docker volume inspect varal-silo-data` antes do primeiro deploy. Não remover ou substituir um volume existente que contenha arquivos.
2. Apontar os registros DNS `silo-admin.codehub.systems` e `arquivos.codehub.systems` para a VPS.
3. No projeto Silo/production do Coolify, criar ou editar o recurso Docker Compose e usar o Compose versionado. Manter o nome do componente `silo`, o volume externo e a rede `coolify`.
4. Configurar no recurso `SILO_ADMIN_USER`, `SILO_ADMIN_PASSWORD` e `SILO_CONSOLE_URL`. Esta última vale `https://silo-admin.codehub.systems`. Os valores secretos ficam no Coolify; não entram no Compose, documentação ou histórico Git.
5. Configurar os dois domínios no componente, associando console à porta `9001` e API à `9000`. Reaplicar somente o serviço Silo pelo Coolify e acompanhar sua saúde.
6. Criar o bucket privado e uma credencial de runtime restrita a ele. A chave administrativa não deve ser usada pela API/worker do Varal. O estado desta validação está na tabela abaixo.

O usuário administrativo do Silo e a credencial de runtime do Varal têm funções diferentes. A criação/configuração inicial do bucket requer administração separada. A credencial de runtime deve permitir apenas as operações de objetos e de consulta do bucket necessárias ao aplicativo, sem administração do servidor ou alteração das políticas de acesso.

O comando atual `preparar_storage` da aplicação pode criar o bucket (`CreateBucket`) e sempre aplica ACL privada (`PutBucketAcl`). A credencial restrita de runtime não recebe essas permissões. No futuro deploy do Varal, executar esse bootstrap com uma credencial administrativa separada, ou pré-provisionar o bucket e ajustar/omitir a etapa administrativa no caminho de inicialização do aplicativo. Apenas criar o bucket previamente não permite executar o comando atual com a chave restrita, pois ele ainda chama `PutBucketAcl`. A aplicação Varal ainda não foi implantada nesta VPS por este procedimento.

As credenciais remotas de runtime estão mantidas no `infra/.env` não versionado sob o prefixo `SILO_PROD_*`, separado das configurações locais de desenvolvimento. Esse prefixo é um inventário de configuração remota: não muda sozinho o destino utilizado pelo Django. No deploy futuro da aplicação, o operador fará o mapeamento para `S3_ENDPOINT_URL`, `S3_PUBLIC_ENDPOINT_URL`, `S3_BUCKET_NAME`, `S3_REGION_NAME`, `AWS_ACCESS_KEY_ID` e `AWS_SECRET_ACCESS_KEY` da API e dos workers. Não colocar essas credenciais no frontend.

## Correção do 503

O Silo estava `running:healthy`, mas ambos os domínios devolviam HTTP 503 e HTTPS apresentava certificado padrão autoassinado. A definição gerada continha somente labels `coolify.*`, sem as rotas Traefik do console e da API.

Atualizar as URLs pela API do Coolify e reaplicar/reprocessar o Compose não gerou as rotas nesta instalação. A correção aplicada no próprio recurso foi:

- declarar labels Traefik explícitos para os dois hosts e portas;
- usar os entrypoints existentes `http` e `https`, com redirecionamento HTTP → HTTPS;
- usar o resolver existente `letsencrypt`;
- conectar o container à rede externa `coolify` e indicar essa rede ao Traefik;
- desabilitar access logs e tracing nos quatro routers próprios do Silo, para não registrar URLs assinadas no proxy;
- preservar volume, imagem e credenciais existentes.

O proxy global e outros serviços não foram reiniciados para essa correção. A configuração de observabilidade é específica dos routers `varal-silo-console`, `varal-silo-console-http`, `varal-silo-s3` e `varal-silo-s3-http`; não altera a observabilidade global de outros recursos. As rotas estão no Compose para sobreviverem a novas recriações do recurso; editar apenas um domínio na interface sem atualizar os labels pode produzir divergência.

## Verificação

| Verificação | Estado registrado |
| --- | --- |
| Console por HTTPS | HTTP 200 com certificado validado pelo cliente, após a correção |
| Login e sessão do console | Login HTTP 204, consulta de sessão HTTP 200 e cookie com `Secure=true` e `HttpOnly=true` |
| API S3 `/minio/health/ready` | HTTP 200 com certificado validado pelo cliente, após a correção |
| Volume externo | Referência `varal-silo-data:/data` preservada na definição gerada |
| Bucket `varal-arquivos` | Criado, privado; operações de runtime e negação de acesso anônimo comprovadas |
| Credencial de runtime | Criada pelo console; credenciais efetivas salvas em `infra/.env`, sem valores versionados |
| Limite da credencial ao bucket | `ListBuckets` HTTP 200 lista somente `varal-arquivos`; `GetBucketAcl`, `GetBucketPolicy` e `GetObject` em outro bucket devolvem HTTP 403 |
| PUT/GET e integridade de boleto/comprovante sintéticos | Passaram nos prefixos `boletos/` e `comprovantes/`, com SHA-256 idêntico no download |
| Acesso anônimo negado | GET sem assinatura devolveu HTTP 403 |
| URL assinada de 60 s e expiração real | Download autorizado antes do prazo; HTTP 403 após o prazo real |
| Persistência de objeto após reinício do Silo | Reinício real confirmado por logs MCP; ambos os objetos permaneceram legíveis com SHA-256 idêntico |
| Limpeza dos arquivos de teste | `DeleteObject` removeu somente os dois objetos sintéticos criados para a verificação |
| Backup automático e restauração na VPS | Backup local diário configurado; recuperação de arquivos e permissões comprovada em volume novo isolado. [Procedimento e limites](silo-backup-recuperacao.md) |

As operações de provisionamento e verificação final terminaram com exit 0. O startup do reinício observado pelo MCP ocorreu em `2026-11-17T00:47:13.863844960Z` (16/11/2026 em America/Fortaleza). Os testes de persistência foram executados depois desse marco. O resumo sem segredos, sem URLs assinadas e sem identificadores de objetos de teste está na [evidência sanitizada](../etapas/11-acabamento-deploy/evidencias/silo-coolify-2026-11-16.json), consolidada pelo orquestrador. Este registro atribui as execuções remotas ao orquestrador; o agente documental validou somente a configuração versionada.

Consultas públicas repetíveis, sem credenciais e sem ignorar TLS:

```sh
curl --fail --show-error --output /dev/null https://silo-admin.codehub.systems/
curl --fail --show-error https://arquivos.codehub.systems/minio/health/ready
```

Sucesso no endpoint de saúde não substitui upload/download autenticados, teste de assinatura, conferência de hash ou prova de recuperação. Não publicar URLs assinadas, cookies, senhas ou chaves nos artefatos das verificações.

## Atualização e recuperação

Para atualizar, revisar a release, obter um backup consistente e testar a restauração antes de alterar a tag fixada no Compose. Aplicar a atualização no recurso Silo, conferir o volume externo e repetir HTTP/TLS e I/O autenticado. Preservar o nome do volume e o ponto `/data`; não copiar arquivos diretamente sobre uma instância ativa nem executar limpeza de volumes para resolver problemas de domínio.

Uma recriação do container deve reutilizar o volume externo. Isso é persistência, não backup. Por pedido posterior expresso do dono, o [backup local diário e a recuperação isolada](silo-backup-recuperacao.md) foram configurados e testados na VPS. A prova usa um arquivo real do volume e uma instância separada, sem substituir o primário; não inclui PostgreSQL ou journal do futuro app nem recebe por herança o aceite do laboratório da Etapa 11.

## Capacidade e limites

O snapshot fornecido pelo dono registra disco de 96 GB, 65 GB disponíveis, memória total de 7,8 GiB e 3,6 GiB disponíveis naquele momento. A VPS também executa outras aplicações. Esses números são uma observação pontual, não uma reserva ou uma prova de capacidade do conjunto Varal/Silo.

Há uma única VPS e um único disco visível. Esta topologia não oferece redundância contra falha do disco ou perda completa do servidor. Backups mantidos nesse mesmo local podem ajudar em recuperação lógica, mas compartilham o risco de perda da VPS. Crescimento deve considerar espaço de objetos, banco, imagens Docker, logs e backups. A [retenção local do Silo](silo-backup-recuperacao.md) está configurada; acompanhar espaço livre e alertas continua necessário, pois os limites de retenção não são uma quota rígida nem reservam espaço para a próxima cópia.

Não há aprovação de produção resiliente, disponibilidade, perda zero, RPO/RTO ou encerramento de CA16/CA18 por esta instalação. A implantação da aplicação e as demais pendências da Etapa 11 continuam no [estado do projeto](../PROGRESSO.md) e no [relatório da etapa](../etapas/11-acabamento-deploy/relatorio.md).
