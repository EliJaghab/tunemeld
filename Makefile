.PHONY: format \
	lint \
	invalidate_cache \
	setup_env \
	check-frontend-tools \
	build-frontend \
	serve-frontend \
	serve-backend \
	serve-redis \
	kill-redis \
	serve \
	kill-frontend \
	kill-backend \
	clear-cache \
	sync-prod \
	makemigrations \
	migrate \
	migrate-dev \
	migration-safety-check \
	run-play-count-etl \
	test-play-count-etl \
	ci-db-safety-check \
	ci-db-migrate \
	ci-db-validate \
	run-playlist-etl \
	run-audio-features-etl \
	test-audio-features-etl \
	pre-commit-check \
	pre-commit-install \
	ruff-check \
	ruff-fix \
	ruff-format \
	django-check \
	typescript-check \
	clean-cache \
	clean-frontend-cache \
	check \
	format-quick

PROJECT_ROOT := $(shell pwd)
VENV := $(PROJECT_ROOT)/.venv
export PYTHONPATH := $(PROJECT_ROOT)

# Directory variables
BACKEND_DIR := $(PROJECT_ROOT)/backend
FRONTEND_DIR := $(PROJECT_ROOT)/frontend
KV_WORKER_DIR := $(PROJECT_ROOT)/kv_worker

# Python executable
PYTHON := $(VENV)/bin/python
PYTHON_CI := python

# Virtual environment activation
ACTIVATE := source $(VENV)/bin/activate

ifeq ($(GITHUB_ACTIONS),)
	ENV_FILE := .env.dev
	USE_VENV_PYTHON := true
else
	ENV_FILE := .env.prod
	USE_VENV_PYTHON := false
endif

# Conditional Python command
ifeq ($(USE_VENV_PYTHON),true)
	PYTHON_CMD := $(PYTHON)
else
	PYTHON_CMD := $(PYTHON_CI)
endif

setup_env:
	@echo "Setting up environment paths..."
	@echo "Project root: $(PROJECT_ROOT)"
	@echo "Virtual environment: $(VENV)"
	@echo "PYTHONPATH: $(PROJECT_ROOT)"
	@echo "Creating sitecustomize.py to set PYTHONPATH in venv..."
	@echo "import sys; sys.path.insert(0, '$(PROJECT_ROOT)')" > $(VENV)/lib/python3.13/site-packages/sitecustomize.py
	@echo "Loading environment variables from $(ENV_FILE)..."
	@# Note: .env files not present in repo, need to be created locally


# Frontend build variables
NODE_BIN := $(FRONTEND_DIR)/node_modules/.bin
VITE := $(NODE_BIN)/vite
TSC := $(NODE_BIN)/tsc
NODE := node

# Check if frontend tools are available
check-frontend-tools:
	@if [ ! -f "$(VITE)" ]; then \
		echo "Error: Vite not found. Run 'cd frontend && npm install' first."; \
		exit 1; \
	fi
	@if [ ! -f "$(TSC)" ]; then \
		echo "Error: TypeScript compiler not found. Run 'cd frontend && npm install' first."; \
		exit 1; \
	fi

build-frontend: check-frontend-tools
	@echo " Building React v2 frontend with Vite..."
	@cd $(FRONTEND_DIR) && $(VITE) build
	@echo " Frontend built successfully!"

format: install-pre-commit
	@echo " Running pre-commit hooks to format and lint code..."
	$(ACTIVATE) && pre-commit run --all-files
	@echo " Code formatted and linted!"
	@$(MAKE) build-frontend

invalidate_cache:
	@echo "Warning: No environment file found. Skipping cache invalidation."
	@echo "Create .env.dev or .env.prod with CF_ZONE_ID and CLOUDFLARE_API_TOKEN to enable."


lint: setup_env
	@echo "Running type checking with mypy..."
	@$(ACTIVATE) && \
	echo "Checking kv_worker..." && \
	(cd $(KV_WORKER_DIR) && $(VENV)/bin/mypy . --ignore-missing-imports --show-error-codes) && \
	echo "Checking backend..." && \
	(cd $(BACKEND_DIR) && $(VENV)/bin/mypy . --ignore-missing-imports --show-error-codes --explicit-package-bases)

ruff-check: setup_env
	@echo "Running ruff linter checks..."
	$(ACTIVATE) && ruff check --no-fix

ruff-fix: setup_env
	@echo "Running ruff with auto-fixes..."
	$(ACTIVATE) && ruff check --fix --unsafe-fixes

ruff-format: setup_env
	@echo "Running ruff formatter..."
	$(ACTIVATE) && ruff format

django-check: setup_env
	@echo "Running Django deployment checks..."
	cd $(BACKEND_DIR) && $(ACTIVATE) && PYTHONPATH=$(PROJECT_ROOT) $(PYTHON) manage.py check --deploy

typescript-check: check-frontend-tools
	@echo "Running TypeScript type checking..."
	@cd $(FRONTEND_DIR) && $(TSC) --noEmit
	@echo "TypeScript check passed!"

django-import-check: setup_env
	@echo "Testing Django management command imports..."
	@cd $(BACKEND_DIR) && $(ACTIVATE) && PYTHONPATH=$(PROJECT_ROOT) DJANGO_SETTINGS_MODULE=core.settings $(PYTHON) -c 'import django; django.setup(); from core.management.commands import playlist_etl; print("All management commands import successfully")'

backend-startup-check: setup_env
	@echo "Validating backend startup..."
	cd $(BACKEND_DIR) && $(ACTIVATE) && PYTHONPATH=$(PROJECT_ROOT) $(PYTHON) manage.py check --deploy --fail-level ERROR

clean-cache:
	@echo "Cleaning Python cache files..."
	@find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name '*.pyc' -delete 2>/dev/null || true
	@rm -rf .mypy_cache 2>/dev/null || true
	@echo "Cache cleaned"

clean-frontend-cache:
	@echo "Cleaning Vite cache..."
	@rm -rf $(FRONTEND_DIR)/node_modules/.vite 2>/dev/null || true
	@rm -rf $(FRONTEND_DIR)/dist 2>/dev/null || true
	@echo "Frontend cache cleaned"

check: lint ruff-check django-check typescript-check
	@echo "All checks passed!"

format-quick: ruff-fix ruff-format clean-cache
	@echo "Quick format completed (ruff + cache cleanup)"

pre-commit-check: setup_env
	@echo "Running all pre-commit hooks..."
	$(ACTIVATE) && pre-commit run --all-files

pre-commit-install: setup_env
	@echo "Installing pre-commit hooks..."
	$(ACTIVATE) && pre-commit install

install-dev: setup_env
	@echo "Installing development dependencies..."
	$(ACTIVATE) && pip install -e ".[dev]"

install-pre-commit: install-dev
	@echo "Installing pre-commit hooks..."
	$(ACTIVATE) && pre-commit install


serve-frontend: check-frontend-tools
	@echo " Starting TuneMeld React v2 frontend (Vite dev server)..."
	@if lsof -ti tcp:3000 > /dev/null 2>&1; then \
		echo " Vite server already running at: http://localhost:3000"; \
		echo " Use 'make kill-frontend' to stop existing server"; \
		exit 1; \
	fi
	@echo " React v2 (Vite): http://localhost:3000/index-v2.html"
	@echo " V1 (Legacy):     http://localhost:3000/index.html"
	@echo " Press Ctrl+C to stop the server"
	@echo ""
	@cd $(FRONTEND_DIR) && $(VITE)
serve-redis:
	@if [ -n "$$REDIS_URL" ]; then \
		echo " Using REDIS_URL from environment"; \
	elif lsof -ti tcp:6379 > /dev/null 2>&1; then \
		echo " Redis already running on port 6379"; \
	elif command -v redis-server >/dev/null 2>&1; then \
		redis-server --save "" --appendonly no --daemonize yes; \
		echo " Redis started on port 6379"; \
	else \
		echo "Error: Redis not found. Install with: brew install redis"; \
		exit 1; \
	fi


serve-backend: serve-redis
	@echo " Starting Django backend server..."
	@if lsof -ti tcp:8000 > /dev/null 2>&1; then \
		echo " Backend server already running at: http://localhost:8000"; \
		echo " Use 'make kill-backend' to stop existing server"; \
	else \
		echo " Backend API: http://localhost:8000"; \
		echo " Press Ctrl+C to stop"; \
		cd $(BACKEND_DIR) && $(PYTHON) manage.py runserver; \
	fi

clear-cache:
	@echo " Clearing Redis cache..."
	@redis-cli -n 1 FLUSHDB > /dev/null 2>&1 || echo " Redis not running, skipping cache clear"
	@echo " Cache cleared! Frontend requests will automatically populate cache."

sync-prod: serve-redis
	@echo " Syncing production to local (database + Redis cache)..."
	@echo " WARNING: This will overwrite your local data!"
	@cd $(BACKEND_DIR) && $(PYTHON_CMD) manage.py sync_prod
	@echo " Production synced to local!"


kill-frontend:
	@echo " Stopping frontend server..."
	@if lsof -ti tcp:3000 > /dev/null 2>&1; then \
		lsof -ti tcp:3000 | xargs kill -9 && echo " Vite server (port 3000) stopped"; \
	else \
		echo "  No Vite server running on port 3000"; \
	fi

kill-backend:
	@echo " Stopping backend server..."
	@if lsof -ti tcp:8000 > /dev/null 2>&1; then \
		lsof -ti tcp:8000 | xargs kill -9 && echo " Backend server stopped"; \
	else \
		echo "  No backend server running on port 8000"; \
	fi

kill-redis:
	@echo " Stopping Redis server on port 6379..."
	@if lsof -ti tcp:6379 > /dev/null 2>&1; then \
		lsof -ti tcp:6379 | xargs kill -9 && echo " Redis server stopped"; \
	else \
		echo "  No Redis server running on port 6379"; \
	fi

serve:
	@echo " Starting both frontend and backend servers..."
	@echo " React v2 (Vite): http://localhost:3000/index-v2.html"
	@echo " Backend API: http://localhost:8000"
	@echo " Redis cache: redis://localhost:6379"
	@echo " Press Ctrl+C to stop all servers"
	@echo ""
	@$(MAKE) serve-frontend & $(MAKE) serve-backend & wait

# Django Migration Commands
makemigrations:
	@echo " Creating Django migrations..."
	@cd $(BACKEND_DIR) && echo "1\n0" | $(PYTHON) manage.py makemigrations core
	@echo " Migrations created successfully"

migrate:
	@echo " Applying migrations to production PostgreSQL..."
	@cd $(BACKEND_DIR) && $(PYTHON) manage.py migrate --noinput
	@echo " Migrations applied successfully"

migrate-dev:
	@echo " Applying migrations to local SQLite database..."
	@cd $(BACKEND_DIR) && $(PYTHON) manage.py migrate --noinput
	@echo " Local migrations applied successfully"

# Database Safety and ETL Commands
migration-safety-check:
	@echo " Running comprehensive database safety check..."
	@cd $(BACKEND_DIR) && $(PYTHON) migration_safety_check.py
	@echo " Database safety check passed"

test-play-count-etl:
	@echo " Running Play Count ETL (limited for testing)..."
	@cd $(BACKEND_DIR) && $(PYTHON_CMD) manage.py play_count --limit 10
	@echo " Play Count ETL test completed"

# CI/CD Database Operations
ci-db-safety-check:
	@echo " Running comprehensive database safety check..."
	@cd $(BACKEND_DIR) && $(PYTHON_CI) migration_safety_check.py
	@echo " Database safety check passed"

ci-db-migrate:
	@echo " Checking migration status on production PostgreSQL..."
	@cd $(BACKEND_DIR) && $(PYTHON_CI) manage.py showmigrations
	@echo ""
	@echo " Applying migrations to production PostgreSQL..."
	@cd $(BACKEND_DIR) && $(PYTHON_CI) manage.py migrate --noinput
	@echo ""
	@echo " Verifying migration consistency..."
	@cd $(BACKEND_DIR) && $(PYTHON_CI) manage.py showmigrations | grep -E "\\[ \\]" && echo "❌ Unapplied migrations detected!" && exit 1 || echo " All migrations applied successfully"
	@echo " Production database migrations completed successfully"

ci-db-validate:
	@echo " Running post-ETL database validation..."
	@cd $(BACKEND_DIR) && $(PYTHON_CI) migration_safety_check.py
	@echo " Post-ETL validation passed"

run-play-count-etl:
	@echo " Running Play Count ETL Pipeline..."
	@cd $(BACKEND_DIR) && $(PYTHON_CMD) manage.py play_count
	@echo " Play Count ETL Pipeline completed"

run-playlist-etl:
	@echo " Running Playlist ETL Pipeline..."
	@cd $(BACKEND_DIR) && $(PYTHON_CMD) manage.py playlist_etl
	@echo " Playlist ETL Pipeline completed"

run-playlist-etl-force-refresh:
	@echo " Running Playlist ETL Pipeline with Force Refresh (bypassing RapidAPI cache)..."
	@cd $(BACKEND_DIR) && $(PYTHON_CMD) manage.py playlist_etl --force-refresh
	@echo " Playlist ETL Pipeline with Force Refresh completed"

run-audio-features-etl:
	@echo " Running Audio Features ETL Pipeline..."
	@cd $(BACKEND_DIR) && $(PYTHON_CMD) manage.py audio_features_etl
	@echo " Audio Features ETL Pipeline completed"

test-audio-features-etl:
	@echo " Running Audio Features ETL (limited for testing)..."
	@cd $(BACKEND_DIR) && $(PYTHON_CMD) manage.py audio_features_etl --limit 10
	@echo " Audio Features ETL test completed"
