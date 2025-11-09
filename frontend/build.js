#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const DIST_DIR = path.join(__dirname, "dist");
const SRC_DIR = path.join(__dirname, "src");
const STATIC_FILES = ["index.html", "index-v2.html", "css", "images", "html"];

const log = {
  info: (msg) => console.log(`[INFO] ${msg}`),
  success: (msg) => console.log(`[SUCCESS] ${msg}`),
  error: (msg) => console.error(`[ERROR] ${msg}`),
  warn: (msg) => console.warn(`[WARN] ${msg}`),
  build: (msg) => console.log(`[BUILD] ${msg}`),
};

log.build("Starting TuneMeld frontend production build");

// Clean dist directory
if (fs.existsSync(DIST_DIR)) {
  fs.rmSync(DIST_DIR, { recursive: true });
}
fs.mkdirSync(DIST_DIR);
log.info("Cleaned dist directory");

// Verify src directory exists
if (!fs.existsSync(SRC_DIR)) {
  log.error(`Source directory ${SRC_DIR} does not exist`);
  process.exit(1);
}

// Copy static files from frontend root
STATIC_FILES.forEach((item) => {
  const srcPath = path.join(__dirname, item);
  const destPath = path.join(DIST_DIR, item);

  if (fs.existsSync(srcPath)) {
    if (fs.lstatSync(srcPath).isDirectory()) {
      fs.cpSync(srcPath, destPath, { recursive: true });
      log.info(`Copied ${item}/ directory`);
    } else {
      fs.copyFileSync(srcPath, destPath);
      log.info(`Copied ${item}`);
    }
  } else {
    log.warn(`${item} not found, skipping`);
  }
});

// Run TypeScript compiler
log.build("Compiling TypeScript");
try {
  execSync("npx tsc", { stdio: "pipe" });
  log.success("TypeScript compiled");
} catch (error) {
  log.error("TypeScript compilation failed");
  console.error(error.stdout?.toString() || error.message);
  process.exit(1);
}

// Resolve path aliases to relative imports
log.build("Resolving path aliases");
try {
  execSync("npx tsc-alias", { stdio: "pipe" });
  log.success("Path aliases resolved");
} catch (error) {
  log.error("Path alias resolution failed");
  console.error(error.message);
  process.exit(1);
}

// Add .js extensions to all relative imports
log.build("Adding .js extensions to imports");
try {
  execSync("node add-js-extensions.js", { stdio: "pipe" });
  log.success(".js extensions added");
} catch (error) {
  log.error("Adding .js extensions failed");
  console.error(error.message);
  process.exit(1);
}

// Verify all expected files are present
const expectedDirs = [
  "components",
  "config",
  "utils",
  "state",
  "routing",
  "services",
  "types",
  "v2",
];
const missingDirs = expectedDirs.filter(
  (dir) => !fs.existsSync(path.join(DIST_DIR, dir)),
);

if (missingDirs.length > 0) {
  log.error(`Missing compiled directories: ${missingDirs.join(", ")}`);
  process.exit(1);
}

log.success("Production build complete");
log.info("Ready for Cloudflare Pages deployment from dist/");
