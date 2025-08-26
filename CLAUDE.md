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

- **First check** for linting violations (fails if found)
- Run Ruff with aggressive fixes (including unsafe fixes)
- Run Prettier on JavaScript files
- Enforce double quotes in Python
- Enforce space indentation
- Ban relative imports
- Fix many code quality issues

**Formatting Standards:**

- **Python**: Double quotes, space indentation, no relative imports, no redundant inline comments
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

# Test playlist ETL pipeline (simulates playlist_etl GitHub workflow)
make test-playlist-etl

# Visual/UI testing
make test-header-art         # Test header art functionality
make test-visual             # Full visual regression tests
```

**Test Environment:**

- All tests use `.env.test` with fake API keys (safe to commit)
- No external API calls or costs incurred during testing
- Comprehensive mocking of Spotify, YouTube, Apple Music, and RapidAPI services

**Test File Naming Convention:**

- Django management command tests: `{command_name}_test.py` (e.g., `raw_extract_test.py`)
- General test files: `test_{module_name}.py` or `{module_name}_test.py`

**Test Code Style:**

- No docstrings or comments needed in test files
- Test method names should be self-documenting

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

## Railway Deployment & Debugging

**Railway MCP Integration:** Claude has access to Railway MCP tools for deployment monitoring and debugging.

**API Credentials:** Railway API token is available in `.env.dev` file:

```bash
RAILWAY_API_TOKEN=8000e980-7bb5-4d06-9288-22411eeeb73f
```

**Railway Commands Available:**

- Monitor deployment status and logs
- Check service health and configuration
- Debug failed deployments
- Manage environment variables
- View project and service information

**Project Information:**

- Project ID: `b6a14488-05cf-43ad-85be-995c7bae75d1`
- Service ID: `e791f98d-3033-4990-b159-b551f0e61f83` (tunemeld)
- Environment ID: `8910d930-6bd7-4742-90a7-3c59b1b42217` (production)

**Web Debugging:** Playwright MCP tools are available for browser automation and web testing.

## Development Workflow

1. **Start servers:** `make serve-frontend` and `make serve-backend`
2. **Make changes:** Edit code as needed
3. **Format code:** `make format`
4. **Test changes:** `make test-header-art` or `make test-visual`
5. **Run tests:** `make test`
6. **Run linting:** `ruff check .` (catches PEP 8 violations)
7. **Run pre-commit hooks:** `pre-commit run --all-files` (fails first, then fixes)
8. **Run type checking:** `mypy .` (catches type issues)
9. **Commit:** Pre-commit hooks will run automatically (will fail if violations found)
10. **Deploy:** `make pull_push` then `make prod`

## Environment Setup

```bash
# Setup Python environment
make setup_env

# Setup backend environment
make setup_backend_env

# Install development dependencies
make install-dev
```

# important-instruction-reminders

Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (\*.md) or README files. Only create documentation files if explicitly requested by the User.
