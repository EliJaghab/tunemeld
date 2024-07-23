.PHONY: extract transform aggregate format_all lint fix pull_push dev prod invalidate_cache

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

format_all:
	@echo "Linting code with tox..."
	tox -e lint
	@echo "Formatting code with tox..."
	tox -e format

fix: format_all
	@echo "Automatically fixing code style issues..."

pull_push:
	@git pull --rebase
	@if [ $$? -ne 0 ]; then echo "Error: Failed to pull the latest changes. Aborting push."; exit 1; fi
	@git push
	@if [ $$? -ne 0 ]; then echo "Error: Failed to push the changes."; exit 1; fi
	@echo "Successfully pulled, rebased, and pushed the changes."

dev:
	cd backend/backend && wrangler dev --env development src/index.ts

prod:
	cd backend/backend && wrangler deploy --env production src/index.ts

invalidate_cache:
	@set -o allexport; source .env; set +o allexport; \
	echo "Invalidating cache using Cloudflare API..." && \
	RESPONSE=$$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$$CF_ZONE_ID/purge_cache" \
	-H "Authorization: Bearer $$CLOUDFLARE_API_TOKEN" \
	-H "Content-Type: application/json" \
	--data '{"purge_everything":true}'); \
	echo "$$RESPONSE" | grep -q '"success":true' && echo "Success" || echo "Failure: $$RESPONSE"
