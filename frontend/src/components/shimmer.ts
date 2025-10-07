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

function createPlaylistHeaderShimmer(): HTMLDivElement {
  // Create service header shimmer (shows service icons/metadata)
  const headerShimmer = createElement(
    "div",
    "playlist-header-shimmer",
  ) as HTMLDivElement;
  const titleRow = createElement("div", "playlist-title-shimmer");

  const logoShimmer = createElement("div", "shimmer shimmer-playlist-logo");
  const titleShimmer = createElement("div", "shimmer shimmer-playlist-title");
  const descShimmer = createElement("div", "shimmer shimmer-playlist-desc");

  titleRow.appendChild(logoShimmer);
  titleRow.appendChild(titleShimmer);
  titleRow.appendChild(descShimmer);

  headerShimmer.appendChild(titleRow);
  return headerShimmer;
}

function createControlButtonsShimmer(): HTMLDivElement {
  const controlsContainer = createElement(
    "div",
    "controls-shimmer-container",
  ) as HTMLDivElement;

  // Genre controls shimmer
  const genreSection = createElement("div", "control-group");
  const genreLabel = createElement("label", "control-label shimmer");
  const genreButtons = createElement("div", "genre-controls");

  for (let i = 0; i < 4; i++) {
    genreButtons.appendChild(createElement("div", "sort-button shimmer"));
  }

  genreSection.appendChild(genreLabel);
  genreSection.appendChild(genreButtons);
  controlsContainer.appendChild(genreSection);

  // Ranking controls shimmer
  const rankSection = createElement("div", "control-group");
  const rankLabel = createElement("label", "control-label shimmer");
  const rankButtons = createElement("div", "sort-controls");

  for (let i = 0; i < 3; i++) {
    rankButtons.appendChild(createElement("div", "sort-button shimmer"));
  }

  rankSection.appendChild(rankLabel);
  rankSection.appendChild(rankButtons);
  controlsContainer.appendChild(rankSection);

  return controlsContainer;
}

function createTrackTableShimmer(shimmerType: ShimmerType): HTMLDivElement {
  const tableContainer = createElement(
    "div",
    "shimmer-table-container",
  ) as HTMLDivElement;
  tableContainer.appendChild(createShimmerTable(shimmerType));
  return tableContainer;
}

function createPlaylistShimmer(
  shimmerPlaylistHeader: boolean,
  shimmerButtons: boolean,
  shimmerTracks: boolean,
  shimmerType: ShimmerType = SHIMMER_TYPES.TUNEMELD,
): HTMLDivElement {
  const overlay = createElement(
    "div",
    "loading-overlay loading-overlay-playlist",
  ) as HTMLDivElement;

  if (shimmerPlaylistHeader) {
    overlay.appendChild(createPlaylistHeaderShimmer());
  }

  if (shimmerButtons) {
    overlay.appendChild(createControlButtonsShimmer());
  }

  if (shimmerTracks) {
    overlay.appendChild(createTrackTableShimmer(shimmerType));
  }

  return overlay;
}

export function showShimmerLoaders(
  shimmerPlaylistHeader: boolean,
  shimmerButtons: boolean,
  shimmerTracks: boolean,
  forceShimmerType?: ShimmerType,
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

  // Hide elements based on what we're shimmering
  if (shimmerPlaylistHeader) {
    playlistHeader?.classList.add("hidden");
  }

  if (shimmerButtons) {
    const controlGroups = playlistContent.querySelectorAll(".control-group");
    controlGroups.forEach((group) => group.classList.add("hidden"));
  }

  if (shimmerTracks) {
    const playlistTable = playlistContent.querySelector(".playlist-table");
    playlistTable?.classList.add("hidden");
  }

  // Create and add the shimmer overlay
  const shimmer = createPlaylistShimmer(
    shimmerPlaylistHeader,
    shimmerButtons,
    shimmerTracks,
    shimmerType,
  );
  playlistContent.appendChild(shimmer);
}

export function showServiceHeaderAndTrackShimmer(): void {
  // Shows shimmer for service header and tracks (used during genre changes and initial load)
  const isInitial = stateManager.isInitialLoad();
  const currentShimmerType = stateManager.getShimmerType();

  if (isInitial) {
    // Initial load: shimmer everything (playlist header, buttons, tracks)
    showShimmerLoaders(true, true, true, currentShimmerType);
    stateManager.markInitialLoadComplete();
  } else {
    // Genre change: shimmer playlist header and tracks, but NOT buttons
    showShimmerLoaders(true, false, true, currentShimmerType);
  }
}

export function showTrackShimmer(): void {
  // Shows shimmer for tracks only (used during rank changes)
  const currentShimmerType = stateManager.getShimmerType();
  // Rank change: only shimmer tracks
  showShimmerLoaders(false, false, true, currentShimmerType);
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
