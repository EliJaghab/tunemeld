#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const { execSync, spawn } = require("child_process");

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
      console.log(`Copied ${item}/ to ${item}/`);
    } else {
      fs.copyFileSync(srcPath, destPath);
      console.log(`Copied ${item}`);
    }
  } else {
    console.warn(`Warning: ${item} not found, skipping`);
  }
});

// Run TypeScript compiler once
console.log("Compiling TypeScript...");
try {
  execSync("npx tsc", { stdio: "inherit" });
} catch (error) {
  console.error("TypeScript compilation failed");
  process.exit(1);
}

// Resolve path aliases to relative imports
console.log("Resolving path aliases...");
try {
  execSync("npx tsc-alias", { stdio: "inherit" });
} catch (error) {
  console.error("Path alias resolution failed");
  process.exit(1);
}

// Add .js extensions to all relative imports
console.log("Adding .js extensions to imports...");
try {
  execSync("node add-js-extensions.js", { stdio: "inherit" });
} catch (error) {
  console.error("Adding .js extensions failed");
  process.exit(1);
}

console.log("Initial build complete!");
console.log("");
console.log("Starting file watchers...");

// Watch static files (CSS, HTML, images)
const WATCH_DIRS = [
  { src: "css", extensions: [".css"] },
  { src: "html", extensions: [".html"] },
  {
    src: "images",
    extensions: [".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico"],
  },
];

WATCH_DIRS.forEach(({ src, extensions }) => {
  const srcDir = path.join(__dirname, src);

  if (!fs.existsSync(srcDir)) {
    return;
  }

  fs.watch(srcDir, { recursive: true }, (eventType, filename) => {
    if (filename && extensions.some((ext) => filename.endsWith(ext))) {
      const srcPath = path.join(srcDir, filename);
      const destPath = path.join(DIST_DIR, src, filename);

      const destDir = path.dirname(destPath);
      if (!fs.existsSync(destDir)) {
        fs.mkdirSync(destDir, { recursive: true });
      }

      try {
        if (fs.existsSync(srcPath)) {
          fs.copyFileSync(srcPath, destPath);
          console.log(`Updated: ${src}/${filename}`);
        }
      } catch (error) {
        console.error(`Error copying ${filename}:`, error.message);
      }
    }
  });

  console.log(`Watching ${src}/ for changes...`);
});

// Watch index.html in root
const indexHtml = path.join(__dirname, "index.html");
if (fs.existsSync(indexHtml)) {
  fs.watchFile(indexHtml, () => {
    const destPath = path.join(DIST_DIR, "index.html");
    try {
      fs.copyFileSync(indexHtml, destPath);
      console.log("Updated: index.html");
    } catch (error) {
      console.error("Error copying index.html:", error.message);
    }
  });
  console.log("Watching index.html for changes...");
}

// Start TypeScript watcher
console.log("Starting TypeScript watcher...");
console.log("");

const tscWatch = spawn("npx", ["tsc", "--watch"], {
  stdio: "inherit",
  shell: true,
});

// Handle process termination
process.on("SIGINT", () => {
  console.log("\nStopping watchers...");
  tscWatch.kill();
  process.exit(0);
});

process.on("SIGTERM", () => {
  tscWatch.kill();
  process.exit(0);
});
