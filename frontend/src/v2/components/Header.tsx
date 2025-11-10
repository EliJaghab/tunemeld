import React, { useContext } from "react";
import { APP_BASE_URL } from "@/config/config";
import { ThemeContext } from "@/v2/ThemeContext";
import { THEME } from "@/v2/constants";
import GlassSurface from "@/v2/components/GlassSurface";

export function Header(): React.ReactElement {
  const [theme, setTheme] = useContext(ThemeContext);
  const isDark = theme === THEME.DARK;
  const buttonLabel = isDark ? "Switch to light mode" : "Switch to dark mode";

  const toggleTheme = () => setTheme(isDark ? THEME.LIGHT : THEME.DARK);

  return (
    <div className="flex justify-center px-3 py-4 desktop:px-4 desktop:py-6">
      <GlassSurface
        width="100%"
        borderRadius={50}
        backgroundOpacity={0.1}
        saturation={1}
        borderWidth={0.07}
        brightness={50}
        opacity={0.93}
        blur={11}
        displace={0.5}
        distortionScale={-180}
        redOffset={0}
        greenOffset={10}
        blueOffset={20}
        className="w-full max-w-container px-5 py-3 desktop:px-8 desktop:py-4"
      >
        <div className="flex w-full flex-wrap items-center justify-between gap-3 text-text desktop:gap-6">
          <div className="flex min-w-0 flex-1 items-center gap-2 desktop:gap-4">
            <a
              href={APP_BASE_URL}
              className="flex items-center gap-2 desktop:gap-4"
            >
              <img
                src="./images/tunemeld.png"
                alt="tunemeld Logo"
                className="h-9 w-9 rounded-full shadow-lg desktop:h-12 desktop:w-12"
              />
              <div className="flex flex-col">
                <span className="text-sm font-semibold tracking-wide desktop:text-lg">
                  tunemeld
                </span>
                <span className="text-[0.625rem] font-light text-muted desktop:text-xs">
                  React v2 prototype
                </span>
              </div>
            </a>
          </div>

          <div className="flex justify-end text-xs font-medium desktop:text-sm">
            <button
              className="flex items-center justify-center rounded-full border border-text/20 bg-text/10 p-2 transition hover:bg-text/20 desktop:p-3"
              onClick={toggleTheme}
              aria-label={buttonLabel}
              type="button"
            >
              <img
                src={isDark ? "./images/sun.svg" : "./images/moon.svg"}
                alt={isDark ? "Light mode" : "Dark mode"}
                className="h-4 w-4 desktop:h-5 desktop:w-5"
              />
            </button>
          </div>
        </div>
      </GlassSurface>
    </div>
  );
}
