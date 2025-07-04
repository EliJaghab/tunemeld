#!/bin/bash

# Railway MCP Setup Script for TuneMeld
# This script sets up Railway MCP for any user on any system

set -e

echo "🚄 Setting up Railway MCP for TuneMeld..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if we're in the right directory
if [[ ! -f "package.json" ]] || [[ ! -d "railway-mcp" ]]; then
    print_error "This script must be run from the tunemeld project root directory"
    exit 1
fi

# Step 1: Build Railway MCP server
print_step "1. Building Railway MCP server..."
cd railway-mcp

# Install dependencies
print_status "Installing dependencies..."
npm install

# Build the server
print_status "Building TypeScript to JavaScript..."
npm run build

if [[ ! -f "build/index.js" ]]; then
    print_error "Build failed - build/index.js not found"
    exit 1
fi

print_status "✅ Railway MCP server built successfully"

# Step 2: Get Railway API token
print_step "2. Railway API Token setup..."
echo ""
echo "To use Railway MCP, you need a Railway API token."
echo "You can get one at: https://railway.app/account/tokens"
echo ""

# Check if token is provided as argument
if [[ -n "$1" ]]; then
    RAILWAY_TOKEN="$1"
    print_status "Using provided Railway API token"
else
    # Interactive token input
    echo "Please enter your Railway API token:"
    read -s RAILWAY_TOKEN
    echo ""
fi

if [[ -z "$RAILWAY_TOKEN" ]]; then
    print_error "Railway API token is required"
    exit 1
fi

# Step 3: Setup Claude Desktop configuration
print_step "3. Configuring Claude Desktop..."

# Get the absolute path to the built index.js
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MCP_PATH="$PROJECT_ROOT/railway-mcp/build/index.js"

# Detect OS and set Claude config path
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    CLAUDE_CONFIG_DIR="$HOME/.config/claude-desktop"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    CLAUDE_CONFIG_DIR="$APPDATA/Claude"
else
    print_warning "Unknown OS type: $OSTYPE"
    print_warning "Please manually set CLAUDE_CONFIG_DIR"
    exit 1
fi

CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"

# Create config directory if it doesn't exist
mkdir -p "$CLAUDE_CONFIG_DIR"

# Create or update Claude Desktop configuration
if [[ -f "$CLAUDE_CONFIG_FILE" ]]; then
    print_status "Updating existing Claude Desktop configuration..."

    # Backup existing config
    cp "$CLAUDE_CONFIG_FILE" "$CLAUDE_CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    print_status "Backed up existing configuration"

    # Use jq to update the config if available, otherwise manual JSON manipulation
    if command -v jq &> /dev/null; then
        # Use jq for safe JSON manipulation
        jq --arg mcp_path "$MCP_PATH" --arg token "$RAILWAY_TOKEN" \
           '.mcpServers["railway-mcp"] = {
              "command": "node",
              "args": [$mcp_path],
              "env": {
                "RAILWAY_API_TOKEN": $token
              }
            }' "$CLAUDE_CONFIG_FILE" > "$CLAUDE_CONFIG_FILE.tmp" && \
        mv "$CLAUDE_CONFIG_FILE.tmp" "$CLAUDE_CONFIG_FILE"
    else
        print_warning "jq not found, using manual JSON update"
        # Manual JSON update (basic approach)
        cat > "$CLAUDE_CONFIG_FILE" << EOF
{
  "mcpServers": {
    "railway-mcp": {
      "command": "node",
      "args": ["$MCP_PATH"],
      "env": {
        "RAILWAY_API_TOKEN": "$RAILWAY_TOKEN"
      }
    }
  }
}
EOF
    fi
else
    print_status "Creating new Claude Desktop configuration..."
    cat > "$CLAUDE_CONFIG_FILE" << EOF
{
  "mcpServers": {
    "railway-mcp": {
      "command": "node",
      "args": ["$MCP_PATH"],
      "env": {
        "RAILWAY_API_TOKEN": "$RAILWAY_TOKEN"
      }
    }
  }
}
EOF
fi

print_status "✅ Claude Desktop configuration updated"

# Step 4: Test the setup
print_step "4. Testing Railway MCP setup..."
cd "$PROJECT_ROOT"

# Test the MCP server
if [[ -f "test-railway-mcp.js" ]]; then
    print_status "Running Railway MCP test..."
    if RAILWAY_API_TOKEN="$RAILWAY_TOKEN" node test-railway-mcp.js; then
        print_status "✅ Railway MCP test passed"
    else
        print_warning "Railway MCP test failed, but setup may still work"
    fi
else
    print_warning "Test file not found, skipping test"
fi

# Step 5: Final instructions
print_step "5. Setup complete!"
echo ""
echo "🎉 Railway MCP has been successfully configured!"
echo ""
echo "Configuration details:"
echo "  • MCP Server: $MCP_PATH"
echo "  • Config File: $CLAUDE_CONFIG_FILE"
echo "  • API Token: [HIDDEN]"
echo ""
echo "Next steps:"
echo "  1. Restart Claude Desktop to load the new configuration"
echo "  2. Try commands like: 'List my Railway projects'"
echo "  3. See railway-mcp-config.md for detailed usage instructions"
echo ""
echo "Troubleshooting:"
echo "  • If Claude doesn't recognize Railway commands, restart Claude Desktop"
echo "  • Check that your Railway API token has the necessary permissions"
echo "  • Verify Node.js is installed and accessible"
echo ""
print_status "Setup completed successfully! 🚄"
