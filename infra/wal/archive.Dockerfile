FROM ghcr.io/astral-sh/uv:0.13.7@sha256:96f40d3904aad8d0bd010539001d36c8e2188b981e1334471a90c4a1d93bb490 AS uv
FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b AS dependencies
COPY --from=uv /uv /bin/uv
ENV UV_PROJECT_ENVIRONMENT=/venv UV_LINK_MODE=copy
WORKDIR /app
COPY api/pyproject.toml api/uv.lock ./
RUN uv sync --frozen --no-dev
FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b
RUN groupadd --gid 70 wal && useradd --uid 70 --gid 70 --no-create-home --shell /usr/sbin/nologin wal && mkdir -p /varal/wal-spool /varal/wal-archive /varal/wal-acks /varal/wal-anchor && chown -R 70:70 /varal
ENV PATH="/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY --from=dependencies /venv /venv
COPY --chown=70:70 infra/wal/archive.py infra/wal/health.py infra/wal/verify.py infra/wal/export.py /srv/
USER 70:70
ENTRYPOINT ["python", "/srv/archive.py"]
