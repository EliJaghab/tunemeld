.PHONY: extract \
	transform \
	aggregate \
	view_count \
	format \
	format-js \
	format-check \
	clean-repo \
	lint \
	fix \
	pull_push \
	dev \
	prod \
	invalidate_cache \
	test \
	test-unit \
	test-integration \
	test-slow \
	test-all \
	test-coverage \
	test-ci \
	test-header-art \
	test-visual \
	setup_env \
	activate \
	install_deps \
	build \
	run \
	build_and_run \
	build_and_debug \
	build_locally \
	setup_backend_env \
	serve \
	serve-frontend \
	serve-backend

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
	@echo "import sys; sys.path.insert(0, '$(shell pwd)')" > venv/lib/python3.10/site-packages/sitecustomize.py
	@echo "Loading environment variables from .env.dev..."
	@source venv/bin/activate && export $(cat .env.dev | xargs)

extract:
	@echo "Running extract..."
	python playlist_etl/extract.py

transform:
	@echo "Running transform..."
	python playlist_etl/transform.py

aggregate:
	@echo "Running aggregate..."
	python playlist_etl/aggregate.py

view_count:
	@echo "Running view counts..."
	python playlist_etl/view_count.py

historical_view_count:
	@echo "Running view counts..."
	python playlist_etl/historical_view_count.py

format: setup_env
	@echo "Running ruff to lint and format code aggressively..."
	source venv/bin/activate && ruff check --fix --unsafe-fixes . && ruff format .
	@echo "Formatting JavaScript files with Prettier..."
	npx prettier --write "docs/**/*.js"

format-js:
	@echo "Formatting JavaScript files with Prettier..."
	npx prettier --write "docs/**/*.js"

format-check:
	@echo "Checking code formatting..."
	source venv/bin/activate && ruff check . && ruff format --check .
	@echo "Checking JavaScript formatting..."
	npx prettier --check "docs/**/*.js"

clean-repo: setup_env
	@echo "🧹 Cleaning up repository with aggressive formatting..."
	source venv/bin/activate && ruff check --fix --unsafe-fixes .
	source venv/bin/activate && ruff format .
	npx prettier --write "docs/**/*.js" "docs/**/*.html" "docs/**/*.css" "docs/**/*.md"
	@echo "✅ Repository cleaned and formatted!"

pull_push: setup_env
	@git pull --rebase
	@if [ $$? -ne 0 ]; then echo "Error: Failed to pull the latest changes. Aborting push."; exit 1; fi
	@git push
	@if [ $$? -ne 0 ]; then echo "Error: Failed to push the changes."; exit 1; fi
	@echo "Successfully pulled, rebased, and pushed the changes."

dev: setup_env
	cd backend/backend && wrangler dev --env development src/index.ts

prod:
	cd backend/backend && wrangler deploy --env production src/index.ts

invalidate_cache:
	@set -o allexport; source $(ENV_FILE); set +o allexport; \
	echo "Invalidating cache using Cloudflare API..." && \
	RESPONSE=$$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$$CF_ZONE_ID/purge_cache" \
	-H "Authorization: Bearer $$CLOUDFLARE_API_TOKEN" \
	-H "Content-Type: application/json" \
	--data '{"purge_everything":true}'); \
	echo "$$RESPONSE" | grep -q '"success":true' && echo "Success" || echo "Failure: $$RESPONSE"

test: setup_env
	@echo "Running all tests..."
	source venv/bin/activate && python -m pytest tests/ -v

test-unit: setup_env
	@echo "Running unit tests only..."
	source venv/bin/activate && python -m pytest tests/ -v -m "not integration and not slow"

test-integration: setup_env
	@echo "Running integration tests..."
	source venv/bin/activate && python -m pytest tests/ -v -m "integration and not slow"

test-slow: setup_env
	@echo "Running slow tests..."
	source venv/bin/activate && python -m pytest tests/ -v -m "slow"

test-all: setup_env
	@echo "Running all tests including slow ones..."
	source venv/bin/activate && python -m pytest tests/ -v -m "integration or slow or (not integration and not slow)"

test-coverage: setup_env
	@echo "Running tests with coverage report..."
	source venv/bin/activate && python -m pytest tests/ -v --cov=playlist_etl --cov-report=html --cov-report=term-missing

test-ci: setup_env
	@echo "Running tests as they would run in CI..."
	source venv/bin/activate && python -m pytest tests/ -v --tb=short --cov=playlist_etl --cov-report=xml -m "not slow"

lint: setup_env
	@echo "Running linting checks..."
	source venv/bin/activate && ruff check . && mypy .

install-dev: setup_env
	@echo "Installing development dependencies..."
	source venv/bin/activate && pip install -e ".[dev]"

install-pre-commit: install-dev
	@echo "Installing pre-commit hooks..."
	source venv/bin/activate && pre-commit install

setup_backend_env:
	@echo "Setting up backend virtual environment..."
	python3 -m venv backend
	@echo "Activating backend virtual environment and installing requirements..."
	pip install --upgrade pip && pip install -r django_backend/requirements.txt

build_locally:
	@echo "Building locally..."
	@echo "Killing any process using port 8000..."
	-lsof -ti tcp:8000 | xargs kill -9
	python3 django_backend/manage.py runserver 0.0.0.0:8000

serve-frontend:
	@echo "🌐 Starting TuneMeld frontend server..."
	@echo "📍 Website will be available at: http://localhost:8080"
	@echo "🛑 Press Ctrl+C to stop the server"
	@cd docs && python -m http.server 8080

serve:
	@echo "🌐 Starting TuneMeld website..."
	@echo "📍 Frontend: http://localhost:8080"
	@echo "🛑 Press Ctrl+C to stop"
	@cd docs && python -m http.server 8080

serve-backend:
	@echo "🚀 Starting Django backend server..."
	@echo "📍 Backend API: http://localhost:8000"
	@echo "🛑 Press Ctrl+C to stop"
	@cd django_backend && python manage.py runserver

test-header-art:
	@echo "🧪 Testing header art functionality..."
	@if [ ! -f scripts/verify-header-art.js ]; then echo "❌ Puppeteer scripts not found. Run setup first."; exit 1; fi
	@node scripts/verify-header-art.js http://localhost:8000

test-visual:
	@echo "📸 Running visual tests..."
	@if [ ! -f scripts/verify-header-art.js ]; then echo "❌ Puppeteer scripts not found. Run setup first."; exit 1; fi
	@node scripts/verify-header-art.js http://localhost:8000
	@node scripts/responsive-screenshots.js http://localhost:8000
