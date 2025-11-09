import React, { useContext } from "react";
import { APP_BASE_URL } from "@/config/config";
import { ThemeContext } from "@/v2/ThemeContext";
import { THEME } from "@/v2/theme";

export function Header(): React.ReactElement {
  const [theme, setTheme] = useContext(ThemeContext);
  const isDark = theme === THEME.DARK;
  const buttonLabel = isDark ? "Switch to light mode" : "Switch to dark mode";

  const toggleTheme = () => {
    setTheme(isDark ? THEME.LIGHT : THEME.DARK);
  };

  return (
    <>
      <div className="vertical-spacing"></div>
      <div className="logo-title">
        <a href={APP_BASE_URL} className="logo-title-link">
          <img
            src="./images/tunemeld.png"
            id="tunemeld-logo"
            alt="tunemeld Logo"
          />
          <h1 className="main-title">tunemeld (React v2)</h1>
        </a>
        <div className="theme-toggle-container">
          <button
            className={`theme-toggle ${isDark ? "dark-mode" : ""}`}
            onClick={toggleTheme}
            aria-label={buttonLabel}
            title={buttonLabel}
          >
            <img src="images/sun.svg" alt="Sun Icon" className="sun" />
            <img src="images/moon.svg" alt="Moon Icon" className="moon" />
          </button>
        </div>
        <a
          href="https://soundcloud.com/elijaghab"
          target="_blank"
          id="soundcloud-link"
        >
          <img
            src="./images/soundcloud_logo.png"
            alt="SoundCloud"
            id="soundcloud-logo"
          />
          Eli&apos;s SoundCloud
        </a>
      </div>
      <div className="vertical-spacing"></div>
    </>
  );
}
