FROM postgres:17-alpine@sha256:e5d2edd28b1f8d40a0a6c0c9cdc545b19b56a0d5d88f94bc11a97d970d4700d0
RUN mkdir -p /varal/wal-spool /varal/wal-acks && chown -R 70:70 /varal
COPY --chmod=0555 archive-command.sh /usr/local/bin/varal-archive-wal
COPY --chmod=0555 init-db.sh /docker-entrypoint-initdb.d/10-varal-role.sh
