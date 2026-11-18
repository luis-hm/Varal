COMPOSE := docker compose -f infra/docker-compose.yml
# Run as the host user so generated files (migrations, openapi.yaml) are not owned by root.
RUN := $(COMPOSE) run --rm --user $$(id -u):$$(id -g)
API := $(RUN) --no-deps api
API_DB := $(RUN) api
# Fail fast on Node < 22 (CI reads web/.nvmrc); v20 hides errors that only show up in CI.
NODE22 := @node -e 'process.exit(parseInt(process.versions.node) < 22 ? 1 : 0)' 2>/dev/null || { echo "Node 22+ required (found $$(node -v 2>/dev/null || echo none)). Run: cd web && nvm install && nvm use" >&2; exit 1; }

.PHONY: help env dev down test test-api test-web e2e lint types migrate seed limpar-dev codex-sync

help: ## List targets
	@grep -E '^[a-z0-9-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

env:
	@test -f infra/.env || cp infra/.env.example infra/.env

dev: env ## Start everything (api, worker, beat, postgres, redis, minio, web)
	$(COMPOSE) up --build -d
	@echo "web http://localhost:3000 · api http://localhost:8000/api/health/ · docs http://localhost:8000/api/docs/"

down: ## Stop everything
	$(COMPOSE) down

test: env ## Run all tests
	$(NODE22)
	$(MAKE) test-api
	$(MAKE) test-web

test-api: env
	$(API_DB) pytest -q

test-web:
	$(NODE22)
	cd web && npm test

e2e: env ## Run Playwright e2e with the real API (390x844 and 1440x900)
	$(NODE22)
	ACCOUNT_RATE_LIMIT_SIGNUP=1000/m/ip $(COMPOSE) -p varal -f infra/docker-compose.e2e.yml up --build -d api worker
	@attempt=0; until $(COMPOSE) -p varal exec -T api python -c 'from urllib.request import urlopen; urlopen("http://127.0.0.1:8000/api/health/", timeout=2)' >/dev/null 2>&1; do \
		attempt=$$((attempt + 1)); \
		if [ "$$attempt" -ge 60 ]; then echo "API healthcheck failed; inspect docker compose logs api" >&2; exit 1; fi; \
		sleep 1; \
	done
	@redis_id=$$($(COMPOSE) -p varal -f infra/docker-compose.e2e.yml ps -q redis-e2e); \
		test -n "$$redis_id" || { echo "Isolated E2E Redis missing" >&2; exit 1; }; \
		cd web && npx playwright install chromium && E2E_RN31_ISOLATED=1 E2E_RN31_REDIS_CONTAINER="$$redis_id" E2E_RN31_PROJECT=varal E2E_RN31_SERVICE=redis-e2e npm run e2e -- --workers=1

lint: env ## Lint and typecheck api and web
	$(NODE22)
	$(API) sh -c "ruff check . && ruff format --check ."
	cd web && npm run lint && npm run typecheck

types: env ## Regenerate api/openapi.yaml and web/src/types/api.ts
	$(NODE22)
	$(API) python manage.py export_schema --file openapi.yaml
	cd web && npm run types

migrate: env ## Create and apply migrations
	$(API_DB) sh -c "python manage.py makemigrations && python manage.py migrate"

seed: env ## Load development data
	$(API_DB) python manage.py seed

codex-sync: ## Regenerate Codex agents/skills from .claude (see AGENTS.md)
	sh infra/scripts/codex-sync.sh

limpar-dev: env ## Delete test leftovers from the dev DB (asks first; SIM=1 skips it)
	$(API_DB) python manage.py limpar_dev $(if $(SIM),--sim)
