.PHONY: extract transform aggregate view_count format lint fix pull_push dev prod invalidate_cache test setup_env activate

# Automatically detect the project root
PROJECT_ROOT := $(shell pwd)

# Set the virtual environment directory
VENV := $(PROJECT_ROOT)/venv

# Add PYTHONPATH to include the project root and ensure it's used in the venv
export PYTHONPATH := $(PROJECT_ROOT)

# Ensure the virtual environment is activated
activate:
	@echo "Activating virtual environment..."
	@source $(VENV)/bin/activate

# Command to setup environment paths
setup_env:
	@echo "Setting up environment paths..."
	@echo "Project root: $(PWD)"
	@echo "Virtual environment: $(VENV)"
	@echo "PYTHONPATH: $(PYTHONPATH)"
	@mkdir -p $(VENV)/lib/python3.10/site-packages
	@echo "Creating sitecustomize.py to set PYTHONPATH in venv..."
	@echo 'import sys; sys.path.insert(0, "$(PYTHONPATH)")' > $(VENV)/lib/python3.10/site-packages/sitecustomize.py


extract: setup_env
	@echo "Running extract..."
	$(VENV)/bin/python playlist_etl/extract.py

transform: setup_env
	@echo "Running transform..."
	$(VENV)/bin/python playlist_etl/transform.py

aggregate: setup_env
	@echo "Running aggregate..."
	$(VENV)/bin/python playlist_etl/aggregate.py

view_count: setup_env
	@echo "Running view counts..."
	$(VENV)/bin/python playlist_etl/view_count.py

format: setup_env
	@echo "Running tox to lint and format code..."
	$(VENV)/bin/tox

pull_push: setup_env
	@git pull --rebase
	@if [ $$? -ne 0 ]; then echo "Error: Failed to pull the latest changes. Aborting push."; exit 1; fi
	@git push
	@if [ $$? -ne 0 ]; then echo "Error: Failed to push the changes."; exit 1; fi
	@echo "Successfully pulled, rebased, and pushed the changes."

dev: setup_env
	cd backend/backend && wrangler dev --env development src/index.ts

prod: setup_env
	cd backend/backend && wrangler deploy --env production src/index.ts

invalidate_cache: setup_env
	@set -o allexport; source .env; set +o allexport; \
	echo "Invalidating cache using Cloudflare API..." && \
	RESPONSE=$$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$$CF_ZONE_ID/purge_cache" \
	-H "Authorization: Bearer $$CLOUDFLARE_API_TOKEN" \
	-H "Content-Type: application/json" \
	--data '{"purge_everything":true}'); \
	echo "$$RESPONSE" | grep -q '"success":true' && echo "Success" || echo "Failure: $$RESPONSE"

test: setup_env
	@echo "Running tests..."
	$(VENV)/bin/python -m unittest discover tests/
