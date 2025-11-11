#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const { execSync, spawn } = require("child_process");

const DIST_DIR = path.join(__dirname, "dist");
const SRC_DIR = path.join(__dirname, "src");
const STATIC_FILES = ["index.html", "index-v2.html", "css", "images", "html"];
const copyV2CssFiles = () => {
  const srcDir = path.join(SRC_DIR, "v2");
  const destDir = path.join(DIST_DIR, "v2");

  const copyRecursive = (source, destination) => {
    if (!fs.existsSync(source)) return;
    const entries = fs.readdirSync(source, { withFileTypes: true });

    entries.forEach((entry) => {
      const srcPath = path.join(source, entry.name);
      const destPath = path.join(destination, entry.name);

      if (entry.isDirectory()) {
        copyRecursive(srcPath, destPath);
      } else if (entry.isFile() && entry.name.endsWith(".css")) {
        fs.mkdirSync(path.dirname(destPath), { recursive: true });
        fs.copyFileSync(srcPath, destPath);
        log.info(
          `Copied CSS ${path.relative(SRC_DIR, srcPath)} -> ${path.relative(
            DIST_DIR,
            destPath,
          )}`,
        );
      }
    });
  };

  copyRecursive(srcDir, destDir);
};

const log = {
  info: (msg) => console.log(`[INFO] ${msg}`),
  success: (msg) => console.log(`[SUCCESS] ${msg}`),
  error: (msg) => console.error(`[ERROR] ${msg}`),
  warn: (msg) => console.warn(`[WARN] ${msg}`),
  build: (msg) => console.log(`[BUILD] ${msg}`),
};

log.build("Starting TuneMeld frontend build");

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

// Build Tailwind CSS initially
log.build("Building Tailwind CSS for v2");
try {
  execSync(
    "npx tailwindcss -i ./src/v2/styles/tailwind.css -o ./dist/v2/tailwind.css",
    { stdio: "pipe" },
  );
  log.success("Tailwind CSS built");
} catch (error) {
  log.error("Tailwind CSS build failed");
  console.error(error.message);
  process.exit(1);
}

// Run TypeScript compiler once
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
  copyV2CssFiles();
  log.success("Component CSS copied");
} catch (error) {
  log.error("Adding .js extensions failed");
  console.error(error.message);
  process.exit(1);
}

log.success("Initial build complete");
console.log("");
log.info("Starting file watchers");

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
          log.info(`Updated ${src}/${filename}`);
        }
      } catch (error) {
        log.error(`Failed to copy ${filename}: ${error.message}`);
      }
    }
  });

  log.info(`Watching ${src}/ directory`);
});

// Watch v2 CSS files
const v2Dir = path.join(SRC_DIR, "v2");
if (fs.existsSync(v2Dir)) {
  fs.watch(v2Dir, { recursive: true }, (eventType, filename) => {
    if (filename && filename.endsWith(".css")) {
      copyV2CssFiles();
    }
  });
  log.info("Watching src/v2 CSS files");
}
// Watch index.html in root
["index.html", "index-v2.html"].forEach((file) => {
  const filePath = path.join(__dirname, file);
  if (fs.existsSync(filePath)) {
    fs.watchFile(filePath, () => {
      const destPath = path.join(DIST_DIR, file);
      try {
        fs.copyFileSync(filePath, destPath);
        log.info(`Updated ${file}`);
      } catch (error) {
        log.error(`Failed to copy ${file}: ${error.message}`);
      }
    });
    log.info(`Watching ${file}`);
  }
});

// Start TypeScript watcher with post-processing
log.info("Starting TypeScript watcher");
console.log("");

const tscWatch = spawn("npx", ["tsc", "--watch"], {
  shell: true,
});

const tailwindWatch = spawn(
  "npx",
  [
    "tailwindcss",
    "-i",
    "./src/v2/styles/tailwind.css",
    "-o",
    "./dist/v2/tailwind.css",
    "--watch",
  ],
  {
    shell: true,
  },
);

let isProcessing = false;

tscWatch.stdout.on("data", (data) => {
  const output = data.toString();

  // Filter out noisy TypeScript output, only show important messages
  if (output.includes("error TS")) {
    log.error(output.trim());
  } else if (output.includes("Found 0 errors")) {
    log.success("TypeScript compilation complete");
  } else if (output.includes("File change detected")) {
    log.build("Recompiling TypeScript");
  }

  // Detect compilation completion
  if (
    (output.includes("Watching for file changes") ||
      output.includes("Found 0 errors")) &&
    !isProcessing
  ) {
    isProcessing = true;

    // Run post-processing steps
    try {
      execSync("npx tsc-alias", { stdio: "pipe" });
      log.success("Path aliases resolved");

      execSync("node add-js-extensions.js", { stdio: "pipe" });
      log.success(".js extensions added");
      copyV2CssFiles();
      log.success("Component CSS copied");

      console.log("");
    } catch (error) {
      log.error(`Post-processing failed: ${error.message}`);
    } finally {
      isProcessing = false;
    }
  }
});

tscWatch.stderr.on("data", (data) => {
  const output = data.toString();

  if (output.includes("error TS")) {
    log.error(output.trim());
  } else if (output.includes("Found 0 errors")) {
    log.success("TypeScript compilation complete");
  } else if (output.includes("File change detected")) {
    log.build("Recompiling TypeScript");
  }

  if (
    (output.includes("Watching for file changes") ||
      output.includes("Found 0 errors")) &&
    !isProcessing
  ) {
    isProcessing = true;

    try {
      execSync("npx tsc-alias", { stdio: "pipe" });
      log.success("Path aliases resolved");

      execSync("node add-js-extensions.js", { stdio: "pipe" });
      log.success(".js extensions added");
      copyV2CssFiles();
      log.success("Component CSS copied");

      console.log("");
    } catch (error) {
      log.error(`Post-processing failed: ${error.message}`);
    } finally {
      isProcessing = false;
    }
  }
});

// Handle process termination
process.on("SIGINT", () => {
  log.info("Stopping watchers");
  tscWatch.kill();
  tailwindWatch.kill();
  process.exit(0);
});

process.on("SIGTERM", () => {
  log.info("Stopping watchers");
  tscWatch.kill();
  tailwindWatch.kill();
  process.exit(0);
});
