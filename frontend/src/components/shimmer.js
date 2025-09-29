/**
 * Shimmer/Loading System
 * Provides unified loading states for services and playlists
 */

import { stateManager } from "@/state/StateManager.js";
import { TUNEMELD_RANK_FIELD, SHIMMER_TYPES } from "@/config/constants.js";
import {
  createShimmerRowFromStructure,
  getTableStructure,
} from "@/config/tableStructures.js";

/**
 * SHIMMER COLUMN CONFIGURATIONS
 *
 * Now using shared table structure configurations from tableStructures.js
 * This ensures actual table and shimmer stay in perfect lockstep.
 */

const SHIMMER_ROW_COUNT = 20;

// Helper functions
function createElement(tag, className) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  return element;
}

/**
 * Creates a shimmer row based on shimmer type using shared structure configuration
 */
function createShimmerTableRow(shimmerType) {
  return createShimmerRowFromStructure(shimmerType);
}

function createShimmerTable(shimmerType) {
  const table = createElement("table", "playlist-table playlist-table-shimmer");
  const tbody = createElement("tbody");

  for (let i = 0; i < SHIMMER_ROW_COUNT; i++) {
    tbody.appendChild(createShimmerTableRow(shimmerType));
  }

  table.appendChild(tbody);
  return table;
}

function createServiceShimmer() {
  const overlay = createElement(
    "div",
    "loading-overlay loading-overlay-service",
  );
  const imageShimmer = createElement("div", "shimmer shimmer-service-image");
  const textShimmer = createElement("div", "shimmer shimmer-service-text");

  overlay.appendChild(imageShimmer);
  overlay.appendChild(textShimmer);

  return overlay;
}

function createPlaylistShimmer(
  includeControls = true,
  shimmerType = SHIMMER_TYPES.TUNEMELD,
) {
  const overlay = createElement(
    "div",
    "loading-overlay loading-overlay-playlist",
  );

  // Only include header shimmer on initial load
  if (includeControls) {
    // Create playlist header shimmer
    const header = createElement("div", "playlist-header-shimmer");
    const titleRow = createElement("div", "playlist-title-shimmer");

    const logoShimmer = createElement("div", "shimmer shimmer-playlist-logo");
    const titleShimmer = createElement("div", "shimmer shimmer-playlist-title");
    const descShimmer = createElement("div", "shimmer shimmer-playlist-desc");

    titleRow.appendChild(logoShimmer);
    titleRow.appendChild(titleShimmer);
    titleRow.appendChild(descShimmer);

    header.appendChild(titleRow);
    overlay.appendChild(header);
  }

  // Only include controls shimmer on initial load
  if (includeControls) {
    const controlsContainer = createElement("div", "playlist-controls-shimmer");

    // Genre controls
    const genreSection = createElement("div", "control-group-shimmer");
    const genreLabel = createElement("div", "shimmer shimmer-control-label");
    const genreButtons = createElement("div", "shimmer-buttons-row");

    for (let i = 0; i < 4; i++) {
      genreButtons.appendChild(createElement("div", "shimmer shimmer-button"));
    }

    genreSection.appendChild(genreLabel);
    genreSection.appendChild(genreButtons);

    // Ranking controls
    const rankSection = createElement("div", "control-group-shimmer");
    const rankLabel = createElement("div", "shimmer shimmer-control-label");
    const rankButton = createElement("div", "shimmer-buttons-row");

    for (let i = 0; i < 3; i++) {
      rankButton.appendChild(createElement("div", "shimmer shimmer-button"));
    }

    rankSection.appendChild(rankLabel);
    rankSection.appendChild(rankButton);

    controlsContainer.appendChild(genreSection);
    controlsContainer.appendChild(rankSection);
    overlay.appendChild(controlsContainer);
  }

  // Use the appropriate table shimmer based on ranking type
  const tableContainer = createElement("div", "shimmer-table-container");
  tableContainer.appendChild(createShimmerTable(shimmerType));
  overlay.appendChild(tableContainer);

  return overlay;
}

export function showShimmerLoaders(isInitialLoad = false) {
  // Use StateManager to explicitly track shimmer type
  stateManager.setShimmerTypeFromColumn(stateManager.getCurrentColumn());
  const shimmerType = stateManager.getShimmerType();
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

  if (isInitialLoad) {
    // Initial load: shimmer the whole main playlist with controls
    const mainPlaylist = document.querySelector(".playlist.main-playlist");
    if (mainPlaylist) {
      let overlay = mainPlaylist.querySelector(".loading-overlay");
      if (!overlay) {
        overlay = createPlaylistShimmer(true, shimmerType);
        mainPlaylist.appendChild(overlay);
      }
      overlay.classList.add("active");
    }
  } else {
    // Genre switching: only shimmer the table area, keep buttons visible
    const playlistTable = document.querySelector(
      ".main-playlist .playlist-table",
    );
    if (playlistTable) {
      let overlay = playlistTable.querySelector(".loading-overlay");
      if (!overlay) {
        // Create table-only shimmer (just the track rows) using the appropriate configuration
        overlay = createPlaylistShimmer(false, shimmerType);
        playlistTable.appendChild(overlay);
      }
      overlay.classList.add("active");
    }
  }
}

export function showInitialShimmer() {
  showShimmerLoaders(true);
}

export function showGenreSwitchShimmer() {
  showShimmerLoaders(false);
}

export function hideShimmerLoaders() {
  // Hide all loading overlays
  document.querySelectorAll(".loading-overlay").forEach((overlay) => {
    overlay.classList.remove("active");
  });
}
