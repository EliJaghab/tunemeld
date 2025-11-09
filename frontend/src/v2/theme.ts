export const THEME = {
  LIGHT: "light",
  DARK: "dark",
} as const;

export type ThemeValue = (typeof THEME)[keyof typeof THEME];

export const isThemeValue = (value: unknown): value is ThemeValue =>
  value === THEME.LIGHT || value === THEME.DARK;

export const THEME_STORAGE_KEY = "tunemeld:v2:theme";
