.PHONY: fmt simplify lint fix imports

# Format the Go code.
fmt:
	@echo "Formatting Go code..."
	@go fmt ./...

# Simplify the Go code.
simplify:
	@echo "Simplifying Go code..."
	@gofmt -s -w .

# Check the Go code with golangci-lint.
lint:
	@echo "Linting Go code..."
	@golangci-lint run

# Auto-fix issues with golangci-lint (only works with some linters).
fix:
	@echo "Auto-fixing Go code..."
	@golangci-lint run --fix

# Organize imports.
imports:
	@echo "Organizing imports..."
	@goimports -w .

# Combine all the targets for a full tidy.
tidy: fmt simplify imports lint
	@echo "Tidying Go code..."

# Run the extract command.
run-extract:
	@echo "Sourcing API credentials and running extract command..."
	@bash -c "source api_credentials.sh && go run cmd/extract/main.go"

run-extract-actions:
	@bash -c "go run cmd/extract/main.go"

# Run the transform command.
run-transform:
	@echo "Building and running transform command..."
	@bash -c "source api_credentials.sh && go run cmd/transform/main.go"

run-transform-actions:
	@bash -c "go run cmd/transform/main.go"

start-server:
	python3 -m http.server 8000

