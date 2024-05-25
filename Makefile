# Makefile

.PHONY: format lint fix

# Linting and formatting combined targets
lint:
	@echo "Linting code with tox..."
	tox -e lint

format:
	@echo "Formatting code with tox..."
	tox -e format

fix: format
	@echo "Automatically fixing code style issues..."

# Default target to lint and format everything
all: lint format
