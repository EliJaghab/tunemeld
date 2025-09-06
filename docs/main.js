import { loadTitleContent } from "./title.js?v=20250828b";
import { setupSortButtons } from "./playlist.js?v=20250906b";
import { setupGenreSelector, setupViewCountTypeSelector } from "./selectors.js?v=20250906a";
import { setupBodyClickListener, setupClosePlayerButton } from "./servicePlayer.js?v=20250828b";
import { initializeTosPrivacyOverlay } from "./tosPrivacy.js?v=20250828b";
import { stateManager } from "./StateManager.js?v=20250828b";
import { loadGenresIntoSelector } from "./genre-loader.js?v=20250828b";
import { appRouter } from "./router.js?v=20250828b";

document.addEventListener("DOMContentLoaded", initializeApp);

async function initializeApp() {
  await loadTitleContent();
  applyStoredTheme();
  setupThemeToggle();

  const genreSelector = document.getElementById("genre-selector");
  const viewCountTypeSelector = document.getElementById("view-count-type-selector");

  stateManager.initializeFromDOM();

  try {
    await loadGenresIntoSelector();
  } catch (error) {
    console.error("Genre loader failed:", error);
  }

  await appRouter.initialize();

  setupGenreSelector(genreSelector);
  setupViewCountTypeSelector(viewCountTypeSelector);
  setupSortButtons();
  setupClosePlayerButton();
  initializeTosPrivacyOverlay();
}

function applyStoredTheme() {
  const storedTheme = localStorage.getItem("theme");
  if (storedTheme) {
    document.body.classList.toggle("dark-mode", storedTheme === "dark");
    document.getElementById("theme-toggle-button").checked = storedTheme === "dark";
  } else {
    applyThemeBasedOnTime();
  }
}

function applyThemeBasedOnTime() {
  const hour = new Date().getHours();
  const isDarkMode = hour >= 19 || hour < 7;

  if (isDarkMode) {
    document.body.classList.add("dark-mode");
    document.getElementById("theme-toggle-button").checked = true;
  } else {
    document.body.classList.remove("dark-mode");
    document.getElementById("theme-toggle-button").checked = false;
  }
}

function toggleTheme() {
  const isDarkMode = document.body.classList.toggle("dark-mode");
  localStorage.setItem("theme", isDarkMode ? "dark" : "light");
}

function setupThemeToggle() {
  const themeToggleButton = document.getElementById("theme-toggle-button");
  if (themeToggleButton) {
    themeToggleButton.addEventListener("change", toggleTheme);
  }
}
