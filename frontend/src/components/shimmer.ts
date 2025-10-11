/**
 * Shimmer/Loading System
 * Provides unified loading states for services and playlists
 */

import { stateManager } from "@/state/StateManager";
import {
  TUNEMELD_RANK_FIELD,
  SHIMMER_TYPES,
  type ShimmerType,
} from "@/config/constants";
import { DEBUG_LOG_ENABLED, debugLog } from "@/config/config";
import { createShimmerRowFromStructure } from "@/config/tableStructures";

/**
 * SHIMMER COLUMN CONFIGURATIONS
 *
 * Now using shared table structure configurations from tableStructures.js
 * This ensures actual table and shimmer stay in perfect lockstep.
 */

const SHIMMER_ROW_COUNT = 20;
const shimmerDebug = (message: string, meta?: unknown) => {
  debugLog("Shimmer", message, meta);
};
const SHIMMER_LOG_PREFIX = "[Shimmer]";

export const trackLoadLog = (
  phase: string,
  meta?: Record<string, unknown>,
): void => {
  if (!DEBUG_LOG_ENABLED) {
    return;
  }
  const timestamp = new Date().toISOString();
  if (meta === undefined) {
    console.debug(`[TrackLoad ${timestamp}] ${phase}`);
  } else {
    console.debug(`[TrackLoad ${timestamp}] ${phase}`, meta);
  }
};

let tunemeldTrackShimmerActive = false;
let trackShimmerObserver: MutationObserver | null = null;

export const markTunemeldTrackShimmerHidden = (
  meta?: Record<string, unknown>,
): void => {
  if (tunemeldTrackShimmerActive) {
    tunemeldTrackShimmerActive = false;
    trackLoadLog("Tunemeld track shimmer hidden", meta);
  }
};

function attachTrackShimmerObserver(placeholder: HTMLElement): void {
  if (trackShimmerObserver) {
    return;
  }

  trackShimmerObserver = new MutationObserver(() => {
    if (!tunemeldTrackShimmerActive) {
      return;
    }

    const remainingShimmer = placeholder.querySelector(".shimmer");
    if (!remainingShimmer || placeholder.childElementCount === 0) {
      markTunemeldTrackShimmerHidden({
        reason: "mutation-cleared",
        childCount: placeholder.childElementCount,
        hasShimmer: !!remainingShimmer,
      });
    }
  });

  trackShimmerObserver.observe(placeholder, {
    childList: true,
    subtree: true,
  });
}

interface ShimmerOptions {
  includeServices?: boolean;
  includePlaylist?: boolean;
  includeHeaderAndControls?: boolean;
  isInitialLoad?: boolean;
}

let playlistRevealPromise: Promise<void> | null = null;
const inlineShimmerRegistry = new Map<
  HTMLElement,
  { placeholder: HTMLElement; originalDisplay: string }
>();

function determinePlaceholderDisplay(element: HTMLElement): string {
  const computedDisplay = window.getComputedStyle(element).display;
  if (computedDisplay === "inline" || computedDisplay === "inline-block") {
    return "inline-block";
  }
  return "block";
}

function createInlinePlaceholder(
  element: HTMLElement,
  className: string,
  fallbackWidth?: string,
  fallbackHeight?: string,
): HTMLElement | null {
  const parent = element.parentElement;
  if (!parent) {
    console.warn(
      SHIMMER_LOG_PREFIX,
      "createInlinePlaceholder: element without parent",
      element,
    );
    return null;
  }

  const placeholder = createElement(
    "span",
    `shimmer inline-shimmer ${className}`,
  );
  const display = determinePlaceholderDisplay(element);
  placeholder.style.display = display;

  const rect = element.getBoundingClientRect();
  const width = rect.width || (fallbackWidth ? parseFloat(fallbackWidth) : 0);
  const height =
    rect.height || (fallbackHeight ? parseFloat(fallbackHeight) : 0);

  if (width) {
    placeholder.style.width = `${width}px`;
  } else if (fallbackWidth) {
    placeholder.style.width = fallbackWidth;
  }

  if (height) {
    placeholder.style.height = `${height}px`;
  } else if (fallbackHeight) {
    placeholder.style.height = fallbackHeight;
  }

  parent.insertBefore(placeholder, element);
  return placeholder;
}

function applyInlineShimmer(
  element: HTMLElement,
  className: string,
  fallbackWidth?: string,
  fallbackHeight?: string,
): void {
  if (inlineShimmerRegistry.has(element)) {
    return;
  }

  const placeholder = createInlinePlaceholder(
    element,
    className,
    fallbackWidth,
    fallbackHeight,
  );
  if (!placeholder) {
    return;
  }

  inlineShimmerRegistry.set(element, {
    placeholder,
    originalDisplay: element.style.display,
  });

  element.style.display = "none";
  shimmerDebug("applyInlineShimmer", { element, className });
}

function clearInlineShimmer(element: HTMLElement | null): void {
  if (!element) return;

  const record = inlineShimmerRegistry.get(element);
  if (!record) {
    return;
  }

  record.placeholder.remove();
  element.style.display = record.originalDisplay || "";
  inlineShimmerRegistry.delete(element);
  shimmerDebug("clearInlineShimmer", { element });
}

export function registerPlaylistReveal(promise: Promise<void> | null): void {
  if (!promise) {
    shimmerDebug("registerPlaylistReveal: cleared");
    playlistRevealPromise = null;
    return;
  }

  shimmerDebug("registerPlaylistReveal: registered promise");
  playlistRevealPromise = promise.finally(() => {
    shimmerDebug("playlistRevealPromise: resolved");
  });
}

function consumePlaylistReveal(): Promise<void> | null {
  const promise = playlistRevealPromise;
  playlistRevealPromise = null;
  if (promise) {
    shimmerDebug("consumePlaylistReveal: promise consumed");
  } else {
    shimmerDebug("consumePlaylistReveal: no pending promise");
  }
  return promise;
}

// Helper functions
function createElement(tag: string, className?: string): HTMLElement {
  const element = document.createElement(tag);
  if (className) element.className = className;
  return element;
}

/**
 * Creates a shimmer row based on shimmer type using shared structure configuration
 */
function createShimmerTableRow(
  shimmerType: ShimmerType,
): HTMLTableRowElement | null {
  return createShimmerRowFromStructure(shimmerType);
}

function resetShimmerAnimations(container: ParentNode): void {
  container.querySelectorAll<HTMLElement>(".shimmer").forEach((element) => {
    element.classList.remove("morphing-out");
    // Force reflow so future animations restart cleanly
    void element.offsetWidth;
  });

  if (container instanceof HTMLElement) {
    container.classList.remove("fade-out");
  }
}

function createServiceShimmer(): HTMLDivElement {
  const overlay = document.createElement("div");
  overlay.className = "loading-overlay loading-overlay-service";
  overlay.innerHTML = `
    <div class="shimmer shimmer-service-image"></div>
    <div class="shimmer shimmer-service-text"></div>
  `;
  return overlay;
}

function showShimmerLoaders(options: ShimmerOptions = {}): void {
  const {
    includeServices = true,
    includePlaylist = true,
    includeHeaderAndControls = false,
    isInitialLoad = false,
  } = options;

  shimmerDebug("showShimmerLoaders", {
    includeServices,
    includePlaylist,
    includeHeaderAndControls,
    isInitialLoad,
  });

  if (includeServices) {
    stateManager.showShimmer("services", isInitialLoad);
  } else {
    stateManager.hideShimmer("services");
  }

  if (includePlaylist) {
    stateManager.showShimmer("playlist", isInitialLoad);
    stateManager.setShimmerTypeFromColumn(stateManager.getCurrentColumn());
  } else {
    stateManager.hideShimmer("playlist");
  }

  if (includeServices) {
    document.querySelectorAll(".service").forEach((service) => {
      let overlay = service.querySelector(".loading-overlay");
      if (!overlay) {
        overlay = createServiceShimmer();
        service.appendChild(overlay);
      }
      resetShimmerAnimations(overlay);
      overlay.classList.remove("fade-out");
      overlay.classList.add("active");
      shimmerDebug("service shimmer active", {
        serviceId: (service as HTMLElement).id || "unknown-service",
      });
    });
  }

  if (includePlaylist) {
    const shimmerType = stateManager.getShimmerType() as ShimmerType;
    injectShimmerIntoPlaceholders(shimmerType, includeHeaderAndControls);
  }
}

export function showInitialShimmer(): void {
  shimmerDebug("showInitialShimmer: start");
  // Reset loading states to ensure proper shimmer coordination
  stateManager.resetLoadingState();
  showShimmerLoaders({
    includeServices: true,
    includePlaylist: true,
    includeHeaderAndControls: true,
    isInitialLoad: true,
  });
  shimmerDebug("showInitialShimmer: end");
}

export function showGenreSwitchShimmer(): void {
  // Reset loading states to prevent premature shimmer hiding from previous load flags
  stateManager.resetLoadingState();
  showShimmerLoaders({
    includeServices: true,
    includePlaylist: true,
    includeHeaderAndControls: false,
    isInitialLoad: false,
  });
  shimmerDebug("showGenreSwitchShimmer invoked");
}

export { showGenreSwitchShimmer as showServiceHeaderAndTrackShimmer };

export function showRankSwitchShimmer(): void {
  // Reset loading states to prevent premature shimmer hiding from previous load flags
  stateManager.resetLoadingState();
  showShimmerLoaders({
    includeServices: false,
    includePlaylist: true,
    includeHeaderAndControls: false,
    isInitialLoad: false,
  });
  shimmerDebug("showRankSwitchShimmer invoked");
}

/**
 * Wrapper that shows shimmer, executes callback, then hides shimmer
 */
export async function withGenreShimmer<T>(
  callback: () => Promise<T> | T,
): Promise<T> {
  showGenreSwitchShimmer();
  try {
    const result = await callback();
    return result;
  } finally {
    hideShimmerLoaders();
  }
}

/**
 * Wrapper that shows shimmer, executes callback, then hides shimmer
 */
export async function withRankShimmer<T>(
  callback: () => Promise<T> | T,
): Promise<T> {
  showRankSwitchShimmer();
  try {
    const result = await callback();
    return result;
  } finally {
    hideShimmerLoaders();
  }
}

function injectShimmerIntoPlaceholders(
  shimmerType: ShimmerType,
  includeHeaderAndControls: boolean,
): void {
  if (!stateManager.getShimmerState("playlist")) {
    shimmerDebug(
      "injectShimmerIntoPlaceholders skipped (playlist shimmer inactive)",
    );
    return;
  }

  shimmerDebug("injectShimmerIntoPlaceholders", {
    shimmerType,
    includeHeaderAndControls,
  });

  // Main playlist tracks
  const mainPlaylistPlaceholder = document.getElementById(
    "main-playlist-data-placeholder",
  );
  if (mainPlaylistPlaceholder) {
    attachTrackShimmerObserver(mainPlaylistPlaceholder);
    mainPlaylistPlaceholder.innerHTML = "";
    mainPlaylistPlaceholder.setAttribute("data-rendered", "false");

    // Keep old tracks visible - don't clear or hide data container
    // New tracks will replace old ones when ready
    const currentColumn = stateManager.getCurrentColumn();
    const hideServiceIconShimmer =
      shimmerType === SHIMMER_TYPES.TOTAL_PLAYS &&
      currentColumn !== TUNEMELD_RANK_FIELD;

    for (let i = 0; i < SHIMMER_ROW_COUNT; i++) {
      const row = createShimmerTableRow(shimmerType);
      if (row) {
        if (hideServiceIconShimmer) {
          const seenOnCell = row.querySelector("td.seen-on");
          if (seenOnCell) {
            row.removeChild(seenOnCell);
          }
        }
        mainPlaylistPlaceholder.appendChild(row);
      }
    }
    shimmerDebug("main playlist shimmer rows injected", {
      count: mainPlaylistPlaceholder.childElementCount,
    });

    if (!tunemeldTrackShimmerActive) {
      tunemeldTrackShimmerActive = true;
      trackLoadLog("Tunemeld track shimmer shown", {
        rowCount: mainPlaylistPlaceholder.childElementCount,
        isInitialLoad: stateManager.isInitialLoad(),
        shimmerType,
      });
    }
  }

  // Service playlist tracks (for initial load)
  if (includeHeaderAndControls) {
    const servicePlaceholders = [
      "soundcloud-data-placeholder",
      "apple_music-data-placeholder",
      "spotify-data-placeholder",
    ];

    servicePlaceholders.forEach((id) => {
      const placeholder = document.getElementById(id);
      if (placeholder) {
        placeholder.innerHTML = "";
        for (let i = 0; i < 10; i++) {
          const row = createShimmerTableRow(SHIMMER_TYPES.TUNEMELD);
          if (row) {
            placeholder.appendChild(row);
          }
        }
        shimmerDebug(`service shimmer rows injected for ${id}`, {
          count: placeholder.childElementCount,
        });
      }
    });
  }

  // Handle header and controls shimmer for initial load
  if (includeHeaderAndControls) {
    // Shimmer for TuneMeld logo
    const tuneMeldLogo = document.querySelector(
      ".main-playlist .source-icon",
    ) as HTMLImageElement;
    if (tuneMeldLogo) {
      applyInlineShimmer(tuneMeldLogo, "shimmer-inline-logo", "24px", "24px");
    }

    const genreLabel = document.querySelector(
      ".control-group:has(#genre-controls) .control-label",
    );
    if (genreLabel && genreLabel.textContent === "Genre") {
      genreLabel.innerHTML =
        '<span class="shimmer" style="width: 60px; height: 20px; display: inline-block;"></span>';
    }

    const genreControlsContainer = document.getElementById("genre-controls");
    if (
      genreControlsContainer &&
      genreControlsContainer.children.length === 0
    ) {
      genreControlsContainer.innerHTML = Array(4)
        .fill(0)
        .map(
          () =>
            '<div class="sort-button shimmer shimmer-control shimmer-control-genre" aria-hidden="true" tabindex="-1"><span class="shimmer-control-bar"></span></div>',
        )
        .join("");
    }

    const rankLabel = document.querySelector(
      ".control-group:has(#sort-controls) .control-label",
    );
    if (rankLabel && rankLabel.textContent === "Ranking") {
      rankLabel.innerHTML =
        '<span class="shimmer" style="width: 80px; height: 20px; display: inline-block;"></span>';
    }

    const sortControlsContainer = document.getElementById("sort-controls");
    if (sortControlsContainer && sortControlsContainer.children.length === 0) {
      sortControlsContainer.innerHTML = Array(3)
        .fill(0)
        .map(
          () =>
            '<div class="sort-button shimmer shimmer-control shimmer-control-rank" aria-hidden="true" tabindex="-1"><span class="shimmer-control-bar"></span></div>',
        )
        .join("");
    }

    // Create shimmer for playlist title/description
    const playlistTitle = document.getElementById("tunemeld-playlist-title");
    const playlistDesc = document.getElementById("playlist-description");

    if (playlistTitle) {
      applyInlineShimmer(
        playlistTitle as HTMLElement,
        "shimmer-inline-title",
        "140px",
        "24px",
      );
    }

    if (playlistDesc) {
      applyInlineShimmer(
        playlistDesc as HTMLElement,
        "shimmer-inline-description",
        "220px",
        "20px",
      );
    }
  }
}

export function hideShimmerLoaders(): void {
  shimmerDebug("hideShimmerLoaders: start");
  const initialLoad = stateManager.isInitialLoad();
  const mainPlaceholder = document.getElementById(
    "main-playlist-data-placeholder",
  );
  const shouldRenderCached =
    initialLoad &&
    !!mainPlaceholder &&
    mainPlaceholder.getAttribute("data-rendered") !== "true";

  shimmerDebug("hideShimmerLoaders: context", {
    initialLoad,
    shouldRenderCached,
  });

  if (shouldRenderCached) {
    shimmerDebug(
      "hideShimmerLoaders: initial load, rendering cached playlists",
    );
    window.dispatchEvent(new CustomEvent("renderCachedPlaylists"));
  }

  const runFadeOut = (): void => {
    shimmerDebug("hideShimmerLoaders: runFadeOut");
    const shimmers = document.querySelectorAll(".shimmer");
    shimmers.forEach((shimmer) => {
      shimmer.classList.add("morphing-out");
    });

    const activeOverlays = document.querySelectorAll<HTMLElement>(
      ".loading-overlay-playlist.active, .loading-overlay-table.active, .loading-overlay-service.active",
    );
    activeOverlays.forEach((overlay) => {
      overlay.classList.add("fade-out");
    });

    setTimeout(() => {
      shimmerDebug("hideShimmerLoaders: timeout cleanup");
      stateManager.hideAllShimmers();

      activeOverlays.forEach((overlay) => {
        overlay.classList.remove("active", "fade-out");
        resetShimmerAnimations(overlay);
      });

      markTunemeldTrackShimmerHidden({ reason: "hide-shimmer-loaders" });

      // Show the real TuneMeld logo
      const tuneMeldLogo = document.querySelector(
        ".main-playlist .source-icon",
      ) as HTMLImageElement | null;
      clearInlineShimmer(tuneMeldLogo);

      const playlistTitle = document.getElementById(
        "tunemeld-playlist-title",
      ) as HTMLElement | null;
      clearInlineShimmer(playlistTitle);

      const playlistDesc = document.getElementById(
        "playlist-description",
      ) as HTMLElement | null;
      clearInlineShimmer(playlistDesc);

      const genreLabel = document.querySelector(
        ".control-group:has(#genre-controls) .control-label",
      );
      if (genreLabel && genreLabel.querySelector(".shimmer")) {
        genreLabel.innerHTML = "Genre";
      }

      const rankLabel = document.querySelector(
        ".control-group:has(#sort-controls) .control-label",
      );
      if (rankLabel && rankLabel.querySelector(".shimmer")) {
        rankLabel.innerHTML = "Ranking";
      }

      const genreControls = document.getElementById("genre-controls");
      if (genreControls) {
        genreControls.querySelectorAll(".shimmer").forEach((el) => el.remove());
        const realButtons = document.getElementById("genre-controls-real");
        if (realButtons) {
          realButtons.style.display = "";
          while (realButtons.firstChild) {
            genreControls.appendChild(realButtons.firstChild);
          }
          realButtons.remove();
        }
      }

      const sortControls = document.getElementById("sort-controls");
      if (sortControls) {
        sortControls.querySelectorAll(".shimmer").forEach((el) => el.remove());
        const realButtons = document.getElementById("sort-controls-real");
        if (realButtons) {
          realButtons.style.display = "";
          while (realButtons.firstChild) {
            sortControls.appendChild(realButtons.firstChild);
          }
          realButtons.remove();
        }
      }

      shimmerDebug("hideShimmerLoaders: end");
    }, 500);
  };

  const revealPromise = consumePlaylistReveal();
  if (revealPromise) {
    revealPromise
      .catch((error) => {
        console.warn(
          SHIMMER_LOG_PREFIX,
          "hideShimmerLoaders: playlist reveal promise rejected",
          error,
        );
      })
      .finally(() => {
        shimmerDebug(
          "hideShimmerLoaders: reveal promises settled, running fade-out",
        );
        runFadeOut();
      });
  } else {
    shimmerDebug(
      "hideShimmerLoaders: no reveal promise, running fade-out immediately",
    );
    runFadeOut();
  }
}
