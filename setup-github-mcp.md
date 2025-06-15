# Setting up GitHub MCP for Claude Code

## Option 1: Official GitHub MCP Server

1. Install the GitHub MCP server:

```bash
npm install -g @modelcontextprotocol/server-github
```

2. Configure it in your Claude Desktop config:

```json
{
  "mcpServers": {
    "github": {
      "command": "mcp-server-github",
      "args": [],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your_github_token_here"
      }
    }
  }
}
```

## Option 2: Community GitHub MCP Servers

Several community options available:

- `mcp-server-github` - Full GitHub API access
- `github-mcp` - Lightweight GitHub integration
- `mcp-github-tools` - Focused on repository operations

## Current Setup (GitHub CLI)

For now, we're successfully using GitHub CLI which provides:

- ✅ Action run monitoring (`gh run list`, `gh run view`)
- ✅ PR creation and management (`gh pr create`, `gh pr view`)
- ✅ Repository operations (`gh repo view`)
- ✅ Issue tracking (`gh issue list`)

## Recommended: Stick with GitHub CLI for now

The GitHub CLI approach is working well and provides all needed functionality.
MCP integration would be nice-to-have but isn't essential for our current workflow.
