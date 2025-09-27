import { loadTitleContent } from "@/components/title.js";
import { loadAndRenderRankButtons } from "@/components/rankButton.js";
import { loadAndRenderGenreButtons } from "@/components/genreButtons.js";
import {
  setupBodyClickListener,
  setupClosePlayerButton,
} from "@/components/servicePlayer.js";
import { initializeTosPrivacyOverlay } from "./tosPrivacy.js";
import { stateManager } from "@/state/StateManager.js";
import { appRouter } from "@/routing/router.js";
import { applyCacheBusting } from "@/config/config.js";
import { showInitialShimmer } from "@/components/shimmer.js";

applyCacheBusting();

document.addEventListener("DOMContentLoaded", initializeApp);

async function initializeApp() {
  // Load title content first
  await loadTitleContent();

  // Initialize state and theme
  stateManager.initializeFromDOM();
  stateManager.applyTheme(stateManager.getTheme());
  setupThemeToggle();

  document.getElementById("main-content").style.visibility = "visible";
  document.body.style.opacity = "1";
  showInitialShimmer();

  try {
    await appRouter.initialize();
  } catch (error) {
    console.error("App initialization failed:", error);
  }

  await loadAndRenderGenreButtons();
  setupClosePlayerButton();
  initializeTosPrivacyOverlay();

  // Reveal content after everything is loaded with smooth transition
  document.getElementById("main-content").style.visibility = "visible";
  document.body.style.transition = "opacity 0.2s ease-in";
  document.body.style.opacity = "1";
}

function setupThemeToggle() {
  const themeToggleButton = stateManager.getElement("theme-toggle-button");
  if (themeToggleButton) {
    themeToggleButton.addEventListener("change", () => {
      stateManager.toggleTheme();
    });
  }
}
