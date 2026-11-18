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
SQL
