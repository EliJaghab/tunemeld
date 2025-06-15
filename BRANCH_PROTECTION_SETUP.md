# Branch Protection Setup Guide

This guide explains how to set up branch protection rules to prevent direct commits to the main branch and require CI tests to pass before merging.

## 🛡️ Required Branch Protection Rules

To implement the CI-based workflow, you need to configure the following branch protection rules on GitHub:

### 1. Access Repository Settings

1. Go to your repository on GitHub
2. Click on **Settings** tab
3. Navigate to **Branches** in the left sidebar

### 2. Add Branch Protection Rule

Click **Add rule** and configure:

#### Rule Name

- **Branch name pattern**: `main` (or `master` if that's your default branch)

#### Protection Settings

Enable these settings:

✅ **Require a pull request before merging**

- Require approvals: `1` (minimum)
- Dismiss stale PR approvals when new commits are pushed
- Require review from code owners (if you have CODEOWNERS file)

✅ **Require status checks to pass before merging**

- Require branches to be up to date before merging
- **Required status checks**:
  - `test (3.10)` - Core tests on Python 3.10
  - `test (3.11)` - Core tests on Python 3.11
  - `build-status` - Overall build status check

✅ **Require conversation resolution before merging**

✅ **Restrict pushes that create files larger than 100 MB**

#### Advanced Settings (Optional but Recommended)

✅ **Require linear history** - Keeps git history clean
✅ **Include administrators** - Apply rules to repo admins too
✅ **Allow force pushes** - ❌ Disabled for safety
✅ **Allow deletions** - ❌ Disabled for safety

### 3. Save Protection Rule

Click **Create** to save the branch protection rule.

## 🔄 Feature Branch Workflow

With branch protection enabled, your workflow becomes:

### For New Features/Fixes:

```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# Make your changes
# ... code changes ...

# Commit and push
git add .
git commit -m "Add your feature"
git push origin feature/your-feature-name

# Create pull request via GitHub UI or CLI
gh pr create --title "Add your feature" --body "Description of changes"
```

### CI Automatically Runs:

- ✅ Code formatting checks (ruff)
- ✅ Linting checks (ruff)
- ✅ Type checking (mypy)
- ✅ Unit tests (pytest)
- ✅ Integration tests (pytest)
- ✅ Django tests
- ✅ Security scans (safety, bandit)

### Merge Process:

1. **All CI checks must pass** ✅
2. **Code review required** 👥
3. **PR approved** ✅
4. **Merge to main** 🎉

## 🚀 Quick Setup Commands

If you have GitHub CLI installed:

```bash
# Enable branch protection via CLI
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["test (3.10)","test (3.11)","build-status"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
  --field restrictions=null
```

## 📊 Status Check Badges

Add build status badges to your README:

```markdown
![CI Status](https://github.com/your-username/tunemeld/workflows/CI%20Pipeline/badge.svg)
![Coverage](https://codecov.io/gh/your-username/tunemeld/branch/main/graph/badge.svg)
```

## 🔧 Troubleshooting

### Common Issues:

1. **Status checks not appearing**:

   - Ensure CI workflow has run at least once
   - Check that job names match exactly in workflow and branch protection

2. **CI fails on first run**:

   - MongoDB service may need more time to start
   - Check environment variables are set correctly

3. **Tests pass locally but fail in CI**:
   - Check Python version compatibility
   - Verify all dependencies are in requirements.txt
   - Environment variable differences

### Emergency Override:

If you need to bypass branch protection temporarily:

1. Go to Settings → Branches
2. Edit the protection rule
3. Uncheck "Include administrators"
4. Make your emergency commit
5. **Re-enable protection immediately**

## 📝 Next Steps

After setting up branch protection:

1. **Test the workflow**: Create a test PR to verify CI runs
2. **Update team documentation**: Share this workflow with collaborators
3. **Set up notifications**: Configure GitHub notifications for PR reviews
4. **Consider CODEOWNERS**: Add code review assignments for specific paths

---

_This setup ensures code quality and prevents broken code from reaching the main branch._ 🛡️
