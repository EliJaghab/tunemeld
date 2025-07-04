#!/usr/bin/env node

/**
 * Railway MCP Setup Script for TuneMeld
 * Cross-platform setup script for Railway MCP configuration
 */

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");
const os = require("os");

// Colors for console output
const colors = {
  red: "\x1b[31m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  reset: "\x1b[0m",
};

function printStatus(message) {
  console.log(`${colors.green}[INFO]${colors.reset} ${message}`);
}

function printWarning(message) {
  console.log(`${colors.yellow}[WARNING]${colors.reset} ${message}`);
}

function printError(message) {
  console.log(`${colors.red}[ERROR]${colors.reset} ${message}`);
}

function printStep(message) {
  console.log(`${colors.blue}[STEP]${colors.reset} ${message}`);
}

function getClaudeConfigPath() {
  const platform = os.platform();
  const homeDir = os.homedir();

  switch (platform) {
    case "darwin": // macOS
      return path.join(homeDir, "Library", "Application Support", "Claude");
    case "linux":
      return path.join(homeDir, ".config", "claude-desktop");
    case "win32": // Windows
      return path.join(process.env.APPDATA || homeDir, "Claude");
    default:
      throw new Error(`Unsupported platform: ${platform}`);
  }
}

function promptForToken() {
  return new Promise(resolve => {
    process.stdout.write("Please enter your Railway API token: ");
    process.stdin.setRawMode(true);
    process.stdin.resume();
    process.stdin.setEncoding("utf8");

    let token = "";

    process.stdin.on("data", char => {
      if (char === "\u0003") {
        // Ctrl+C
        process.exit();
      } else if (char === "\r" || char === "\n") {
        process.stdin.setRawMode(false);
        process.stdin.pause();
        console.log(""); // New line after hidden input
        resolve(token);
      } else if (char === "\u0008" || char === "\u007f") {
        // Backspace
        if (token.length > 0) {
          token = token.slice(0, -1);
          process.stdout.write("\b \b");
        }
      } else {
        token += char;
        process.stdout.write("*");
      }
    });
  });
}

async function main() {
  console.log("🚄 Setting up Railway MCP for TuneMeld...\n");

  try {
    // Check if we're in the right directory
    if (!fs.existsSync("package.json") || !fs.existsSync("railway-mcp")) {
      printError("This script must be run from the tunemeld project root directory");
      process.exit(1);
    }

    // Step 1: Build Railway MCP server
    printStep("1. Building Railway MCP server...");

    process.chdir("railway-mcp");

    printStatus("Installing dependencies...");
    execSync("npm install", { stdio: "inherit" });

    printStatus("Building TypeScript to JavaScript...");
    execSync("npm run build", { stdio: "inherit" });

    if (!fs.existsSync("build/index.js")) {
      printError("Build failed - build/index.js not found");
      process.exit(1);
    }

    printStatus("✅ Railway MCP server built successfully");

    // Step 2: Get Railway API token
    printStep("2. Railway API Token setup...");
    console.log();
    console.log("To use Railway MCP, you need a Railway API token.");
    console.log("You can get one at: https://railway.app/account/tokens");
    console.log();

    let railwayToken = process.argv[2];

    if (!railwayToken) {
      railwayToken = await promptForToken();
    }

    if (!railwayToken) {
      printError("Railway API token is required");
      process.exit(1);
    }

    // Step 3: Setup Claude Desktop configuration
    printStep("3. Configuring Claude Desktop...");

    const projectRoot = path.resolve("..");
    const mcpPath = path.join(projectRoot, "railway-mcp", "build", "index.js");

    const claudeConfigDir = getClaudeConfigPath();
    const claudeConfigFile = path.join(claudeConfigDir, "claude_desktop_config.json");

    // Create config directory if it doesn't exist
    if (!fs.existsSync(claudeConfigDir)) {
      fs.mkdirSync(claudeConfigDir, { recursive: true });
    }

    let config = {};

    // Load existing config if it exists
    if (fs.existsSync(claudeConfigFile)) {
      printStatus("Updating existing Claude Desktop configuration...");

      // Backup existing config
      const backupFile = `${claudeConfigFile}.backup.${Date.now()}`;
      fs.copyFileSync(claudeConfigFile, backupFile);
      printStatus("Backed up existing configuration");

      try {
        const configData = fs.readFileSync(claudeConfigFile, "utf8");
        config = JSON.parse(configData);
      } catch (error) {
        printWarning("Could not parse existing config, creating new one");
        config = {};
      }
    } else {
      printStatus("Creating new Claude Desktop configuration...");
    }

    // Update config with Railway MCP
    if (!config.mcpServers) {
      config.mcpServers = {};
    }

    config.mcpServers["railway-mcp"] = {
      command: "node",
      args: [mcpPath],
      env: {
        RAILWAY_API_TOKEN: railwayToken,
      },
    };

    // Write updated config
    fs.writeFileSync(claudeConfigFile, JSON.stringify(config, null, 2));
    printStatus("✅ Claude Desktop configuration updated");

    // Step 4: Test the setup
    printStep("4. Testing Railway MCP setup...");

    process.chdir(projectRoot);

    if (fs.existsSync("test-railway-mcp.js")) {
      printStatus("Running Railway MCP test...");
      try {
        execSync("node test-railway-mcp.js", {
          stdio: "inherit",
          env: { ...process.env, RAILWAY_API_TOKEN: railwayToken },
        });
        printStatus("✅ Railway MCP test passed");
      } catch (error) {
        printWarning("Railway MCP test failed, but setup may still work");
      }
    } else {
      printWarning("Test file not found, skipping test");
    }

    // Step 5: Final instructions
    printStep("5. Setup complete!");
    console.log();
    console.log("🎉 Railway MCP has been successfully configured!");
    console.log();
    console.log("Configuration details:");
    console.log(`  • MCP Server: ${mcpPath}`);
    console.log(`  • Config File: ${claudeConfigFile}`);
    console.log("  • API Token: [HIDDEN]");
    console.log();
    console.log("Next steps:");
    console.log("  1. Restart Claude Desktop to load the new configuration");
    console.log('  2. Try commands like: "List my Railway projects"');
    console.log("  3. See railway-mcp-config.md for detailed usage instructions");
    console.log();
    console.log("Troubleshooting:");
    console.log("  • If Claude doesn't recognize Railway commands, restart Claude Desktop");
    console.log("  • Check that your Railway API token has the necessary permissions");
    console.log("  • Verify Node.js is installed and accessible");
    console.log();
    printStatus("Setup completed successfully! 🚄");
  } catch (error) {
    printError(`Setup failed: ${error.message}`);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { main };
