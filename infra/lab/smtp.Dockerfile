FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b
RUN groupadd --gid 10002 capture && useradd --uid 10002 --gid 10002 --no-create-home --shell /usr/sbin/nologin capture
COPY --chown=10002:10002 smtp-starttls.py smtp-health.py /srv/
USER 10002:10002
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
CMD ["python", "/srv/smtp-starttls.py"]
