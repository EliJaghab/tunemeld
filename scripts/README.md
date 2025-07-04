# TuneMeld Scripts

## Railway MCP Setup

Automated setup scripts for Railway MCP (Model Context Protocol) configuration.

### setup-railway-mcp.js

Cross-platform Node.js script for Railway MCP setup.

**Usage:**

```bash
# Interactive setup (recommended)
node scripts/setup-railway-mcp.js

# With token argument
node scripts/setup-railway-mcp.js YOUR_RAILWAY_API_TOKEN
```

**Features:**

- Cross-platform compatibility (Windows, macOS, Linux)
- Interactive token input with hidden characters
- Automatic Claude Desktop configuration
- Built-in testing and validation
- Backup of existing configurations

### setup-railway-mcp.sh

Bash script for Unix-like systems (Linux, macOS).

**Usage:**

```bash
# Make executable and run
chmod +x scripts/setup-railway-mcp.sh
./scripts/setup-railway-mcp.sh

# With token argument
./scripts/setup-railway-mcp.sh YOUR_RAILWAY_API_TOKEN
```

**Features:**

- Bash-based setup with colored output
- JSON manipulation with jq (optional)
- Automatic dependency detection
- Comprehensive error handling

## What These Scripts Do

1. **Build Railway MCP Server**

   - Install npm dependencies
   - Compile TypeScript to JavaScript
   - Verify build success

2. **Configure Claude Desktop**

   - Detect OS and find Claude config directory
   - Create or update `claude_desktop_config.json`
   - Backup existing configurations
   - Set Railway API token securely

3. **Test Setup**

   - Run Railway MCP test suite
   - Verify API token authentication
   - Validate server functionality

4. **Provide Instructions**
   - Clear next steps for users
   - Troubleshooting guidance
   - Feature overview

## Requirements

- Node.js (for building and running the MCP server)
- Railway.app account and API token
- Claude Desktop application
- Internet connection for npm packages

## Getting Your Railway API Token

1. Go to https://railway.app/account/tokens
2. Click "Create New Token"
3. Give it a descriptive name
4. Copy the token (it will only be shown once)
5. Use it with the setup script

## Troubleshooting

- **"This script must be run from the tunemeld project root"**: Make sure you're in the correct directory
- **Build fails**: Check that Node.js is installed and npm is working
- **Claude doesn't recognize commands**: Restart Claude Desktop after setup
- **API token invalid**: Verify your token at railway.app/account/tokens
