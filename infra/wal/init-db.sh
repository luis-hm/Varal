#!/bin/sh
set -eu
# Separate migration owner and runtime role; the runtime role cannot disable triggers.
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set=app_user="$APP_USER" --set=app_password="$APP_PASSWORD" --set=migrate_user="$MIGRATE_USER" --set=migrate_password="$MIGRATE_PASSWORD" --set=db_name="$POSTGRES_DB" --set=ON_ERROR_STOP=1 <<'SQL'
CREATE ROLE :"migrate_user" LOGIN PASSWORD :'migrate_password';
CREATE ROLE :"app_user" LOGIN PASSWORD :'app_password';
ALTER DATABASE :"db_name" OWNER TO :"migrate_user";
ALTER SCHEMA public OWNER TO :"migrate_user";
GRANT USAGE ON SCHEMA public TO :"app_user";
ALTER DEFAULT PRIVILEGES FOR ROLE :"migrate_user" IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO :"app_user";
ALTER DEFAULT PRIVILEGES FOR ROLE :"migrate_user" IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO :"app_user";
GRANT EXECUTE ON FUNCTION pg_catalog.pg_switch_wal() TO :"app_user";
GRANT EXECUTE ON FUNCTION pg_catalog.pg_current_wal_insert_lsn() TO :"app_user";
GRANT EXECUTE ON FUNCTION pg_catalog.pg_walfile_name(pg_lsn) TO :"app_user";
SQL
# Bind this disposable spool to the actual PostgreSQL cluster, once, before archiving.
cluster_id=$(psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -t -A -v ON_ERROR_STOP=1 -c 'SELECT system_identifier::text FROM pg_control_system()')
case "$cluster_id" in *[!0-9]*|'') exit 1 ;; esac
if [ -e /varal/wal-spool/cluster.id ]; then
    [ "$(cat /varal/wal-spool/cluster.id)" = "$cluster_id" ] || exit 1
else
    umask 077
    printf '%s\n' "$cluster_id" > /varal/wal-spool/.cluster.id.tmp
    sync -f /varal/wal-spool/.cluster.id.tmp
    mv /varal/wal-spool/.cluster.id.tmp /varal/wal-spool/cluster.id
    sync -f /varal/wal-spool
fi
