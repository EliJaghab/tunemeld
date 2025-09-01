# TuneMeld Development Guide

## Quick Start

```bash
make serve-frontend    # Frontend at http://localhost:8080
make serve-backend     # Backend at http://localhost:8000
make format           # Format and lint all code (pre-commit hooks)
```

## Railway & Playwright

**Railway MCP:** Monitor deployments, check service health, debug failures. Credentials in `.env.dev`.

**Playwright MCP:** Browser automation and web testing.

**Project Info:**

- Project: `b6a14488-05cf-43ad-85be-995c7bae75d1`
- Service: `e791f98d-3033-4990-b159-b551f0e61f83`
- Environment: `8910d930-6bd7-4742-90a7-3c59b1b42217`

## Development Workflow

1. `make serve-frontend` and `make serve-backend`
2. Edit code
3. `make format` (runs pre-commit hooks: ruff + prettier)
4. Commit and push (hooks auto-run)

**Claude Code must run `make format` (pre-commit hooks) before completing any coding task.**

**DO NOT ADD COMMENTS unless explicitly asked. Write clean, self-documenting code.**

**NEVER add fallbacks or workarounds as fixes - identify and fix root causes in the backend/data pipeline instead.**
