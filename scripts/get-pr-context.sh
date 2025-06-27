#!/bin/bash

# Get Thread-Relevant PR Context - Show only PRs related to current work
# Usage: ./scripts/get-pr-context.sh [search_term]

SEARCH_TERM=${1:-""}

echo "## Thread-Relevant PR Context"
echo ""

if [ -n "$SEARCH_TERM" ]; then
    echo "PRs related to current work on: $SEARCH_TERM"
    gh api repos/$(gh repo view --json owner,name --jq '.owner.login + "/" + .name')/pulls \
      --jq '.[] | select(.state=="open") | select(.title | test("'$SEARCH_TERM'"; "i")) | {number: .number, title: .title, html_url: .html_url}' \
      | jq -r '"**Work completed:** \(.title) - [PR #\(.number)](\(.html_url)) - Status: Ready for review"'
else
    echo "**Work completed:** Use with search term to show relevant PRs"
fi
