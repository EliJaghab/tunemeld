# Railway MCP Configuration

## Overview

This document describes the Railway MCP (Model Context Protocol) server setup for the TuneMeld project. The Railway MCP server enables AI agents to manage Railway.app infrastructure through natural language commands.

## Quick Setup (Recommended)

For easy setup on any system, use the automated setup script:

### Option 1: Interactive Setup

```bash
# Run from the tunemeld project root
node scripts/setup-railway-mcp.js
```

### Option 2: With Token Argument

```bash
# Pass your Railway API token as an argument
node scripts/setup-railway-mcp.js YOUR_RAILWAY_API_TOKEN
```

### Option 3: Bash Script (Unix/Linux/macOS)

```bash
# Run from the tunemeld project root
./scripts/setup-railway-mcp.sh
```

The setup script will:

- Build the Railway MCP server
- Configure Claude Desktop automatically
- Test the setup
- Provide troubleshooting tips

**Get your Railway API token at:** https://railway.app/account/tokens

## Configuration

### Claude Desktop Configuration

The Railway MCP server is configured in the Claude Desktop configuration file:

**Location:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "railway-mcp": {
      "command": "node",
      "args": ["/Users/eli/github/tunemeld/railway-mcp/build/index.js"],
      "env": {
        "RAILWAY_API_TOKEN": "8000e980-7bb5-4d06-9288-22411eeeb73f"
      }
    }
  }
}
```

### Server Details

- **Package:** `@jasontanswe/railway-mcp` v1.3.0
- **Source:** `/Users/eli/github/tunemeld/railway-mcp/`
- **Built executable:** `/Users/eli/github/tunemeld/railway-mcp/build/index.js`
- **API Token:** Configured in environment variable `RAILWAY_API_TOKEN`

## Features

The Railway MCP server provides the following capabilities:

- **Project Management:** List, create, and delete Railway projects
- **Service Management:** Create services from GitHub repos or Docker images, list services, restart services
- **Deployment Management:** List deployments, trigger deployments, view deployment logs
- **Variable Management:** List, create, update, and delete environment variables
- **Database Support:** Create and manage database services
- **Volume Management:** Create and manage persistent volumes
- **Network Management:** Configure TCP proxies and custom domains

## Usage

Once configured, Claude Code can interact with Railway.app through natural language commands:

- "List all my Railway projects"
- "Create a new service from my GitHub repo"
- "Deploy the latest changes to production"
- "Show me the logs for the latest deployment"
- "Set an environment variable for my service"

## Testing

The Railway MCP server can be tested using the included test script:

```bash
cd /Users/eli/github/tunemeld
node test-railway-mcp.js
```

## Build Instructions

To rebuild the Railway MCP server:

```bash
cd /Users/eli/github/tunemeld/railway-mcp
npm install
npm run build
```

## Security

- The Railway API token provides full access to your Railway account
- Keep the token secure and do not commit it to version control
- The token is stored in the Claude Desktop configuration file
- All API calls use HTTPS for secure communication

## Troubleshooting

If the Railway MCP server is not working:

1. Verify the API token is valid in the Railway dashboard
2. Check that the built index.js file exists at the configured path
3. Ensure Node.js is installed and accessible
4. Restart Claude Desktop after configuration changes
5. Check the Railway API status for any service disruptions
