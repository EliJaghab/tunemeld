# TuneMeld Development Guide

## Requirements

**Python 3.13+** - Project requires Python 3.13 or newer. Python 3.10-3.12 are obsolete for this project.

## Server Management - ALWAYS USE MAKEFILE COMMANDS

**NEVER start servers manually. ALWAYS use these Makefile commands:**

```bash
# Start servers (use these commands ONLY)
make serve-frontend    # Starts frontend at http://localhost:8080
make serve-backend     # Starts backend at http://localhost:8000

# Stop servers (use these commands ONLY)
make kill-frontend     # Stops frontend server
make kill-backend      # Stops backend server
```

**DO NOT use manual commands like:**

- ❌ `python -m http.server 8080`
- ❌ `cd backend && python manage.py runserver`
- ❌ `source venv/bin/activate && ...`

**The Makefile handles all environment setup, virtual environment activation, and proper server configuration.**

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

## ETL Commands

```bash
make run-view-count-etl      # Full view count extraction
make test-view-count-etl     # Limited extraction for testing (10 tracks)
make run-playlist-etl        # Full playlist extraction
```

**DO NOT ADD COMMENTS unless explicitly asked. Write clean, self-documenting code.**

## Comment Policy - Comments Are Code Smells

**NEVER add these types of comments:**

- **Redundant comments** that just repeat what the code does (e.g., `// Stores the user's name` above a property)
- **Excessive comments** that narrate every single line of code
- **Outdated comments** that no longer match the implementation
- **Obvious comments** that state what's already clear from the code

**Only acceptable comments:**

- **Business logic explanations** that explain WHY something is done (e.g., payment gateway rounding requirements)
- **External references** to documentation, specs, or contracts (e.g., SLA section references)
- **API documentation** with proper structured format for public interfaces

**When in doubt, remove the comment and make the code more self-documenting instead.**

**NEVER add fallbacks or workarounds as fixes - identify and fix root causes in the backend/data pipeline instead.**

**NEVER add sneaky fallback values or default configurations - if something is required, make it fail explicitly rather than silently using defaults.**

**NEVER disable tools, linting, or validation to work around errors unless explicitly requested. Always fix the root cause.**

**ALWAYS use Python 3.11+ built-in types for type hints:**

- Use `list[str]` not `List[str]`
- Use `dict[str, int]` not `Dict[str, int]`
- Use `str | None` not `Optional[str]`
- Use `int | str` not `Union[int, str]`
- No imports from `typing` for basic types (list, dict, tuple, set)

## Response Format

**When completing tasks, always end with a summary that includes:**

1. **Problem identified** - Brief description of what was wrong
2. **Solution implemented** - List of changes with exact file paths and line numbers using `file_path:line_number` format
3. **Verification** - How the fix was tested/verified

**Example:**

```
## Problem Identified
The SoundCloud playlist title was displaying malformed Unicode characters.

## Solution Implemented
1. Created Unicode cleaning utility at `/path/to/file.py:121`
2. Updated SoundCloud service at `/path/to/service.py:33,36` to use cleaning function
3. Fixed existing database records with migration script

## Verification
GraphQL now returns proper Unicode characters instead of malformed bytes.
```
