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
	@echo "Building and running extract command..."
	@go run cmd/extract/main.go

# Run the transform command.
run-transform:
	@echo "Building and running transform command..."
	@go run cmd/transform/main.go

