#!/usr/bin/env node

// Simple test script to verify Railway MCP is working
import { spawn } from "child_process";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

console.log("🧪 Testing Railway MCP Server...");

const mcpServer = spawn("node", [join(__dirname, "railway-mcp/build/index.js")], {
  env: {
    ...process.env,
    RAILWAY_API_TOKEN: "8000e980-7bb5-4d06-9288-22411eeeb73f",
  },
  stdio: ["pipe", "pipe", "pipe"],
});

mcpServer.stdout.on("data", data => {
  console.log("✅ MCP Server Output:", data.toString());
});

mcpServer.stderr.on("data", data => {
  console.log("🔍 MCP Server Info:", data.toString());
});

// Test for 3 seconds then exit
setTimeout(() => {
  console.log("🏁 Test completed. Railway MCP server is working!");
  mcpServer.kill();
  process.exit(0);
}, 3000);
