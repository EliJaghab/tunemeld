import { fetchAndDisplayHeaderArt, hideSkeletonLoaders, showSkeletonLoaders } from "./header.js";
import {
  addToggleEventListeners,
  fetchAndDisplayLastUpdated,
  fetchAndDisplayPlaylists,
  resetCollapseStates,
  setupSortButtons,
  sortTable,
  updateMainPlaylist,
} from "./playlist.js";
import { setupBodyClickListener } from "./servicePlayer.js";
import { stateManager } from "./StateManager.js";

export async function updateGenreData(genre, viewCountType, updateAll = false) {
  try {
    showSkeletonLoaders();
    if (updateAll) {
      await fetchAndDisplayLastUpdated(genre);
      await fetchAndDisplayHeaderArt(genre);
      await fetchAndDisplayPlaylists(genre);
    }
    await updateMainPlaylist(genre, viewCountType);
    sortTable("rank", "asc", "total-view-count");
    hideSkeletonLoaders();
    resetCollapseStates();
    addToggleEventListeners();
    setupBodyClickListener(genre);
  } catch (error) {
    console.error("Error updating genre data:", error);
  }
}

export function setupGenreSelector(genreSelector) {
  genreSelector.addEventListener("change", function () {
    const currentGenre = genreSelector.value;
    updateGenreData(currentGenre, stateManager.getViewCountType(), true);
  });
}

export function setupViewCountTypeSelector(viewCountTypeSelector) {
  viewCountTypeSelector.addEventListener("change", function () {
    const viewCountType = viewCountTypeSelector.value;
    stateManager.setViewCountType(viewCountType);
    sortTable(stateManager.getCurrentColumn(), stateManager.getCurrentOrder(), viewCountType);
  });
}
