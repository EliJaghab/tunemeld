.PHONY: extract \
	transform \
	aggregate \
	view_count \
	format \
	lint \
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
	serve-backend \
	kill-frontend \
	kill-backend

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

view_count:
	@echo "Running view count ETL pipeline..."
	cd django_backend && python manage.py view_count.view_count

historical_view_count:
	@echo "Running view counts..."
	PYTHONPATH=$(PROJECT_ROOT) python3 playlist_etl/historical_view_count.py

format: install-pre-commit
	@echo "🎨 Running pre-commit hooks to format and lint code..."
	source venv/bin/activate && pre-commit run --all-files
	@echo "✅ Code formatted and linted!"


dev: setup_env
	cd backend/backend && wrangler dev --env development src/index.ts

prod:
	cd backend/backend && wrangler deploy --env production src/index.ts

invalidate_cache:
	@set -o allexport; source $(ENV_FILE); set +o allexport; \
	echo "🗑️  Wiping entire Cloudflare cache (new data release)..." && \
	RESPONSE=$$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$$CF_ZONE_ID/purge_cache" \
	-H "Authorization: Bearer $$CLOUDFLARE_API_TOKEN" \
	-H "Content-Type: application/json" \
	--data '{"purge_everything":true}'); \
	echo "$$RESPONSE" | grep -q '"success":true' && echo "✅ Cache wiped successfully" || echo "❌ Failure: $$RESPONSE"

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

test-playlist-etl:
	@echo "Testing playlist ETL pipeline (simulates playlist_etl workflow)..."
	@set -o allexport; source .env.test; set +o allexport; \
	PYTHONPATH=$(PROJECT_ROOT) python3 playlist_etl/main.py

lint: setup_env
	@echo "Running type checking with mypy..."
	source venv/bin/activate && mypy .

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
	pip install --upgrade pip && pip install -e .

build_locally:
	@echo "Building locally..."
	@echo "Killing any process using port 8000..."
	-lsof -ti tcp:8000 | xargs kill -9
	python3 django_backend/manage.py runserver 0.0.0.0:8000

serve-frontend:
	@echo "🌐 Starting TuneMeld frontend server..."
	@if lsof -ti tcp:8080 > /dev/null 2>&1; then \
		echo "📍 Frontend server already running at: http://localhost:8080"; \
		echo "🔄 Use 'make kill-frontend' to stop existing server"; \
	else \
		echo "📍 Website will be available at: http://localhost:8080"; \
		echo "🔄 Cache disabled for development"; \
		echo "🛑 Press Ctrl+C to stop the server"; \
		cd docs && python -m http.server 8080; \
	fi

serve:
	@echo "🌐 Starting TuneMeld website..."
	@if lsof -ti tcp:8080 > /dev/null 2>&1; then \
		echo "📍 Frontend server already running at: http://localhost:8080"; \
		echo "🔄 Use 'make kill-frontend' to stop existing server"; \
	else \
		echo "📍 Frontend: http://localhost:8080"; \
		echo "🛑 Press Ctrl+C to stop"; \
		cd docs && python -m http.server 8080; \
	fi

serve-backend:
	@echo "🚀 Starting Django backend server..."
	@if lsof -ti tcp:8000 > /dev/null 2>&1; then \
		echo "📍 Backend server already running at: http://localhost:8000"; \
		echo "🔄 Use 'make kill-backend' to stop existing server"; \
	else \
		echo "📍 Backend API: http://localhost:8000"; \
		echo "🛑 Press Ctrl+C to stop"; \
		cd django_backend && python manage.py runserver; \
	fi

test-header-art:
	@echo "🧪 Testing header art functionality..."
	@if [ ! -f scripts/verify-header-art.js ]; then echo "❌ Puppeteer scripts not found. Run setup first."; exit 1; fi
	@node scripts/verify-header-art.js http://localhost:8000

test-visual:
	@echo "📸 Running visual tests..."
	@if [ ! -f scripts/verify-header-art.js ]; then echo "❌ Puppeteer scripts not found. Run setup first."; exit 1; fi
	@node scripts/verify-header-art.js http://localhost:8000
	@node scripts/responsive-screenshots.js http://localhost:8000

kill-frontend:
	@echo "🛑 Stopping frontend server..."
	@if lsof -ti tcp:8080 > /dev/null 2>&1; then \
		lsof -ti tcp:8080 | xargs kill -9 && echo "✅ Frontend server stopped"; \
	else \
		echo "ℹ️  No frontend server running on port 8080"; \
	fi

kill-backend:
	@echo "🛑 Stopping backend server..."
	@if lsof -ti tcp:8000 > /dev/null 2>&1; then \
		lsof -ti tcp:8000 | xargs kill -9 && echo "✅ Backend server stopped"; \
	else \
		echo "ℹ️  No backend server running on port 8000"; \
	fi
