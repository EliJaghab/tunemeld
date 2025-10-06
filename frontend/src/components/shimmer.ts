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
import {
  createShimmerRowFromStructure,
  getTableStructure,
} from "@/config/tableStructures";

/**
 * SHIMMER COLUMN CONFIGURATIONS
 *
 * Now using shared table structure configurations from tableStructures.js
 * This ensures actual table and shimmer stay in perfect lockstep.
 */

const SHIMMER_ROW_COUNT = 20;

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

function createShimmerTable(shimmerType: ShimmerType): HTMLTableElement {
  const table = createElement(
    "table",
    "playlist-table playlist-table-shimmer",
  ) as HTMLTableElement;
  const tbody = createElement("tbody") as HTMLTableSectionElement;

  for (let i = 0; i < SHIMMER_ROW_COUNT; i++) {
    const row = createShimmerTableRow(shimmerType);
    if (row) {
      tbody.appendChild(row);
    }
  }

  table.appendChild(tbody);
  return table;
}

function createServiceShimmer(): HTMLDivElement {
  const overlay = createElement(
    "div",
    "loading-overlay loading-overlay-service",
  ) as HTMLDivElement;
  const imageShimmer = createElement("div", "shimmer shimmer-service-image");
  const textShimmer = createElement("div", "shimmer shimmer-service-text");

  overlay.appendChild(imageShimmer);
  overlay.appendChild(textShimmer);

  return overlay;
}

function createPlaylistShimmer(
  includeControls: boolean = true,
  shimmerType: ShimmerType = SHIMMER_TYPES.TUNEMELD,
): HTMLDivElement {
  const overlay = createElement(
    "div",
    "loading-overlay loading-overlay-playlist",
  ) as HTMLDivElement;

  // Only include header and controls shimmer on initial load
  if (includeControls) {
    // Create playlist header shimmer
    const headerShimmer = createElement("div", "playlist-header-shimmer");
    const titleRow = createElement("div", "playlist-title-shimmer");

    const logoShimmer = createElement("div", "shimmer shimmer-playlist-logo");
    const titleShimmer = createElement("div", "shimmer shimmer-playlist-title");
    const descShimmer = createElement("div", "shimmer shimmer-playlist-desc");

    titleRow.appendChild(logoShimmer);
    titleRow.appendChild(titleShimmer);
    titleRow.appendChild(descShimmer);

    headerShimmer.appendChild(titleRow);
    overlay.appendChild(headerShimmer);

    // Genre controls - using same structure as actual HTML
    const genreSection = createElement("div", "control-group");
    const genreLabel = createElement("label", "control-label shimmer");
    const genreButtons = createElement("div", "genre-controls");

    for (let i = 0; i < 4; i++) {
      genreButtons.appendChild(createElement("div", "sort-button shimmer"));
    }

    genreSection.appendChild(genreLabel);
    genreSection.appendChild(genreButtons);
    overlay.appendChild(genreSection);

    // Ranking controls - using same structure as actual HTML
    const rankSection = createElement("div", "control-group");
    const rankLabel = createElement("label", "control-label shimmer");
    const rankButtons = createElement("div", "sort-controls");

    for (let i = 0; i < 3; i++) {
      rankButtons.appendChild(createElement("div", "sort-button shimmer"));
    }

    rankSection.appendChild(rankLabel);
    rankSection.appendChild(rankButtons);
    overlay.appendChild(rankSection);
  }

  // Always include table shimmer
  const tableContainer = createElement("div", "shimmer-table-container");
  tableContainer.appendChild(createShimmerTable(shimmerType));
  overlay.appendChild(tableContainer);

  return overlay;
}

export function showShimmerLoaders(isInitialLoad: boolean = false): void {
  // Update StateManager shimmer state
  stateManager.showShimmer("services");
  stateManager.showShimmer("playlist", isInitialLoad);

  // Use StateManager to explicitly track shimmer type
  stateManager.setShimmerTypeFromColumn(stateManager.getCurrentColumn());
  const shimmerType = stateManager.getShimmerType() as ShimmerType;
  const structure = getTableStructure(shimmerType);

  // Inject and show service shimmer overlays
  document.querySelectorAll(".service").forEach((service) => {
    let overlay = service.querySelector(".loading-overlay");
    if (!overlay) {
      overlay = createServiceShimmer();
      service.appendChild(overlay);
    }
    overlay.classList.add("active");
  });

  const mainPlaylist = document.querySelector(".main-playlist");
  if (!mainPlaylist) return;

  const playlistHeader = mainPlaylist.querySelector(".playlist-header");
  const playlistContent = mainPlaylist.querySelector(".playlist-content");
  if (!playlistContent) return;

  // Remove any existing shimmer first
  const existingShimmer = playlistContent.querySelector(
    ".loading-overlay-playlist",
  );
  if (existingShimmer) {
    existingShimmer.remove();
  }

  if (isInitialLoad) {
    // Initial load: hide real header, controls and table, show shimmer
    playlistHeader?.classList.add("hidden");

    const controlGroups = playlistContent.querySelectorAll(".control-group");
    const playlistTable = playlistContent.querySelector(".playlist-table");

    controlGroups.forEach((group) => group.classList.add("hidden"));
    playlistTable?.classList.add("hidden");

    // Create and insert shimmer header, controls and table
    const shimmer = createPlaylistShimmer(true, shimmerType);
    playlistContent.appendChild(shimmer);
  } else {
    // Genre switching: only hide/show table
    const playlistTable = playlistContent.querySelector(".playlist-table");
    if (playlistTable) {
      playlistTable.classList.add("hidden");

      // Create and insert table shimmer
      const shimmer = createPlaylistShimmer(false, shimmerType);
      playlistContent.appendChild(shimmer);
    }
  }
}

export function showInitialShimmer(): void {
  showShimmerLoaders(true);
}

export function showGenreSwitchShimmer(): void {
  showShimmerLoaders(false);
}

export function hideShimmerLoaders(): void {
  // Update StateManager shimmer state
  stateManager.hideAllShimmers();

  // Hide service overlays
  const serviceOverlays = document.querySelectorAll(
    ".service .loading-overlay",
  );
  serviceOverlays.forEach((overlay) => {
    overlay.classList.remove("active");
  });

  // Show real playlist content and remove shimmer
  const mainPlaylist = document.querySelector(".main-playlist");
  if (mainPlaylist) {
    const playlistHeader = mainPlaylist.querySelector(".playlist-header");
    const playlistContent = mainPlaylist.querySelector(".playlist-content");

    // Show real header
    playlistHeader?.classList.remove("hidden");

    if (playlistContent) {
      // Show real controls and table
      const controlGroups = playlistContent.querySelectorAll(".control-group");
      const playlistTable = playlistContent.querySelector(".playlist-table");

      controlGroups.forEach((group) => group.classList.remove("hidden"));
      playlistTable?.classList.remove("hidden");

      // Remove shimmer overlay
      const shimmerOverlay = playlistContent.querySelector(
        ".loading-overlay-playlist",
      );
      if (shimmerOverlay) {
        shimmerOverlay.remove();
      }
    }
  }
}
