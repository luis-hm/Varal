FROM ghcr.io/astral-sh/uv:0.13.7@sha256:96f40d3904aad8d0bd010539001d36c8e2188b981e1334471a90c4a1d93bb490 AS uv
FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b AS dependencies
COPY --from=uv /uv /bin/uv
ENV UV_PROJECT_ENVIRONMENT=/venv UV_LINK_MODE=copy
WORKDIR /app
COPY api/pyproject.toml api/uv.lock ./
RUN uv sync --frozen --no-dev

FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b
RUN groupadd --gid 10001 varal && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin varal && mkdir -p /varal/staging /varal/static /varal/lock /varal/beat && chown -R 10001:10001 /varal
ENV PATH="/venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY --from=dependencies /venv /venv
COPY --chown=10001:10001 api/ ./
COPY --chown=10001:10001 infra/deploy/gunicorn.conf.py infra/deploy/api-ready.py infra/deploy/migrate.py ./
USER 10001:10001
CMD ["gunicorn", "-c", "/app/gunicorn.conf.py", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
