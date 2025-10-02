# TuneMeld Development Guide

## Requirements

**Python 3.12+** - Project requires Python 3.12 or newer for Vercel compatibility. Python 3.13+ is preferred for local development but Vercel's @vercel/python runtime currently only supports up to Python 3.12.

## Server Management - ALWAYS USE MAKEFILE COMMANDS

**NEVER start servers manually. ALWAYS use these Makefile commands:**

```bash
# Start servers (use these commands ONLY)
make serve-frontend    # Starts frontend at http://localhost:8080
make serve-backend     # Starts backend at http://localhost:8000 (ensures Redis is running)
make serve-redis       # Manually start Redis cache if needed (normally run by make serve-backend)

# Stop servers (use these commands ONLY)
make kill-frontend     # Stops frontend server
make kill-backend      # Stops backend server
make kill-redis        # Stops local Redis instance started by make serve-redis
```

**DO NOT use manual commands like:**

- ❌ `python -m http.server 8080`
- ❌ `cd backend && python manage.py runserver`
- ❌ `source venv/bin/activate && ...`

**The Makefile handles all environment setup, virtual environment activation, and proper server configuration.**

## MCP Servers

**Playwright MCP:** Browser automation and web testing.

**Vercel MCP:** Deployment management and debugging. Use `mcp__vercel__*` tools for:

- Viewing deployment logs and build errors
- Managing Vercel projects and deployments
- Analyzing deployment status and performance
- Project-specific access configured for tunemeld project

## Cache Architecture

**TuneMeld uses a two-tier cache system:**

### Default Cache (`cache` / `caches["default"]`)

- **Purpose**: CloudflareKV for Django operations (ETL, raw API data)
- **Data**: Spotify playlists, YouTube URLs, RapidAPI responses, SoundCloud data, Apple Music covers
- **Usage**: All Django management commands, ETL pipelines, and operational data
- **Why CloudflareKV**:
  1. **API Rate Limits**: RapidAPI and YouTube API have strict limits - caching prevents hitting quotas
  2. **Performance**: Much faster to pull from CloudflareKV than rescraping/refetching from external APIs

### Redis Cache (`caches["redis"]`)

- **Purpose**: Vercel Redis for GraphQL query results ONLY
- **Data**: GQL_PLAYLIST, GQL_PLAY_COUNT, GQL_PLAYLIST_METADATA
- **Usage**: GraphQL query responses served to the frontend
- **Notes**: Cached entries are keyed by `CachePrefix` enums and stored via `core.utils.redis_cache`

**Simple rule: CloudflareKV for Django/ETL operations, Redis for GraphQL.**

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

## Constants vs Hardcoded Strings

**ALWAYS use defined constants instead of hardcoded strings:**

- Use `ServiceName.SPOTIFY` not `"spotify"`
- Use `ServiceName.APPLE_MUSIC` not `"apple_music"`
- Use defined enum/constant values for any string that represents a business concept
- **NEVER** accept both string and constant types in function parameters - pick one and enforce it
- **NEVER** add fallback logic to convert strings to constants - fail fast instead

## Import Style

**NEVER use inline imports within functions. ALL imports must be at the top of the file.**

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
