# Backup e restauração

> **Contém:** onde ficam os backups do PostgreSQL e como restaurar sem trazer de volta contas excluídas.
> **Origem:** [ADR 0018](adr/0018-exclusao-e-backup-simples.md), `infra/postgres/backup.sh`.

## O que é salvo

| O quê | Onde | Quando |
| --- | --- | --- |
| `pg_dump` cifrado do banco | `s3://<bucket>/backups/postgres/dia-1..7.dump.enc` | Uma vez por dia (serviço `backup`); cada dia da semana sobrescreve o da semana anterior |
| Registro de cada conta excluída | `s3://<bucket>/exclusoes/<operação>.json` | Segundos depois da exclusão |
| PDFs e comprovantes | o próprio bucket | Backup do Silo ([silo-backup-recuperacao.md](silo-backup-recuperacao.md)) |

`BACKUP_PASSPHRASE` fica no Coolify **e** guardada fora dele. Sem ela nenhum dump restaura. Se a variável estiver vazia, o serviço só registra `backup skipped` no log.

## Restaurar

1. Parar `api`, `worker` e `beat` no Coolify. `postgres` continua no ar.
2. No container `backup`, que já tem as credenciais do banco (usuário de migração) e do S3, baixar, decifrar e restaurar o dia escolhido:

   ```sh
   docker exec <backup> sh -c 'set -e
     curl -fsS --aws-sigv4 "aws:amz:$S3_REGION_NAME:s3" --user "$AWS_ACCESS_KEY_ID:$AWS_SECRET_ACCESS_KEY" \
       "$S3_ENDPOINT_URL/$S3_BUCKET_NAME/backups/postgres/dia-3.dump.enc" \
       | openssl enc -d -aes-256-cbc -pbkdf2 -pass env:BACKUP_PASSPHRASE > /tmp/varal.dump
     pg_restore --clean --if-exists --no-owner -d "$PGDATABASE" /tmp/varal.dump
     rm /tmp/varal.dump'
   ```

3. Rodar o `migrate` (redeploy) e depois reaplicar as exclusões:

   ```sh
   docker exec <api> python manage.py reaplicar_exclusoes
   ```

   O comando diz quantas contas apagou de novo. Se uma conta esbarrar numa guarda (último admin, conta restrita sem quem veja), ele lista o UUID e termina com erro. Resolva no grupo e rode de novo; o comando pode rodar quantas vezes for preciso.
4. Subir `api`, `worker` e `beat`.

## Testar o backup

Restaurar num banco descartável pelo menos uma vez por mês e conferir se `reaplicar_exclusoes` roda.
