# Feature Branch Workflow Guide

This guide explains the proper workflow for contributing to TuneMeld with CI/CD and branch protection enabled.

## 🌟 Overview

With the new CI pipeline and branch protection rules, direct commits to `main` are no longer allowed. All changes must go through pull requests with passing CI tests.

## 🔄 Development Workflow

### 1. Start a New Feature

```bash
# Make sure you're on main and it's up to date
git checkout main
git pull origin main

# Create a new feature branch
git checkout -b feature/your-feature-name
# or for bug fixes:
git checkout -b fix/bug-description
# or for improvements:
git checkout -b improve/enhancement-name
```

### 2. Make Your Changes

```bash
# Edit files as needed
# Pre-commit hooks will automatically format your code

# Stage and commit changes
git add .
git commit -m "Add descriptive commit message"

# Push to your feature branch
git push origin feature/your-feature-name
```

### 3. Create Pull Request

```bash
# Using GitHub CLI (recommended)
gh pr create --title "Feature: Your feature title" --body "Description of changes"

# Or visit GitHub and create PR manually
```

### 4. CI Pipeline Runs Automatically

The following checks will run automatically:

- ✅ **Code Formatting** (ruff format)
- ✅ **Linting** (ruff check)
- ✅ **Type Checking** (mypy)
- ✅ **Unit Tests** (pytest)
- ✅ **Integration Tests** (pytest)
- ✅ **Django Tests** (if applicable)
- ✅ **Security Scans** (safety, bandit)

### 5. Review and Merge

1. **Wait for CI checks** to pass ✅
2. **Request code review** from team members
3. **Address feedback** if needed
4. **Merge when approved** and all checks pass

## 🛠️ Common Development Tasks

### Running Tests Locally

```bash
# Run all unit tests
make test

# Run specific test types
pytest tests/ -m "not integration and not slow"    # Unit tests only
pytest tests/ -m "integration"                      # Integration tests
pytest tests/ -m "slow"                            # Slow tests

# Run with coverage
pytest tests/ --cov=playlist_etl --cov-report=html
```

### Code Quality Checks

```bash
# Format code (happens automatically on commit)
make format

# Run linting
make lint

# Type checking
mypy playlist_etl --ignore-missing-imports
```

### Working with Pre-commit Hooks

```bash
# Install pre-commit hooks (one-time setup)
make install-pre-commit

# Run hooks manually
pre-commit run --all-files

# Skip hooks for emergency commits (not recommended)
git commit --no-verify -m "Emergency fix"
```

## 🚫 What's Blocked

### Direct Commits to Main

```bash
# ❌ This will be rejected
git checkout main
git commit -m "Direct commit"
git push origin main
# Error: Branch protection rules prevent direct pushes
```

### Merging Without CI

- Pull requests cannot be merged if CI checks fail
- At least one approval is required
- All conversations must be resolved

## 🔧 Troubleshooting

### CI Fails But Tests Pass Locally

```bash
# Check Python version compatibility
python --version  # Should be 3.10+

# Ensure all dependencies are installed
pip install -e .

# Run tests in same environment as CI
docker run -it python:3.10 bash
# ... install deps and run tests
```

### Pre-commit Hooks Failing

```bash
# Update hooks
pre-commit autoupdate

# Clear cache and retry
pre-commit clean
pre-commit run --all-files
```

### MongoDB Connection Issues in CI

The CI pipeline includes a MongoDB container, but local development may use different settings:

```bash
# Check your local MongoDB connection
export MONGODB_URI="mongodb://localhost:27017/tunemeld_test"
python -c "from playlist_etl.mongo_db_client import MongoDBClient; MongoDBClient()"
```

## 📚 Branch Naming Conventions

Use descriptive branch names with prefixes:

- `feature/add-spotify-integration` - New features
- `fix/mongodb-connection-error` - Bug fixes
- `improve/aggregation-performance` - Enhancements
- `docs/update-readme` - Documentation updates
- `test/increase-coverage` - Test improvements
- `refactor/cleanup-transform-module` - Code refactoring

## 🎯 Best Practices

### Commit Messages

Use clear, descriptive commit messages:

```bash
# ✅ Good
git commit -m "Add ISRC validation to track aggregation"
git commit -m "Fix MongoDB connection timeout in tests"
git commit -m "Improve error handling in Spotify API client"

# ❌ Avoid
git commit -m "fix stuff"
git commit -m "updates"
git commit -m "wip"
```

### Small, Focused PRs

- Keep PRs focused on a single feature or fix
- Aim for <400 lines of changes when possible
- Split large features into multiple PRs

### Testing

- Add tests for new features
- Update tests when changing existing code
- Ensure integration tests pass for cross-service changes

## 🚀 Advanced Workflows

### Working on Large Features

```bash
# Create feature branch
git checkout -b feature/large-feature

# Make incremental commits
git commit -m "Part 1: Add data models"
git commit -m "Part 2: Implement extraction logic"
git commit -m "Part 3: Add integration tests"

# Keep branch updated with main
git checkout main
git pull origin main
git checkout feature/large-feature
git rebase main  # or git merge main
```

### Emergency Hotfixes

For critical production issues:

```bash
# Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug-fix

# Make minimal fix
git commit -m "Fix critical issue X"
git push origin hotfix/critical-bug-fix

# Create PR with priority label
gh pr create --title "HOTFIX: Critical bug fix" --label "priority:high"
```

## 📞 Getting Help

- **CI Failures**: Check the Actions tab in GitHub for detailed logs
- **Branch Protection Issues**: See `BRANCH_PROTECTION_SETUP.md`
- **Test Failures**: Run tests locally first, check environment setup
- **Pre-commit Problems**: Clear cache with `pre-commit clean`

---

_This workflow ensures code quality while maintaining development velocity_ 🚀
