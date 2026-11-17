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

.PHONY: lab11-journal-test
lab11-journal-test: ## Verify isolated deletion journal protocol and crash recovery
	python3 -m unittest discover -s infra/journal -p 'test_*.py' -v

.PHONY: lab11-proxy-smoke
lab11-proxy-smoke: ## Test proxy TLS and SSR restrictions in disposable internal Docker network
	sh infra/scripts/lab11-proxy-smoke.sh

.PHONY: lab11-journal-container
lab11-journal-container: ## Build and test journal in an isolated network and new volumes
	docker build -t varal11-journal-lab:local -f infra/journal/Dockerfile infra/journal
	sh infra/scripts/lab11-journal-container.sh

.PHONY: lab11-init lab11-up
lab11-init: ## Create a new disposable local lab and initialize its journal
	sh infra/scripts/lab11-init.sh

lab11-up: ## Start an existing lab with prebuilt images: LAB_DIR=/tmp/varal11-stack...
	@test -n "$(LAB_DIR)" || { echo 'LAB_DIR is required' >&2; exit 1; }
	sh infra/scripts/lab11-up.sh "$(LAB_DIR)"

.PHONY: lab11-down
lab11-down: ## Stop only the selected lab; retain its volumes
	@test -n "$(LAB_DIR)" || { echo 'LAB_DIR is required' >&2; exit 1; }
	sh infra/scripts/lab11-down.sh "$(LAB_DIR)"

.PHONY: lab11-backup
lab11-backup: ## Quarantine encrypted lab snapshot: LAB_DIR=... BACKUP_KEY_FILE=...
	@test -n "$(LAB_DIR)" -a -n "$(BACKUP_KEY_FILE)" || { echo 'LAB_DIR and BACKUP_KEY_FILE are required' >&2; exit 1; }
	bash infra/scripts/lab11-backup.sh "$(LAB_DIR)" "$(BACKUP_KEY_FILE)"

.PHONY: lab11-smtp-smoke
lab11-smtp-smoke: ## Test synthetic local SMTP STARTTLS capture in an internal network
	sh infra/scripts/lab11-smtp-smoke.sh

.PHONY: lab11-wal-test
lab11-wal-test: ## Verify encrypted WAL witness and crash recovery
	cd api && uv run --frozen python -m unittest discover -s ../infra/wal -p 'test_*.py' -v

.PHONY: lab11-wal-smoke
lab11-wal-smoke: ## Verify PostgreSQL commit -> encrypted WAL -> authenticated ACK in selected lab
	@test -n "$(LAB_DIR)" || { echo 'LAB_DIR is required' >&2; exit 1; }
	bash infra/scripts/lab11-wal-smoke.sh "$(LAB_DIR)"

.PHONY: lab11-backend-witness-smoke
lab11-backend-witness-smoke: ## Test the backend witness in the selected isolated lab
	@test -n "$(LAB_DIR)" || { echo 'LAB_DIR is required' >&2; exit 1; }
	sh infra/scripts/lab11-backend-witness-smoke.sh "$(LAB_DIR)"

.PHONY: lab11-relay-start lab11-relay-stop
lab11-relay-start: ## Expose only the lab TLS proxy on loopback for functional smoke tests
	@test -n "$(LAB_DIR)" || { echo 'LAB_DIR is required' >&2; exit 1; }
	python3 infra/scripts/lab11-relay-start.py "$(LAB_DIR)"

lab11-relay-stop: ## Stop only the selected lab's loopback relay
	@test -n "$(LAB_DIR)" || { echo 'LAB_DIR is required' >&2; exit 1; }
	python3 infra/scripts/lab11-relay-stop.py "$(LAB_DIR)"

.PHONY: lab11-auth-smoke lab11-s3-smoke lab11-log-sentinels
lab11-auth-smoke: ## Exercise synthetic auth/CSRF/SSR over local TLS
	@test -n "$(LAB_DIR)" || { echo 'LAB_DIR is required' >&2; exit 1; }
	python3 infra/scripts/lab11-auth-smoke.py "$(LAB_DIR)"

lab11-s3-smoke: ## Exercise private S3 and a real 60-second signed URL expiry
	@test -n "$(LAB_DIR)" || { echo 'LAB_DIR is required' >&2; exit 1; }
	python3 infra/scripts/lab11-s3-smoke.py "$(LAB_DIR)" --prove-60

lab11-log-sentinels: ## Inspect lab service logs for synthetic URL sentinels
	@test -n "$(LAB_DIR)" || { echo 'LAB_DIR is required' >&2; exit 1; }
	python3 infra/scripts/lab11-log-sentinels.py "$(LAB_DIR)"

.PHONY: lab11-storage-policy-smoke
lab11-storage-policy-smoke: ## Verify S3 private bucket and non-admin lab credential
	sh infra/scripts/lab11-storage-policy-smoke.sh
