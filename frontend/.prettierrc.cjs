module.exports = {
  semi: true,
  singleQuote: false,
  tabWidth: 2,
  trailingComma: "es5",
  printWidth: 80,
  plugins: [
    "prettier-plugin-tailwindcss",
    "prettier-plugin-classnames",
  ],
  customAttributes: ["className", "class"],
  customFunctions: ["clsx"],
};
