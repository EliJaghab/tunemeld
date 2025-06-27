#!/bin/bash

# Get PR Context - Fetch recent open PRs for assistant context
# Usage: ./scripts/get-pr-context.sh [number_of_prs]

MAX_PRS=${1:-5}

echo "## Current Open PRs Context"
echo ""
echo "Recent open pull requests that provide important context for development:"

gh api repos/$(gh repo view --json owner,name --jq '.owner.login + "/" + .name')/pulls \
  --jq '.[] | select(.state=="open") | {number: .number, title: .title, html_url: .html_url, body: .body}' \
  | head -$((MAX_PRS * 4)) \
  | jq -s '.[0:'$MAX_PRS']' \
  | jq -r '.[] | "- **PR #\(.number)**: \(.title) - [View PR](\(.html_url))"'

echo ""
echo "**Problem Summary**: Use this context to understand current development priorities and ongoing work."
