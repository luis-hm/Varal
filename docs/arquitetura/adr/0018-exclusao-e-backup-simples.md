# ADR 0018 — Exclusão de conta e backup sem journal

> **Contém:** como a exclusão de conta sobrevive a uma restauração, e o backup diário do PostgreSQL.
> **Origem:** pedido do dono em 18/11/2026 para enxugar a infraestrutura ("aplique os ajustes numa branch separada"). Substitui as partes de journal, WAL e laboratório da [ADR 0015](0015-exportacao-exclusao-e-prova-local.md).

- **Status:** aceita (18/11/2026, aprovada pelo dono no chat).

## Contexto

A Etapa 11 garantia RN30 ("conta excluída não volta") com um journal externo PREPARE/COMMIT, WAL cifrado com testemunha antes de cada envio, bootstrap de chaves e um laboratório de restauração. Isso somava 6 serviços a mais no deploy, cerca de 15 volumes, 7 Dockerfiles e dezenas de scripts. Mesmo assim, ainda não havia um backup diário do banco.

## Decisão

1. **Exclusão numa transação só:** barreira, prova de reautenticação, intenção, guardas RN04/RN32, consumo da intenção, `OperacaoExclusao` e `usuario.delete()`. Ou tudo acontece, ou nada.
2. **Registro fora do banco:** depois do commit, a task `publicar_exclusoes` grava `exclusoes/<operação>.json` no bucket privado. O registro tem só `owner_id` e a data. O beat repete a cada 60 s o que não foi publicado (`publicada_em` nulo).
3. **Backup:** o serviço `backup` faz `pg_dump` diário, cifrado com `BACKUP_PASSPHRASE` (AES-256, PBKDF2). Envia para `backups/postgres/dia-N.dump.enc`, onde N é o dia da semana. Isso dá 7 dias de retenção sem apagar nada.
4. **Restauração:** depois do `pg_restore`, rodar `manage.py reaplicar_exclusoes`. O comando apaga de novo toda conta que tem registro, com as mesmas guardas. Uma conta que esbarra numa guarda é listada e o comando falha até alguém resolver.
5. **Mantidos:** edge e ssr. Fazem a confiança de IP (RN31) e o `X-Forwarded-Proto` do SSR.

## O que se garante

- Uma exclusão confirmada chega ao bucket em segundos. Se o S3 estiver fora, chega quando ele voltar.
- Restaurar um dump mais antigo não traz de volta contas excluídas depois dele.
- Se o servidor for perdido de vez, o que foi feito desde o último dump se perde junto (RPO de 24 h). Isso vale para todos os dados, não só para exclusões.
- Os registros ficam no mesmo bucket dos arquivos. Quem tem a credencial S3 pode apagá-los. O journal assinado também não protegia contra root.

## Como desfazer

Voltar a usar o journal exige reverter este commit e a migração `privacidade.0009`. As contas excluídas nesse meio-tempo continuam nos registros do bucket.

[Runbook de backup e restauração](../backup-restauracao.md).
