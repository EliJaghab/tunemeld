# Makefile

.PHONY: format lint fix

# Linting and formatting combined targets
lint:
	@echo "Linting code with tox..."
	tox -e lint

format:
	@echo "Formatting code with tox..."
	tox -e format

<<<<<<< Updated upstream
fix: format
	@echo "Automatically fixing code style issues..."
=======
imports:
	@echo "Organizing imports..."
	@goimports -w .

tidy: fmt simplify imports lint
	@echo "Tidying Go code..."

run-extract2:
	@echo "Sourcing API credentials and running extract command..."
	@bash -c "source api_credentials.sh && python migration/extractors.py"

run-extract:
	@echo "Sourcing API credentials and running extract command..."
	@bash -c "source api_credentials.sh && go run cmd/extract/main.go"

run-transform2:
	@bash -c "python migration/transformers.py"

run-transform:
	@echo "Building and running transform command..."
	@bash -c "source api_credentials.sh && go run cmd/transform/main.go"

run-gold:
	@echo "Running gold transform..."
	@bash -c "go run cmd/gold/main.go"

run-extract-actions:
	@bash -c "go run cmd/extract/main.go"

run-transform-actions:
	@bash -c "go run cmd/transform/main.go"

start-server:
	python -m http.server 8000
>>>>>>> Stashed changes

# Default target to lint and format everything
all: lint format
