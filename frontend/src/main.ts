import { loadTitleContent } from "@/components/title";
import { loadAndRenderRankButtons } from "@/components/rankButton";
import { loadAndRenderGenreButtons } from "@/components/genreButtons";
import { debugLog } from "@/config/config";
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

const mainDebug = (message: string, meta?: unknown) => {
  debugLog("Main", message, meta);
};

async function initializeApp(): Promise<void> {
  mainDebug("initializeApp: start");
  const mainContent = document.getElementById("main-content");
  await loadTitleContent();

  mainDebug("initializeApp: title content loaded");
  stateManager.initializeFromDOM();
  const currentTheme = stateManager.getTheme();
  if (currentTheme) {
    stateManager.applyTheme(currentTheme);
  }

  try {
    mainDebug("initializeApp: initializing router");
    // Initialize router first - handles initial shimmer, visibility, and GraphQL queries
    await appRouter.initialize();
    mainDebug("initializeApp: router initialized");

    // Only after router is initialized, set up UI components that depend on global data
    mainDebug("initializeApp: setting up theme toggle");
    await setupThemeToggle();
    mainDebug("initializeApp: loading genre buttons");
    await loadAndRenderGenreButtons();
    mainDebug("initializeApp: loading rank buttons");
    await loadAndRenderRankButtons();
    mainDebug("initializeApp: setting up close player button");
    await setupClosePlayerButton();
    mainDebug("initializeApp: initializing TOS overlay");
    await initializeTosPrivacyOverlay();
    mainDebug("initializeApp: end");
  } catch (error: unknown) {
    console.error("App initialization failed:", error);
  }
}

async function setupThemeToggle(): Promise<void> {
  const themeToggleButton = stateManager.getElement(
    "theme-toggle-button",
  ) as HTMLButtonElement | null;
  if (themeToggleButton) {
    themeToggleButton.addEventListener("click", async () => {
      stateManager.toggleTheme();
      await updateThemeToggleLabels();
    });

    await updateThemeToggleLabels();
  }
}

async function updateThemeToggleLabels(): Promise<void> {
  const themeToggleButton = stateManager.getElement(
    "theme-toggle-button",
  ) as HTMLButtonElement | null;
  if (!themeToggleButton) return;

  const currentTheme = stateManager.getTheme();
  const buttonLabels =
    currentTheme === "dark"
      ? stateManager.getButtonLabel("themeToggleDark")
      : stateManager.getButtonLabel("themeToggleLight");

  if (currentTheme === "dark") {
    themeToggleButton.classList.add("dark-mode");
  } else {
    themeToggleButton.classList.remove("dark-mode");
  }

  if (buttonLabels && buttonLabels.length > 0) {
    const themeLabel = buttonLabels[0];
    if (themeLabel.title) {
      themeToggleButton.title = themeLabel.title;
    }
    if (themeLabel.ariaLabel) {
      themeToggleButton.setAttribute("aria-label", themeLabel.ariaLabel);
    }
  }
}
