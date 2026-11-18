#!/bin/sh
# Daily encrypted pg_dump to S3 (ADR 0018). One object per weekday: 7 days kept, nothing deleted.
# Restore: docs/arquitetura/backup-restauracao.md
set -eu -o pipefail
arquivo=/tmp/varal-backup.enc
while :; do
    if [ -z "${BACKUP_PASSPHRASE:-}" ]; then
        echo "backup skipped: BACKUP_PASSPHRASE is not set" >&2
    else
        chave="backups/postgres/dia-$(date -u +%u).dump.enc"
        if pg_dump --format=custom --no-owner \
            | openssl enc -aes-256-cbc -pbkdf2 -salt -pass env:BACKUP_PASSPHRASE -out "$arquivo" \
            && curl --fail --silent --show-error --aws-sigv4 "aws:amz:${S3_REGION_NAME:-us-east-1}:s3" \
                --user "$AWS_ACCESS_KEY_ID:$AWS_SECRET_ACCESS_KEY" \
                --upload-file "$arquivo" "$S3_ENDPOINT_URL/$S3_BUCKET_NAME/$chave"; then
            echo "backup ok: $chave"
        else
            echo "backup failed; retrying in 1 hour" >&2
            rm -f "$arquivo"
            sleep 3600
            continue
        fi
        rm -f "$arquivo"
    fi
    sleep 86400
done
