.PHONY: extract \
	transform \
	aggregate \
	view_count \
	format \
	lint \
	fix \
	pull_push \
	dev \
	prod \
	invalidate_cache \
	test \
	setup_env \
	activate \
	install_deps \
	build \
	run \
	build_and_run \
	build_and_debug \
	build_locally \
	setup_backend_env

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
	@echo "Running tox to lint and format code..."
	tox

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
	@echo "Running tests..."
	python -m unittest discover tests/

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