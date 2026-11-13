COMPOSE := docker compose -f infra/docker-compose.yml
# Run as the host user so generated files (migrations, openapi.yaml) are not owned by root.
RUN := $(COMPOSE) run --rm --user $$(id -u):$$(id -g)
API := $(RUN) --no-deps api
API_DB := $(RUN) api

.PHONY: help env dev down test test-api test-web e2e lint types migrate seed

help: ## List targets
	@grep -E '^[a-z0-9-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

env:
	@test -f infra/.env || cp infra/.env.example infra/.env

dev: env ## Start everything (api, worker, beat, postgres, redis, minio, web)
	$(COMPOSE) up --build -d
	@echo "web http://localhost:3000 · api http://localhost:8000/api/health/ · docs http://localhost:8000/api/docs/"

down: ## Stop everything
	$(COMPOSE) down

test: test-api test-web ## Run all tests

test-api: env
	$(API_DB) pytest -q

test-web:
	cd web && npm test

e2e: ## Run Playwright e2e (web, 390x844 and 1440x900)
	cd web && npx playwright install chromium && npm run e2e

lint: env ## Lint and typecheck api and web
	$(API) sh -c "ruff check . && ruff format --check ."
	cd web && npm run lint && npm run typecheck

types: env ## Regenerate api/openapi.yaml and web/src/types/api.ts
	$(API) python manage.py spectacular --file openapi.yaml --validate
	cd web && npm run types

migrate: env ## Create and apply migrations
	$(API_DB) sh -c "python manage.py makemigrations && python manage.py migrate"

seed: env ## Load development data
	$(API_DB) python manage.py seed
