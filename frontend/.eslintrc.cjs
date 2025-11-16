const path = require("path");

module.exports = {
  root: true,
  env: {
    browser: true,
    es2020: true,
  },
  parser: "@typescript-eslint/parser",
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
    tsconfigRootDir: __dirname,
    project: path.join(__dirname, "tsconfig.json"),
  },
  plugins: ["@typescript-eslint", "import", "react-hooks"],
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:import/recommended",
    "plugin:import/typescript",
    "plugin:react-hooks/recommended",
    "prettier",
  ],
  ignorePatterns: ["dist/**"],
  settings: {
    "import/resolver": {
      typescript: {
        project: path.join(__dirname, "tsconfig.json"),
      },
    },
  },
  overrides: [
    {
      files: ["src/v2/**/*.{ts,tsx}"],
      rules: {
        "no-restricted-imports": [
          "error",
          {
            patterns: [
              {
                group: ["../*", "./*"],
                message: "Relative imports are not allowed. Use absolute imports with @/ aliases instead.",
              },
            ],
          },
        ],
      },
    },
  ],
};
