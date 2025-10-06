#!/usr/bin/env node

/**
 * Post-processes compiled JavaScript files to add .js extensions to relative imports.
 * This is required for ES modules to work in browsers without a bundler.
 */

const fs = require("fs");
const path = require("path");

function addJsExtensions(dir) {
  const files = fs.readdirSync(dir, { withFileTypes: true });

  for (const file of files) {
    const fullPath = path.join(dir, file.name);

    if (file.isDirectory()) {
      addJsExtensions(fullPath);
    } else if (file.name.endsWith(".js")) {
      let content = fs.readFileSync(fullPath, "utf8");

      // Replace relative imports that don't already have .js extension
      // Matches: from "./path" or from "../path"  (not already ending in .js)
      content = content.replace(
        /from\s+['"](\.\.?\/[^'"]+?)(?<!\.js)['"]/g,
        (match, importPath) => {
          return `from '${importPath}.js'`;
        },
      );

      // Also handle dynamic imports
      content = content.replace(
        /import\s*\(\s*['"](\.\.?\/[^'"]+?)(?<!\.js)['"]\s*\)/g,
        (match, importPath) => {
          return `import('${importPath}.js')`;
        },
      );

      fs.writeFileSync(fullPath, content, "utf8");
    }
  }
}

const distDir = path.join(__dirname, "dist");
console.log("Adding .js extensions to relative imports...");
addJsExtensions(distDir);
console.log("Done!");
