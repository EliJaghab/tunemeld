import { loadTitleContent } from "@/components/title.js";
import { loadAndRenderRankButtons } from "@/components/ranks.js";
import { loadAndRenderGenreButtons } from "@/components/genres.js";
import {
  setupBodyClickListener,
  setupClosePlayerButton,
} from "@/components/servicePlayer.js";
import { initializeTosPrivacyOverlay } from "./tosPrivacy.js";
import { stateManager } from "@/state/StateManager.js";
import { appRouter } from "@/routing/router.js";
import { applyCacheBusting } from "@/config/config.js";

applyCacheBusting();

document.addEventListener("DOMContentLoaded", initializeApp);

async function initializeApp() {
  await loadTitleContent();

  stateManager.initializeFromDOM();
  stateManager.applyTheme(stateManager.getTheme());
  setupThemeToggle();

  try {
    await appRouter.initialize();
  } catch (error) {
    console.error("App initialization failed:", error);
  }

  await loadAndRenderGenreButtons();
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
