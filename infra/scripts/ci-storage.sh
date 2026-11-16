#!/bin/sh
# Ephemeral CI-only S3. The credentials below match the workflow's non-secret test values.
set -eu
docker run -d --name varal-ci-storage -p 9000:9000 \
  -e MINIO_ROOT_USER=varal-ci -e MINIO_ROOT_PASSWORD=varal-ci-password \
  pgsty/silo:RELEASE.2026-11-12T00-00-00Z server /data >/dev/null
curl --fail --silent --show-error --retry 30 --retry-delay 1 --retry-connrefused \
  --retry-all-errors --retry-max-time 60 http://localhost:9000/minio/health/ready >/dev/null
