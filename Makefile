.PHONY: format_all lint fix pull_push

# Combined linting and formatting target
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