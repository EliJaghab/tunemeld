.PHONY: extract \
	transform \
	aggregate \
	format \
	lint \
	invalidate_cache \
	test \
	test-unit \
	test-integration \
	test-slow \
	test-all \
	test-coverage \
	test-ci \
	setup_env \
	serve-frontend \
	serve-backend \
	kill-frontend \
	kill-backend \
	makemigrations \
	migrate \
	migrate-dev \
	migration-safety-check \
	run-view-count-etl \
	ci-db-safety-check \
	ci-db-migrate \
	ci-db-validate \
	run-playlist-etl

PROJECT_ROOT := $(shell pwd)
VENV := $(PROJECT_ROOT)/venv
export PYTHONPATH := $(PROJECT_ROOT)

ifeq ($(GITHUB_ACTIONS),)
	ENV_FILE := .env.dev
else
	ENV_FILE := .env.prod
endif

setup_env:
	@echo "Setting up environment paths..."
	@echo "Project root: $(shell pwd)"
	@echo "Virtual environment: $(shell pwd)/venv"
	@echo "PYTHONPATH: $(shell pwd)"
	@echo "Creating sitecustomize.py to set PYTHONPATH in venv..."
	@echo "import sys; sys.path.insert(0, '$(shell pwd)')" > venv/lib/python3.13/site-packages/sitecustomize.py
	@echo "Loading environment variables from .env.dev..."
	@source venv/bin/activate && export $(cat .env.dev | xargs)

extract:
	@echo "Running extract..."
	PYTHONPATH=$(PROJECT_ROOT) python3 playlist_etl/extract.py

transform:
	@echo "Running transform..."
	PYTHONPATH=$(PROJECT_ROOT) python3 playlist_etl/transform_playlist.py

aggregate:
	@echo "Running aggregate..."
	PYTHONPATH=$(PROJECT_ROOT) python3 playlist_etl/aggregate.py


format: install-pre-commit
	@echo " Running pre-commit hooks to format and lint code..."
	source venv/bin/activate && pre-commit run --all-files
	@echo " Code formatted and linted!"



invalidate_cache:
	@set -o allexport; source $(ENV_FILE); set +o allexport; \
	echo "  Wiping entire Cloudflare cache (new data release)..." && \
	RESPONSE=$$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$$CF_ZONE_ID/purge_cache" \
	-H "Authorization: Bearer $$CLOUDFLARE_API_TOKEN" \
	-H "Content-Type: application/json" \
	--data '{"purge_everything":true}'); \
	echo "$$RESPONSE" | grep -q '"success":true' && echo " Cache wiped successfully" || echo " Failure: $$RESPONSE"

test: setup_env
	@echo "Running all tests..."
	@set -o allexport; source .env.test; set +o allexport; \
	source venv/bin/activate && python -m pytest tests/ -v

test-unit: setup_env
	@echo "Running unit tests only..."
	@set -o allexport; source .env.test; set +o allexport; \
	source venv/bin/activate && python -m pytest tests/ -v -m "not integration and not slow"

test-integration: setup_env
	@echo "Running integration tests..."
	@set -o allexport; source .env.test; set +o allexport; \
	source venv/bin/activate && python -m pytest tests/ -v -m "integration and not slow"

test-slow: setup_env
	@echo "Running slow tests..."
	@set -o allexport; source .env.test; set +o allexport; \
	source venv/bin/activate && python -m pytest tests/ -v -m "slow"

test-all: setup_env
	@echo "Running all tests including slow ones..."
	@set -o allexport; source .env.test; set +o allexport; \
	source venv/bin/activate && python -m pytest tests/ -v -m "integration or slow or (not integration and not slow)"

test-coverage: setup_env
	@echo "Running tests with coverage report..."
	@set -o allexport; source .env.test; set +o allexport; \
	source venv/bin/activate && python -m pytest tests/ -v --cov=playlist_etl --cov-report=html --cov-report=term-missing

test-ci: setup_env
	@echo "Running tests as they would run in CI..."
	@set -o allexport; source .env.test; set +o allexport; \
	source venv/bin/activate && python -m pytest tests/ -v --tb=short --cov=playlist_etl --cov-report=xml -m "not slow"


lint: setup_env
	@echo "Running type checking with mypy..."
	source venv/bin/activate && mypy .

install-dev: setup_env
	@echo "Installing development dependencies..."
	source venv/bin/activate && pip install -e ".[dev]"

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
		cd django_backend && python manage.py runserver; \
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

# Django Migration Commands
makemigrations:
	@echo " Creating Django migrations..."
	@cd django_backend && echo "1\n0" | $(VENV)/bin/python manage.py makemigrations core
	@echo " Migrations created successfully"

migrate:
	@echo " Applying migrations to Railway PostgreSQL..."
	@cd django_backend && $(VENV)/bin/python manage.py migrate --noinput
	@echo " Migrations applied successfully"

migrate-dev:
	@echo " Applying migrations to local SQLite database..."
	@cd django_backend && $(VENV)/bin/python manage.py migrate --noinput
	@echo " Local migrations applied successfully"

# Database Safety and ETL Commands
migration-safety-check:
	@echo " Running comprehensive database safety check..."
	@cd django_backend && $(VENV)/bin/python migration_safety_check.py
	@echo " Database safety check passed"

run-view-count-etl:
	@echo " Running View Count ETL..."
	@cd django_backend && $(VENV)/bin/python manage.py a_view_count
	@echo " View Count ETL completed"

# CI/CD Database Operations
ci-db-safety-check:
	@echo " Running comprehensive database safety check..."
	@cd django_backend && python migration_safety_check.py
	@echo " Database safety check passed"

ci-db-migrate:
	@echo " Checking migration status on Railway PostgreSQL..."
	@cd django_backend && python manage.py showmigrations
	@echo ""
	@echo " Applying migrations to Railway PostgreSQL..."
	@cd django_backend && python manage.py migrate --noinput
	@echo ""
	@echo " Verifying migration consistency..."
	@cd django_backend && python manage.py showmigrations | grep -E "\\[ \\]" && echo "❌ Unapplied migrations detected!" && exit 1 || echo " All migrations applied successfully"
	@echo " Railway database migrations completed successfully"

ci-db-validate:
	@echo " Running post-ETL database validation..."
	@cd django_backend && python migration_safety_check.py
	@echo " Post-ETL validation passed"

run-playlist-etl:
	@echo " Running Playlist ETL Pipeline..."
	@cd django_backend && python manage.py a_playlist_etl
	@echo " Playlist ETL Pipeline completed"
