import React, { createContext, useEffect, useState } from "react";
import {
  THEME,
  type ThemeValue,
  isThemeValue,
  THEME_STORAGE_KEY,
} from "@/v2/constants";

export const ThemeContext = createContext<
  [ThemeValue, (theme: ThemeValue) => void]
>([THEME.LIGHT, () => undefined]);

const getInitialTheme = (): ThemeValue => {
  if (typeof window === "undefined") {
    return THEME.LIGHT;
  }
  const stored = localStorage.getItem(THEME_STORAGE_KEY);
  if (isThemeValue(stored)) {
    return stored;
  }
  const prefersDark =
    window.matchMedia?.("(prefers-color-scheme: dark)")?.matches ?? false;
  return prefersDark ? THEME.DARK : THEME.LIGHT;
};

export function ThemeContextProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [theme, setTheme] = useState<ThemeValue>(() => getInitialTheme());

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === THEME.DARK);
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  return (
    <ThemeContext.Provider value={[theme, setTheme]}>
      {children}
    </ThemeContext.Provider>
  );
}
