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

## Agentree Integration

Agentree is installed and available for creating isolated development environments for AI agents working on separate features or bug fixes.

### What Agentree Does

- Creates isolated Git worktrees (parallel directories) for each AI agent
- Automatically copies all environment files (.env, credentials, etc.)
- Installs dependencies in the new environment
- Allows multiple agents to work on different features simultaneously without conflicts

### Usage

When asked to create a PR or work on a separate feature using agents:

```bash
# Create a new isolated environment for an agent
agentree -b <branch-name>

# Interactive setup
agentree -i
```

### Example Workflow

1. User requests: "Create an agent to fix the authentication bug"
2. Run: `agentree -b fix-auth-bug`
3. This creates:
   - New worktree at: `/Users/eli/github/tunemeld-worktrees/agent-fix-auth-bug`
   - New branch: `agent/fix-auth-bug`
   - Copies all env files and installs dependencies
4. The agent can work in isolation without affecting the main codebase

### Multiple Simultaneous Agents

Agentree supports **unlimited concurrent agents** working simultaneously on different tasks:

```bash
# Agent 1: Fix authentication
agentree -b fix-auth-bug

# Agent 2: Add dark mode (while Agent 1 is still working)
agentree -b add-dark-mode

# Agent 3: Optimize database queries (while others continue)
agentree -b optimize-db-performance

# Agent 4: Refactor test suite
agentree -b refactor-tests
```

**Each agent gets complete isolation:**

- Own directory: `/Users/eli/github/tunemeld-worktrees/agent-<task>/`
- Own Git branch: `agent/<task>`
- Own environment files and dependencies
- No interference with other agents

**Benefits:**

- **Parallel Development**: Multiple features/fixes can be developed simultaneously
- **Clean PRs**: Each agent creates focused, isolated pull requests
- **No Cross-Contamination**: Changes from one agent don't affect others
- **Resource Efficient**: Shared base repo, separate working environments

### Important Notes

- Agentree creates worktrees outside the main repository directory
- Each agent gets its own branch prefixed with `agent/`
- All environment files are automatically copied to maintain consistency
- Dependencies are installed automatically in the new environment

### Critical Usage Warning ⚠️

**IMPORTANT**: After running `agentree -b <branch-name>`, you MUST work in the created worktree directory, NOT in the original repository directory.

**Wrong way** (will pull in unrelated changes):

```bash
agentree -b fix-bug
# Still working in /Users/eli/github/tunemeld/ ❌
# This will include uncommitted changes from other branches!
```

**Correct way** (clean isolated environment):

```bash
agentree -b fix-bug
# Work in /Users/eli/github/tunemeld-worktrees/agent-fix-bug/ ✅
# This has ONLY the clean base branch without contamination
```

**Why this matters**: The worktree directory contains a clean copy from the base branch without any uncommitted changes from other work. Working in the original directory defeats the purpose of isolation and will create PRs with unrelated files.

### Best Practice: Always Start from Latest Main ⚠️

**CRITICAL**: Before creating an agentree, always ensure you're starting from the latest main/master branch to avoid working with stale code:

```bash
# ALWAYS do this first - pull latest changes
git checkout master  # or main
git pull origin master

# THEN create the agentree
agentree -b fix-specific-issue
```

**Why this is essential**:

- **Avoids merge conflicts**: Working from latest code prevents integration issues
- **Prevents stale fixes**: Ensures you're not fixing problems already resolved
- **Clean PRs**: Reduces contamination from outdated branches
- **Current dependencies**: Ensures you have the latest package versions and configurations

**Warning Signs of Stale Base**:

- Tests failing that should pass
- Import errors that don't make sense
- Features behaving differently than expected
- PRs with unexpected file changes

# important-instruction-reminders

Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (\*.md) or README files. Only create documentation files if explicitly requested by the User.

## Communication Guidelines

### Thread-Relevant PR Context

**Include only PRs relevant to current conversation:**

- Show PRs created or worked on during the current session
- Include PRs that are contextually related to the current task/problem
- Add brief status and next steps for each relevant PR
- Format: "**Work completed:** [PR description and link] - Status: [ready for review/needs changes/etc.]"

### PR Link Guidelines

**Include PR links at the end of messages when relevant:**

- If a PR was created or worked on during the session, include the PR URL as a clickable hyperlink at the bottom of your response
- Format: `**Related PR:** [Description](https://github.com/owner/repo/pull/number)`
- This helps the user quickly access context and track progress
- Include this even for brief responses when a PR is relevant
