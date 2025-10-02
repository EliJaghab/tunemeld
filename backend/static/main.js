import { loadTitleContent } from "@/components/title";
import { loadAndRenderRankButtons } from "@/components/rankButton";
import { loadAndRenderGenreButtons } from "@/components/genreButtons";
import { setupClosePlayerButton } from "@/components/servicePlayer";
import { initializeTosPrivacyOverlay } from "./tosPrivacy.js";
import { stateManager } from "@/state/StateManager";
import { appRouter } from "@/routing/router";
import { applyCacheBusting } from "@/config/config";
import { showInitialShimmer } from "@/components/shimmer";
applyCacheBusting();
document.addEventListener("DOMContentLoaded", initializeApp);
async function initializeApp() {
  await loadTitleContent();
  stateManager.initializeFromDOM();
  const currentTheme = stateManager.getTheme();
  if (currentTheme) {
    stateManager.applyTheme(currentTheme);
  }
  setupThemeToggle();
  const mainContent = document.getElementById("main-content");
  if (mainContent) {
    mainContent.style.visibility = "visible";
  }
  document.body.style.opacity = "1";
  showInitialShimmer();
  try {
    await appRouter.initialize();
  } catch (error) {
    console.error("App initialization failed:", error);
  }
  await loadAndRenderGenreButtons();
  await loadAndRenderRankButtons();
  setupClosePlayerButton();
  initializeTosPrivacyOverlay();
  if (mainContent) {
    mainContent.style.visibility = "visible";
  }
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
    await updateThemeToggleLabels();
  }
}
async function updateThemeToggleLabels() {
  const themeToggleButton = stateManager.getElement("theme-toggle-button");
  if (!themeToggleButton) return;
  try {
    const currentTheme = stateManager.getTheme();
    const { graphqlClient } = await import("@/services/graphql-client");
    const buttonLabels = await graphqlClient.getMiscButtonLabels(
      "theme_toggle",
      currentTheme,
    );
    if (buttonLabels && buttonLabels.length > 0) {
      const themeLabel = buttonLabels[0];
      if (themeLabel.title) {
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
  }
}
