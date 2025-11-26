#!/usr/bin/env node

const fs = require("fs");
const path = require("path");

const log = {
  info: (msg) => console.log(`[INFO] ${msg}`),
  success: (msg) => console.log(`[SUCCESS] ${msg}`),
  error: (msg) => console.error(`[ERROR] ${msg}`),
};

function addJsExtensions(dir) {
  const files = fs.readdirSync(dir, { withFileTypes: true });

  for (const file of files) {
    const fullPath = path.join(dir, file.name);

    if (file.isDirectory()) {
      addJsExtensions(fullPath);
    } else if (file.name.endsWith(".js")) {
      let content = fs.readFileSync(fullPath, "utf8");

      // Replace relative imports that don't already have .js extension
      content = content.replace(
        /from\s+['"](\.\.?\/[^'"]+?)(?<!\.js)['"]/g,
        (match, importPath) => {
          // Resolve the full path relative to the current file's directory
          const currentFileDir = path.dirname(fullPath);
          const resolvedPath = path.resolve(currentFileDir, importPath);

          // Check if it's a directory - if so, add /index.js, otherwise add .js
          if (
            fs.existsSync(resolvedPath) &&
            fs.statSync(resolvedPath).isDirectory()
          ) {
            return `from '${importPath}/index.js'`;
          }
          return `from '${importPath}.js'`;
        }
      );

      // Also handle dynamic imports
      content = content.replace(
        /import\s*\(\s*['"](\.\.?\/[^'"]+?)(?<!\.js)['"]\s*\)/g,
        (match, importPath) => {
          const currentFileDir = path.dirname(fullPath);
          const resolvedPath = path.resolve(currentFileDir, importPath);

          if (
            fs.existsSync(resolvedPath) &&
            fs.statSync(resolvedPath).isDirectory()
          ) {
            return `import('${importPath}/index.js')`;
          }
          return `import('${importPath}.js')`;
        }
      );

      fs.writeFileSync(fullPath, content, "utf8");
    }
  }
}

const distDir = path.join(__dirname, "dist");
addJsExtensions(distDir);
