import React, { useContext } from "react";
import clsx from "clsx";
import { APP_BASE_URL } from "@/config/config";
import { ThemeContext } from "@/v2/ThemeContext";
import { THEME } from "@/v2/constants";
import GlassSurface from "@/v2/components/shared/GlassSurface";
import { ResponsiveIcon } from "@/v2/components/shared/ResponsiveIcon";

export function Header(): React.ReactElement {
  const [theme, setTheme] = useContext(ThemeContext);
  const isDark = theme === THEME.DARK;
  const buttonLabel = isDark ? "Switch to light mode" : "Switch to dark mode";

  const toggleTheme = () => setTheme(isDark ? THEME.LIGHT : THEME.DARK);

  return (
    <header id="title-container">
      <div className={clsx("flex justify-center px-3 desktop:px-4")}>
        <GlassSurface
          width="100%"
          height="auto"
          borderRadius={50}
          backgroundOpacity={0.1}
          borderWidth={0}
          blur={11}
          className={clsx(
            "w-full max-w-container",
            "px-2 py-2 desktop:px-2 desktop:py-2"
          )}
        >
          <div
            className={clsx(
              "flex w-full items-center justify-between",
              "gap-3 desktop:gap-6"
            )}
          >
            <div className={clsx("flex items-center gap-2 desktop:gap-3")}>
              <a
                href={APP_BASE_URL}
                className={clsx("flex items-center gap-2 desktop:gap-3")}
              >
                <ResponsiveIcon
                  src="./images/tunemeld.png"
                  alt="tunemeld Logo"
                  size="xl"
                  className={clsx("rounded-full shadow-lg")}
                />
                <span
                  className={clsx(
                    "text-sm desktop:text-base font-semibold",
                    "tracking-wide",
                    "text-black dark:text-white"
                  )}
                >
                  tunemeld
                </span>
              </a>
            </div>

            <button
              className={clsx(
                "flex items-center justify-center",
                "h-6 w-6 desktop:h-8 desktop:w-8",
                "rounded-full",
                "bg-white/10 hover:bg-white/20",
                "transition"
              )}
              onClick={toggleTheme}
              aria-label={buttonLabel}
              type="button"
            >
              <ResponsiveIcon
                src={isDark ? "./images/sun.svg" : "./images/moon.svg"}
                alt={isDark ? "Light mode" : "Dark mode"}
                size="xs"
                className={clsx("brightness-0 dark:brightness-0 dark:invert")}
              />
            </button>
          </div>
        </GlassSurface>
      </div>
    </header>
  );
}
