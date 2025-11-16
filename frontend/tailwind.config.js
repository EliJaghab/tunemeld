const defaultTheme = require("tailwindcss/defaultTheme");

const spacingScale = {
  0: "0px",
  1: "4px",
  2: "8px",
  3: "12px",
  4: "16px",
  5: "20px",
  6: "24px",
  8: "32px",
  9: "36px",
  12: "48px",
};

const colors = {
  transparent: "transparent",
  current: "currentColor",
  inherit: "inherit",
  background: "var(--color-background)",
  surface: "var(--color-surface)",
  "surface-alt": "var(--color-surface-alt)",
  "surface-muted": "var(--color-surface-muted)",
  accent: "#7C5CFF",
  "accent-soft": "#A18CFF",
  "accent-contrast": "#1B0E3F",
  text: "var(--color-text)",
  muted: "var(--color-muted)",
  border: "var(--color-border)",
  white: "#FFFFFF",
  black: "#000000",
  gray: {
    700: "#111827",
  },
};

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/v2/**/*.{ts,tsx,js,jsx}",
    "./src/main-v2.tsx",
    "./index-v2.html",
  ],
  theme: {
    container: {
      center: true,
      padding: {
        DEFAULT: "16px",
        desktop: "32px",
      },
    },
    colors,
    spacing: spacingScale,
    fontFamily: {
      sans: ["'DM Sans'", ...defaultTheme.fontFamily.sans],
    },
    fontSize: {
      "2xs": ["10px", "14px"],
      xs: ["12px", "18px"],
      sm: ["14px", "20px"],
      base: ["16px", "24px"],
      lg: ["20px", "28px"],
      xl: ["24px", "32px"],
      "2xl": ["28px", "36px"],
      "3xl": ["32px", "40px"],
      "4xl": ["40px", "48px"],
    },
    extend: {
      screens: {
        desktop: "768px",
      },
      borderRadius: {
        pill: "999px",
        glass: "50px",
        media: "16px",
      },
      boxShadow: {
        glass: "0 25px 60px rgba(0,0,0,0.45)",
      },
      maxWidth: {
        container: "1200px",
      },
    },
  },
  darkMode: "class",
  plugins: [],
};
