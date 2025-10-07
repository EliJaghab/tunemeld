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

function createPlaylistShimmer(
  includeServiceHeader: boolean = true,
  shimmerType: ShimmerType = SHIMMER_TYPES.TUNEMELD,
): HTMLDivElement {
  const overlay = createElement(
    "div",
    "loading-overlay loading-overlay-playlist",
  ) as HTMLDivElement;

  // Include service header shimmer when needed (genre changes)
  if (includeServiceHeader) {
    // Create service header shimmer (shows service icons/metadata)
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

  // Always include track shimmer (table rows)
  const tableContainer = createElement("div", "shimmer-table-container");
  tableContainer.appendChild(createShimmerTable(shimmerType));
  overlay.appendChild(tableContainer);

  return overlay;
}

export function showShimmerLoaders(
  isInitialLoad: boolean = false,
  forceShimmerType?: ShimmerType,
  isGenreChange: boolean = false,
): void {
  // Use explicit shimmer type if provided, otherwise derive from current column
  let shimmerType: ShimmerType;
  if (forceShimmerType) {
    shimmerType = forceShimmerType;
    stateManager.setShimmerType(shimmerType);
  } else {
    stateManager.setShimmerTypeFromColumn(stateManager.getCurrentColumn());
    shimmerType = stateManager.getShimmerType() as ShimmerType;
  }

  const mainPlaylist = document.querySelector(".main-playlist");
  if (!mainPlaylist) return;

  const playlistHeader = mainPlaylist.querySelector(".playlist-header");
  const playlistContent = mainPlaylist.querySelector(".playlist-content");
  if (!playlistContent) return;

  // Remove any existing shimmer
  const existingShimmer = playlistContent.querySelector(
    ".loading-overlay-playlist",
  );
  if (existingShimmer) {
    existingShimmer.remove();
  }

  // Always hide the table for any shimmer
  const playlistTable = playlistContent.querySelector(".playlist-table");
  playlistTable?.classList.add("hidden");

  // Decide what to shimmer based on the type of change
  if (isInitialLoad) {
    // Hide everything on initial load
    playlistHeader?.classList.add("hidden");
    const controlGroups = playlistContent.querySelectorAll(".control-group");
    controlGroups.forEach((group) => group.classList.add("hidden"));

    // Show full shimmer (header + controls + table)
    const shimmer = createPlaylistShimmer(true, shimmerType);
    playlistContent.appendChild(shimmer);
  } else if (isGenreChange) {
    // Genre change: show service header shimmer and table shimmer
    const shimmer = createPlaylistShimmer(true, shimmerType);
    playlistContent.appendChild(shimmer);
  } else {
    // Rank switch: header stays visible, only table shimmers
    // Show table shimmer only
    const shimmer = createPlaylistShimmer(false, shimmerType);
    playlistContent.appendChild(shimmer);
  }
}

export function showServiceHeaderAndTrackShimmer(): void {
  // Shows shimmer for service header and tracks (used during genre changes and initial load)
  const isInitial = stateManager.isInitialLoad();
  const currentShimmerType = stateManager.getShimmerType();
  showShimmerLoaders(isInitial, currentShimmerType, !isInitial);

  if (isInitial) {
    stateManager.markInitialLoadComplete();
  }
}

export function showTrackShimmer(): void {
  // Shows shimmer for tracks only (used during rank changes)
  const currentShimmerType = stateManager.getShimmerType();
  showShimmerLoaders(false, currentShimmerType, false);
}

export function hideShimmerLoaders(): void {
  stateManager.hideAllShimmers();

  const mainPlaylist = document.querySelector(".main-playlist");
  if (!mainPlaylist) return;

  const playlistHeader = mainPlaylist.querySelector(".playlist-header");
  const playlistContent = mainPlaylist.querySelector(".playlist-content");

  // Show everything
  playlistHeader?.classList.remove("hidden");

  if (playlistContent) {
    const controlGroups = playlistContent.querySelectorAll(".control-group");
    const playlistTable = playlistContent.querySelector(".playlist-table");

    controlGroups.forEach((group) => group.classList.remove("hidden"));
    playlistTable?.classList.remove("hidden");

    // Remove all shimmer overlays
    const shimmerOverlay = playlistContent.querySelector(
      ".loading-overlay-playlist",
    );
    shimmerOverlay?.remove();
  }
}
