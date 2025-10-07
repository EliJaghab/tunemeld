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

applyCacheBusting();

document.addEventListener("DOMContentLoaded", initializeApp);

async function initializeApp(): Promise<void> {
  await loadTitleContent();

  stateManager.initializeFromDOM();
  const currentTheme = stateManager.getTheme();
  if (currentTheme) {
    stateManager.applyTheme(currentTheme);
  }

  const mainContent = document.getElementById("main-content");
  if (mainContent) {
    mainContent.style.visibility = "visible";
  }
  document.body.style.opacity = "1";

  try {
    // Initialize router first - this does the focused GraphQL query
    await appRouter.initialize();

    // Only after router is initialized, set up UI components that depend on global data
    await setupThemeToggle();
    await loadAndRenderGenreButtons();
    await loadAndRenderRankButtons();
    await setupClosePlayerButton();
    await initializeTosPrivacyOverlay();
  } catch (error: unknown) {
    console.error("App initialization failed:", error);
  }

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

  const currentTheme = stateManager.getTheme();
  const buttonLabels =
    currentTheme === "dark"
      ? stateManager.getButtonLabel("themeToggleDark")
      : stateManager.getButtonLabel("themeToggleLight");

  if (buttonLabels && buttonLabels.length > 0) {
    const themeLabel = buttonLabels[0];
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
}
