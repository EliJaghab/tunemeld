.PHONY: format \
	lint \
	invalidate_cache \
	setup_env \
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
	check \
	format-quick

PROJECT_ROOT := $(shell pwd)
VENV := $(PROJECT_ROOT)/.venv
export PYTHONPATH := $(PROJECT_ROOT)

ifeq ($(GITHUB_ACTIONS),)
	ENV_FILE := .env.dev
else
	ENV_FILE := .env.prod
endif

setup_env:
	@echo "Setting up environment paths..."
	@echo "Project root: $(shell pwd)"
	@echo "Virtual environment: $(shell pwd)/.venv"
	@echo "PYTHONPATH: $(shell pwd)"
	@echo "Creating sitecustomize.py to set PYTHONPATH in venv..."
	@echo "import sys; sys.path.insert(0, '$(shell pwd)')" > .venv/lib/python3.13/site-packages/sitecustomize.py
	@echo "Loading environment variables from .env.dev..."
	@# Note: .env files not present in repo, need to be created locally


build-frontend:
	@echo " Building frontend TypeScript..."
	cd frontend && npm run build
	@echo " Frontend built successfully!"

format: install-pre-commit
	@echo " Running pre-commit hooks to format and lint code..."
	source .venv/bin/activate && pre-commit run --all-files
	@echo " Code formatted and linted!"
	@$(MAKE) build-frontend

invalidate_cache:
	@echo "Warning: No environment file found. Skipping cache invalidation."
	@echo "Create .env.dev or .env.prod with CF_ZONE_ID and CLOUDFLARE_API_TOKEN to enable."


lint: setup_env
	@echo "Running type checking with mypy..."
	@source venv/bin/activate && \
	echo "Checking kv_worker..." && \
	(cd kv_worker && ../.venv/bin/mypy . --ignore-missing-imports --show-error-codes) && \
	echo "Checking backend..." && \
	(cd backend && ../.venv/bin/mypy . --ignore-missing-imports --show-error-codes --explicit-package-bases)

ruff-check: setup_env
	@echo "Running ruff linter checks..."
	source .venv/bin/activate && ruff check --no-fix

ruff-fix: setup_env
	@echo "Running ruff with auto-fixes..."
	source .venv/bin/activate && ruff check --fix --unsafe-fixes

ruff-format: setup_env
	@echo "Running ruff formatter..."
	source .venv/bin/activate && ruff format

django-check: setup_env
	@echo "Running Django deployment checks..."
	cd backend && source ../.venv/bin/activate && PYTHONPATH=.. python manage.py check --deploy

typescript-check:
	@echo "Running TypeScript type checking..."
	cd frontend && npx tsc --noEmit
	@echo "TypeScript check passed!"

django-import-check: setup_env
	@echo "Testing Django management command imports..."
	@cd backend && source ../.venv/bin/activate && PYTHONPATH=.. DJANGO_SETTINGS_MODULE=core.settings python -c 'import django; django.setup(); from core.management.commands import playlist_etl; print("All management commands import successfully")'

backend-startup-check: setup_env
	@echo "Validating backend startup..."
	cd backend && source ../.venv/bin/activate && PYTHONPATH=.. python manage.py check --deploy --fail-level ERROR

clean-cache:
	@echo "Cleaning Python cache files..."
	@find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name '*.pyc' -delete 2>/dev/null || true
	@rm -rf .mypy_cache 2>/dev/null || true
	@echo "Cache cleaned"

check: lint ruff-check django-check typescript-check
	@echo "All checks passed!"

format-quick: ruff-fix ruff-format clean-cache
	@echo "Quick format completed (ruff + cache cleanup)"

pre-commit-check: setup_env
	@echo "Running all pre-commit hooks..."
	source venv/bin/activate && pre-commit run --all-files

pre-commit-install: setup_env
	@echo "Installing pre-commit hooks..."
	source venv/bin/activate && pre-commit install

install-dev: setup_env
	@echo "Installing development dependencies..."
	source .venv/bin/activate && pip install -e ".[dev]"

install-pre-commit: install-dev
	@echo "Installing pre-commit hooks..."
	source venv/bin/activate && pre-commit install


serve-frontend:
	@echo " Starting TuneMeld frontend with auto-compilation..."
	@if lsof -ti tcp:8080 > /dev/null 2>&1; then \
		echo " Frontend server already running at: http://localhost:8080"; \
		echo " Use 'make kill-frontend' to stop existing server"; \
		exit 1; \
	fi
	@echo " TypeScript, CSS, and HTML will auto-compile on file changes"
	@echo " Website will be available at: http://localhost:8080"
	@echo " Press Ctrl+C to stop all processes"
	@echo ""
	@cd frontend && npm run dev & (cd frontend/dist && python -m http.server 8080)
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
		cd backend && python manage.py runserver; \
	fi

clear-cache:
	@echo " Clearing Redis cache..."
	@redis-cli -n 1 FLUSHDB > /dev/null 2>&1 || echo " Redis not running, skipping cache clear"
	@echo " Cache cleared! Frontend requests will automatically populate cache."

sync-prod: serve-redis
	@echo " Syncing production to local (database + Redis cache)..."
	@echo " WARNING: This will overwrite your local data!"
ifeq ($(GITHUB_ACTIONS),)
	@cd backend && $(VENV)/bin/python manage.py sync_prod
else
	@cd backend && python manage.py sync_prod
endif
	@echo " Production synced to local!"


kill-frontend:
	@echo " Stopping frontend server..."
	@if lsof -ti tcp:8080 > /dev/null 2>&1; then \
		lsof -ti tcp:8080 | xargs kill -9 && echo " Frontend server stopped"; \
	else \
		echo "  No frontend server running on port 8080"; \
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
	@echo " Frontend: http://localhost:8080 (with TypeScript auto-compilation)"
	@echo " Backend API: http://localhost:8000"
	@echo " Redis cache: redis://localhost:6379"
	@echo " Press Ctrl+C to stop both servers"
	@echo ""
	@$(MAKE) serve-frontend & $(MAKE) serve-backend & wait

# Django Migration Commands
makemigrations:
	@echo " Creating Django migrations..."
	@cd backend && echo "1\n0" | $(VENV)/bin/python manage.py makemigrations core
	@echo " Migrations created successfully"

migrate:
	@echo " Applying migrations to production PostgreSQL..."
	@cd backend && $(VENV)/bin/python manage.py migrate --noinput
	@echo " Migrations applied successfully"

migrate-dev:
	@echo " Applying migrations to local SQLite database..."
	@cd backend && $(VENV)/bin/python manage.py migrate --noinput
	@echo " Local migrations applied successfully"

# Database Safety and ETL Commands
migration-safety-check:
	@echo " Running comprehensive database safety check..."
	@cd backend && $(VENV)/bin/python migration_safety_check.py
	@echo " Database safety check passed"

test-play-count-etl:
	@echo " Running Play Count ETL (limited for testing)..."
ifeq ($(GITHUB_ACTIONS),)
	@cd backend && $(VENV)/bin/python manage.py play_count --limit 10
else
	@cd backend && python manage.py play_count --limit 10
endif
	@echo " Play Count ETL test completed"

# CI/CD Database Operations
ci-db-safety-check:
	@echo " Running comprehensive database safety check..."
	@cd backend && python migration_safety_check.py
	@echo " Database safety check passed"

ci-db-migrate:
	@echo " Checking migration status on production PostgreSQL..."
	@cd backend && python manage.py showmigrations
	@echo ""
	@echo " Applying migrations to production PostgreSQL..."
	@cd backend && python manage.py migrate core 0002 --fake --noinput || true
	@cd backend && python manage.py migrate --noinput
	@echo ""
	@echo " Verifying migration consistency..."
	@cd backend && python manage.py showmigrations | grep -E "\\[ \\]" && echo "❌ Unapplied migrations detected!" && exit 1 || echo " All migrations applied successfully"
	@echo " Production database migrations completed successfully"

ci-db-validate:
	@echo " Running post-ETL database validation..."
	@cd backend && python migration_safety_check.py
	@echo " Post-ETL validation passed"

run-play-count-etl:
	@echo " Running Play Count ETL Pipeline..."
ifeq ($(GITHUB_ACTIONS),)
	@cd backend && $(VENV)/bin/python manage.py play_count
else
	@cd backend && python manage.py play_count
endif
	@echo " Play Count ETL Pipeline completed"

run-playlist-etl:
	@echo " Running Playlist ETL Pipeline..."
ifeq ($(GITHUB_ACTIONS),)
	@cd backend && $(VENV)/bin/python manage.py playlist_etl
else
	@cd backend && python manage.py playlist_etl
endif
	@echo " Playlist ETL Pipeline completed"

run-playlist-etl-force-refresh:
	@echo " Running Playlist ETL Pipeline with Force Refresh (bypassing RapidAPI cache)..."
ifeq ($(GITHUB_ACTIONS),)
	@cd backend && $(VENV)/bin/python manage.py playlist_etl --force-refresh
else
	@cd backend && python manage.py playlist_etl --force-refresh
endif
	@echo " Playlist ETL Pipeline with Force Refresh completed"

run-audio-features-etl:
	@echo " Running Audio Features ETL Pipeline..."
ifeq ($(GITHUB_ACTIONS),)
	@cd backend && $(VENV)/bin/python manage.py audio_features_etl
else
	@cd backend && python manage.py audio_features_etl
endif
	@echo " Audio Features ETL Pipeline completed"

test-audio-features-etl:
	@echo " Running Audio Features ETL (limited for testing)..."
ifeq ($(GITHUB_ACTIONS),)
	@cd backend && $(VENV)/bin/python manage.py audio_features_etl --limit 10
else
	@cd backend && python manage.py audio_features_etl --limit 10
endif
	@echo " Audio Features ETL test completed"
