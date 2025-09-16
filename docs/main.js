import { loadTitleContent } from "@/components/title.js";
import { setupSortButtons } from "@/components/playlist.js";
import {
  setupGenreSelector,
  setupViewCountTypeSelector,
} from "@/utils/selectors.js";
import {
  setupBodyClickListener,
  setupClosePlayerButton,
} from "@/components/servicePlayer.js";
import { initializeTosPrivacyOverlay } from "./tosPrivacy.js";
import { stateManager } from "@/state/StateManager.js";
import { loadGenresIntoSelector } from "@/utils/genre-loader.js";
import { appRouter } from "@/routing/router.js";
import { applyCacheBusting } from "@/config/config.js";

applyCacheBusting();

document.addEventListener("DOMContentLoaded", initializeApp);

async function initializeApp() {
  await loadTitleContent();

  stateManager.initializeFromDOM();
  stateManager.applyTheme(stateManager.getTheme());
  setupThemeToggle();

  const genreSelector = stateManager.getElement("genre-selector");
  const viewCountTypeSelector = stateManager.getElement(
    "view-count-type-selector",
  );

  try {
    await loadGenresIntoSelector();
    await appRouter.initialize();
  } catch (error) {
    console.error("App initialization failed:", error);
  }

  setupGenreSelector(genreSelector);
  setupViewCountTypeSelector(viewCountTypeSelector);
  setupSortButtons();
  setupClosePlayerButton();
  initializeTosPrivacyOverlay();
}

function setupThemeToggle() {
  const themeToggleButton = stateManager.getElement("theme-toggle-button");
  if (themeToggleButton) {
    themeToggleButton.addEventListener("change", () => {
      stateManager.toggleTheme();
    });
  }
}
