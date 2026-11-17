FROM node:22.23.5-alpine@sha256:1314fb30ec37592d5845e5a160d522c0e680972aa534549940b8d73bde88481a AS build
ENV NEXT_TELEMETRY_DISABLED=1 API_INTERNAL_URL=http://ssr:8080
WORKDIR /app
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
ARG VARAL_NEXT_BUNDLER=turbopack
ENV NODE_OPTIONS="--max-old-space-size=1536"
RUN case "$VARAL_NEXT_BUNDLER" in \
      turbopack) npm run build ;; \
      webpack) npm run build -- --webpack ;; \
      *) echo 'unsupported Next bundler' >&2; exit 1 ;; \
    esac && npm prune --omit=dev

FROM node:22.23.5-alpine@sha256:1314fb30ec37592d5845e5a160d522c0e680972aa534549940b8d73bde88481a
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 API_INTERNAL_URL=http://ssr:8080
WORKDIR /app
COPY --from=build --chown=node:node /app/package.json /app/package-lock.json ./
COPY --from=build --chown=node:node /app/node_modules ./node_modules
COPY --from=build --chown=node:node /app/.next ./.next
COPY --from=build --chown=node:node /app/public ./public
COPY --from=build --chown=node:node /app/next.config.ts ./next.config.ts
USER node
CMD ["./node_modules/.bin/next", "start", "--hostname", "0.0.0.0"]
