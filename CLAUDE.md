# TuneMeld Development Guide

## Quick Start

```bash
# Start frontend server (serves at http://localhost:8080)
make serve-frontend

# Start backend server (serves at http://localhost:8000)
make serve-backend

# Format all code before committing
make format

# Run tests
make test
```

## Server Commands

```bash
# Frontend static files server
make serve-frontend          # http://localhost:8080

# Django backend API server
make serve-backend           # http://localhost:8000

# Legacy frontend server (port 8080)
make serve                   # Alias for serve-frontend
```

## Code Formatting & Quality

```bash
# Format both Python and JavaScript files
make format

# Format only JavaScript files
make format-js

# Check formatting without fixing
make format-check

# Aggressively clean and format entire repository
make clean-repo

# Run linting checks
make lint

# Install pre-commit hooks
make install-pre-commit
```

**Pre-commit hooks automatically:**

- Run Ruff with aggressive fixes (including unsafe fixes)
- Run Prettier on JavaScript files
- Enforce double quotes in Python
- Enforce space indentation
- Ban relative imports
- Fix many code quality issues

**Formatting Standards:**

- **Python**: Double quotes, space indentation, no relative imports
- **JavaScript**: Prettier standard formatting
- **Jupyter notebooks**: Excluded from formatting

**CI Integration:** `make format-check` ensures builds fail if formatting is inconsistent.

## Testing Commands

```bash
# Run all tests
make test

# Run only unit tests (fast)
make test-unit

# Run integration tests
make test-integration

# Run tests with coverage
make test-coverage

# Visual/UI testing
make test-header-art         # Test header art functionality
make test-visual             # Full visual regression tests
```

**Visual Testing:** Screenshots saved to `screenshots/` directory (gitignored).

## Build & Deploy

```bash
# Pull latest changes and push (with rebase)
make pull_push

# Deploy to production
make prod

# Invalidate CDN cache
make invalidate_cache
```

## Development Workflow

1. **Start servers:** `make serve-frontend` and `make serve-backend`
2. **Make changes:** Edit code as needed
3. **Format code:** `make format`
4. **Test changes:** `make test-header-art` or `make test-visual`
5. **Run tests:** `make test`
6. **Commit:** Pre-commit hooks will run automatically
7. **Deploy:** `make pull_push` then `make prod`

## ETL Pipeline (Backend)

```bash
# Data pipeline commands
make extract                 # Extract playlist data
make transform               # Transform data
make aggregate               # Aggregate data
make view_count              # Update view counts
make historical_view_count   # Historical view count analysis
```

## Environment Setup

```bash
# Setup Python environment
make setup_env

# Setup backend environment
make setup_backend_env

# Install development dependencies
make install-dev
```
