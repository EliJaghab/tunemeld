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

async function setupThemeToggle() {
  const themeToggleButton = stateManager.getElement("theme-toggle-button");
  if (themeToggleButton) {
    themeToggleButton.addEventListener("change", async () => {
      stateManager.toggleTheme();
      await updateThemeToggleLabels();
    });

    // Initial button labels setup
    await updateThemeToggleLabels();
  }
}

async function updateThemeToggleLabels() {
  const themeToggleButton = stateManager.getElement("theme-toggle-button");
  if (!themeToggleButton) return;

  try {
    const currentTheme = stateManager.getTheme();
    const { graphqlClient } = await import("./src/services/graphql-client.js");
    const buttonLabels = await graphqlClient.getMiscButtonLabels(
      "theme_toggle",
      currentTheme,
    );

    if (buttonLabels && buttonLabels.length > 0) {
      const themeLabel = buttonLabels[0];
      if (themeLabel.title) {
        // For checkbox inputs, we add the title to the label element
        const label = document.querySelector(
          'label[for="theme-toggle-button"]',
        );
        if (label) {
          label.title = themeLabel.title;
        }
      }
      if (themeLabel.ariaLabel) {
        themeToggleButton.setAttribute("aria-label", themeLabel.ariaLabel);
      }
    }
  } catch (error) {
    console.warn("Failed to load theme toggle labels:", error);
    // Continue without labels if fetch fails
  }
}
