# Makefile

.PHONY: format lint fix pull_push format_all

# Linting and formatting combined targets
lint:
	@echo "Linting code with tox..."
	tox -e lint

format:
	@echo "Formatting code with tox..."
	tox -e format

fix: format
	@echo "Automatically fixing code style issues..."

pull_push:
	@git pull --rebase
	@if [ $$? -ne 0 ]; then echo "Error: Failed to pull the latest changes. Aborting push."; exit 1; fi
	@git push
	@if [ $$? -ne 0 ]; then echo "Error: Failed to push the changes."; exit 1; fi
	@echo "Successfully pulled, rebased, and pushed the changes."

# Default target to lint and format everything
format_all: lint format fix
