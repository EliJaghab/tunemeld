import { loadTitleContent } from "./title.js";
import { setupSortButtons } from "./playlist.js";
import { setupGenreSelector, setupViewCountTypeSelector, updateGenreData } from "./selectors.js";
import { setupBodyClickListener, setupClosePlayerButton } from "./servicePlayer.js";
import { initializeTosPrivacyOverlay } from "./tosPrivacy.js";
import { stateManager } from "./StateManager.js";

document.addEventListener("DOMContentLoaded", initializeApp);

function initializeApp() {
  loadTitleContent().then(() => {
    applyStoredTheme();
    setupThemeToggle();

    const genreSelector = document.getElementById("genre-selector");
    const viewCountTypeSelector = document.getElementById("view-count-type-selector");

    stateManager.initializeFromDOM();

    let currentGenre = genreSelector.value || "pop";
    let viewCountType = stateManager.getViewCountType();

    updateGenreData(currentGenre, viewCountType, true);

    setupGenreSelector(genreSelector);
    setupViewCountTypeSelector(viewCountTypeSelector);
    setupBodyClickListener(currentGenre);
    setupSortButtons();
    setupClosePlayerButton();
    initializeTosPrivacyOverlay();
  });
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
