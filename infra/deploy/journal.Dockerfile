FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b
RUN groupadd --gid 10001 journal && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin journal && mkdir -p /varal/journal /varal/checkpoint && chown -R 10001:10001 /varal
WORKDIR /srv/journal
COPY --chown=10001:10001 infra/journal/server.py ./
COPY --chown=10001:10001 infra/deploy/journal-init.py infra/deploy/journal-health.py ./
USER 10001:10001
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENTRYPOINT ["python", "server.py"]
