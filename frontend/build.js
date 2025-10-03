#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const DIST_DIR = path.join(__dirname, "dist");
const SRC_DIR = path.join(__dirname, "src");
const STATIC_FILES = ["index.html", "css", "images", "html"];

console.log("Building TuneMeld frontend...");

// Clean dist directory
if (fs.existsSync(DIST_DIR)) {
  fs.rmSync(DIST_DIR, { recursive: true });
}
fs.mkdirSync(DIST_DIR);

// Verify src directory exists
if (!fs.existsSync(SRC_DIR)) {
  console.error(`Error: Source directory ${SRC_DIR} does not exist`);
  process.exit(1);
}

// Copy static files from frontend root
STATIC_FILES.forEach((item) => {
  const srcPath = path.join(__dirname, item);
  const destPath = path.join(DIST_DIR, item);

  if (fs.existsSync(srcPath)) {
    if (fs.lstatSync(srcPath).isDirectory()) {
      fs.cpSync(srcPath, destPath, { recursive: true });
      console.log(`Copied ${item}/`);
    } else {
      fs.copyFileSync(srcPath, destPath);
      console.log(`Copied ${item}`);
    }
  } else {
    console.warn(`Warning: ${item} not found, skipping`);
  }
});

// Run TypeScript compiler
console.log("Compiling TypeScript...");
try {
  execSync("npx tsc", { stdio: "inherit" });
} catch (error) {
  console.error("TypeScript compilation failed");
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
];
const missingDirs = expectedDirs.filter(
  (dir) => !fs.existsSync(path.join(DIST_DIR, dir)),
);

if (missingDirs.length > 0) {
  console.error(
    `Error: Missing compiled directories: ${missingDirs.join(", ")}`,
  );
  process.exit(1);
}

// Copy build output to backend/static for serving
const BACKEND_STATIC_DIR = path.join(__dirname, "..", "backend", "static");
console.log("Copying build output to backend/static...");

if (fs.existsSync(BACKEND_STATIC_DIR)) {
  fs.rmSync(BACKEND_STATIC_DIR, { recursive: true });
}
fs.mkdirSync(BACKEND_STATIC_DIR, { recursive: true });

// Copy all files from dist to backend/static
fs.cpSync(DIST_DIR, BACKEND_STATIC_DIR, { recursive: true });
console.log("Frontend files copied to backend/static/");

console.log("Build complete! All files compiled successfully.");
