import React, { useContext } from "react";
import { APP_BASE_URL } from "@/config/config";
import { ThemeContext } from "@/v2/ThemeContext";
import { THEME } from "@/v2/constants";
import GlassSurface from "@/v2/components/GlassSurface";
import { ResponsiveIcon } from "@/v2/components/ResponsiveIcon";

export function Header(): React.ReactElement {
  const [theme, setTheme] = useContext(ThemeContext);
  const isDark = theme === THEME.DARK;
  const buttonLabel = isDark ? "Switch to light mode" : "Switch to dark mode";

  const toggleTheme = () => setTheme(isDark ? THEME.LIGHT : THEME.DARK);

  return (
    <div className="flex justify-center px-3 desktop:px-4">
      <GlassSurface
        width="100%"
        height="auto"
        borderRadius={50}
        backgroundOpacity={0.1}
        saturation={1}
        borderWidth={0}
        brightness={50}
        opacity={0.93}
        blur={11}
        displace={0.5}
        distortionScale={-180}
        redOffset={0}
        greenOffset={10}
        blueOffset={20}
        className="w-full max-w-container px-2 py-2 desktop:px-2 desktop:py-2"
      >
        <div className="flex w-full items-center justify-between gap-3 text-white desktop:gap-6">
          <div className="flex items-center gap-2 desktop:gap-3">
            <a
              href={APP_BASE_URL}
              className="flex items-center gap-2 desktop:gap-3"
            >
              <ResponsiveIcon
                src="./images/tunemeld.png"
                alt="tunemeld Logo"
                size="xl"
                className="rounded-full shadow-lg"
              />
              <span className="text-sm font-semibold tracking-wide desktop:text-base">
                tunemeld
              </span>
            </a>
          </div>

          <button
            className="flex items-center justify-center rounded-full bg-white/10 p-1.5 transition hover:bg-white/20 desktop:p-2"
            onClick={toggleTheme}
            aria-label={buttonLabel}
            type="button"
          >
            <ResponsiveIcon
              src={isDark ? "./images/sun.svg" : "./images/moon.svg"}
              alt={isDark ? "Light mode" : "Dark mode"}
              size="xs"
            />
          </button>
        </div>
      </GlassSurface>
    </div>
  );
}
