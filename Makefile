.PHONY: fmt simplify lint fix imports

fmt:
	@echo "Formatting Go code..."
	@go fmt ./...

simplify:
	@echo "Simplifying Go code..."
	@gofmt -s -w .

lint:
	@echo "Linting Go code..."
	@golangci-lint run

fix:
	@echo "Auto-fixing Go code..."
	@golangci-lint run --fix

imports:
	@echo "Organizing imports..."
	@goimports -w .

tidy: fmt simplify imports lint
	@echo "Tidying Go code..."

run-extract:
	@echo "Sourcing API credentials and running extract command..."
	@bash -c "source api_credentials.sh && go run cmd/extract/main.go"

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

