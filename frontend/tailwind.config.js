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

const palette = {
  deepSpace: "#050211",
  midnight: "#1b1428",
  twilight: "#241b35",
  twilightMuted: "#312646",
  ghostWhite: "#f6f5ff",
  lilacGrey: "#b3adc9",
  deepPurpleBorder: "#2f2740",
  electricPurple: "#7C5CFF",
  softPurple: "#A18CFF",
  darkViolet: "#1B0E3F",
  teal: "#008080",
  skyBlue: "#4a9eff",
  oceanBlue: "#00BFFF",
  redError: "#dc3545",
  white: "#FFFFFF",
  black: "#000000",
  darkGray: "#111827",
};

const colors = {
  transparent: "transparent",
  current: "currentColor",
  inherit: "inherit",

  // Semantic mappings
  background: palette.deepSpace,
  surface: palette.midnight,
  "surface-alt": palette.twilight,
  "surface-muted": palette.twilightMuted,
  text: palette.ghostWhite,
  muted: palette.lilacGrey,
  border: palette.deepPurpleBorder,

  accent: palette.electricPurple,
  "accent-soft": palette.softPurple,
  "accent-contrast": palette.darkViolet,

  white: palette.white,
  black: palette.black,
  gray: {
    700: palette.darkGray,
  },

  // Brand colors
  "badge-red": palette.redError,
  "tunemeld-blue": palette.oceanBlue,
  "brand-teal": palette.teal,
  "bright-blue": palette.skyBlue,
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
