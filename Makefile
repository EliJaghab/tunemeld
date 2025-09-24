.PHONY: format \
	lint \
	invalidate_cache \
	setup_env \
	serve-frontend \
	serve-backend \
	serve \
	kill-frontend \
	kill-backend \
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
	pre-commit-check \
	pre-commit-install \
	ruff-check \
	ruff-fix \
	ruff-format \
	django-check \
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


format: install-pre-commit
	@echo " Running pre-commit hooks to format and lint code..."
	source .venv/bin/activate && pre-commit run --all-files
	@echo " Code formatted and linted!"

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

check: lint ruff-check django-check
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
	@echo " Starting TuneMeld frontend server..."
	@if lsof -ti tcp:8080 > /dev/null 2>&1; then \
		echo " Frontend server already running at: http://localhost:8080"; \
		echo " Use 'make kill-frontend' to stop existing server"; \
	else \
		echo " Website will be available at: http://localhost:8080"; \
		echo " Cache disabled for development"; \
		echo " Press Ctrl+C to stop the server"; \
		cd docs && python -m http.server 8080; \
	fi


serve-backend:
	@echo " Starting Django backend server..."
	@if lsof -ti tcp:8000 > /dev/null 2>&1; then \
		echo " Backend server already running at: http://localhost:8000"; \
		echo " Use 'make kill-backend' to stop existing server"; \
	else \
		echo " Backend API: http://localhost:8000"; \
		echo " Press Ctrl+C to stop"; \
		cd backend && python manage.py runserver; \
	fi


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

serve:
	@echo " Starting both frontend and backend servers..."
	@echo " Frontend: http://localhost:8080"
	@echo " Backend API: http://localhost:8000"
	@echo " Press Ctrl+C to stop both servers"
	@echo ""
	@$(MAKE) serve-frontend & $(MAKE) serve-backend & wait

# Django Migration Commands
makemigrations:
	@echo " Creating Django migrations..."
	@cd backend && echo "1\n0" | $(VENV)/bin/python manage.py makemigrations core
	@echo " Migrations created successfully"

migrate:
	@echo " Applying migrations to Railway PostgreSQL..."
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
	@echo " Checking migration status on Railway PostgreSQL..."
	@cd backend && python manage.py showmigrations
	@echo ""
	@echo " Applying migrations to Railway PostgreSQL..."
	@cd backend && python manage.py migrate --noinput
	@echo ""
	@echo " Verifying migration consistency..."
	@cd backend && python manage.py showmigrations | grep -E "\\[ \\]" && echo "❌ Unapplied migrations detected!" && exit 1 || echo " All migrations applied successfully"
	@echo " Railway database migrations completed successfully"

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
