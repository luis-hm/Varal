FROM node:22.23.5-bookworm-slim@sha256:e9f565d32859f0cbfb52125eafe8be39390f24dac302dc3cdf566e8ba3ab21ee AS qa-deps
WORKDIR /qa
COPY web/package.json web/package-lock.json ./
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
RUN npm ci --no-audit --no-fund

FROM mcr.microsoft.com/playwright:v1.65.0-noble@sha256:9beb546099e11f52d62e505537914870e01a67e0e6b00ae41da4775324e73dbe
USER root
RUN apt-get update -qq && apt-get install -y --no-install-recommends 'libnss3-tools=2:3.98-1ubuntu0.3' && rm -rf /var/lib/apt/lists/*
COPY --from=qa-deps /usr/local/bin/node /usr/local/bin/node
COPY --from=qa-deps --chown=1001:1001 /qa/node_modules /opt/qa/node_modules
COPY --chmod=0555 infra/lab/browser-start.sh /usr/local/bin/varal-browser-start
USER 1001:1001
ENTRYPOINT ["/usr/local/bin/varal-browser-start"]
