#!/bin/sh
set -eu
# Keep existing development .env files usable, while permitting explicit endpoints.
export S3_ENDPOINT_URL="${S3_ENDPOINT_URL:-http://minio:9000}"
export S3_PUBLIC_ENDPOINT_URL="${S3_PUBLIC_ENDPOINT_URL:-http://localhost:9000}"
exec "$@"
