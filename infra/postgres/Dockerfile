# PostgreSQL with the role split (init-db.sh) and the daily backup (backup.sh, ADR 0018).
FROM postgres:17-alpine@sha256:e5d2edd28b1f8d40a0a6c0c9cdc545b19b56a0d5d88f94bc11a97d970d4700d0
RUN apk add --no-cache curl openssl
COPY --chmod=0555 init-db.sh /docker-entrypoint-initdb.d/10-varal-role.sh
COPY --chmod=0555 backup.sh /usr/local/bin/varal-backup
