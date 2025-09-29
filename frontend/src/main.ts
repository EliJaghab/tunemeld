import { loadTitleContent } from "@/components/title";
import { loadAndRenderRankButtons } from "@/components/rankButton";
import { loadAndRenderGenreButtons } from "@/components/genreButtons";
import {
  setupBodyClickListener,
  setupClosePlayerButton,
} from "@/components/servicePlayer";
import { initializeTosPrivacyOverlay } from "./tosPrivacy.js";
import { stateManager } from "@/state/StateManager";
import { appRouter } from "@/routing/router";
import { applyCacheBusting } from "@/config/config";
import { showInitialShimmer } from "@/components/shimmer";
import type { ButtonLabel } from "@/types/index";

applyCacheBusting();

document.addEventListener("DOMContentLoaded", initializeApp);

async function initializeApp(): Promise<void> {
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
  } catch (error: unknown) {
    console.error("App initialization failed:", error);
  }

  await loadAndRenderGenreButtons();
  setupClosePlayerButton();
  initializeTosPrivacyOverlay();

  if (mainContent) {
    mainContent.style.visibility = "visible";
  }
  document.body.style.transition = "opacity 0.2s ease-in";
  document.body.style.opacity = "1";
}

async function setupThemeToggle(): Promise<void> {
  const themeToggleButton = stateManager.getElement(
    "theme-toggle-button",
  ) as HTMLInputElement | null;
  if (themeToggleButton) {
    themeToggleButton.addEventListener("change", async () => {
      stateManager.toggleTheme();
      await updateThemeToggleLabels();
    });

    await updateThemeToggleLabels();
  }
}

async function updateThemeToggleLabels(): Promise<void> {
  const themeToggleButton = stateManager.getElement(
    "theme-toggle-button",
  ) as HTMLInputElement | null;
  if (!themeToggleButton) return;

  try {
    const currentTheme = stateManager.getTheme();
    const { graphqlClient } = await import("@/services/graphql-client");
    const buttonLabels: ButtonLabel[] = await graphqlClient.getMiscButtonLabels(
      "theme_toggle",
      currentTheme,
    );

    if (buttonLabels && buttonLabels.length > 0) {
      const themeLabel: ButtonLabel = buttonLabels[0];
      if (themeLabel.title) {
        const label = document.querySelector(
          'label[for="theme-toggle-button"]',
        ) as HTMLLabelElement | null;
        if (label) {
          label.title = themeLabel.title;
        }
      }
      if (themeLabel.ariaLabel) {
        themeToggleButton.setAttribute("aria-label", themeLabel.ariaLabel);
      }
    }
  } catch (error: unknown) {
    console.warn("Failed to load theme toggle labels:", error);
  }
}
