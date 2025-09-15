import {
  fetchAndDisplayHeaderArt,
  hideSkeletonLoaders,
  showSkeletonLoaders,
} from "@/components/header.js";
import {
  addToggleEventListeners,
  fetchAndDisplayPlaylists,
  fetchAndDisplayPlaylistsWithOrder,
  resetCollapseStates,
  setupSortButtons,
  sortTable,
  updateMainPlaylist,
} from "@/components/playlist.js";
import { setupBodyClickListener } from "@/components/servicePlayer.js";
import { stateManager } from "@/state/StateManager.js";
import { appRouter } from "@/routing/router.js";
import { genreManager } from "@/utils/genre-manager.js";
import { graphqlClient } from "@/services/graphql-client.js";
import { displayPlaylistMetadata } from "@/utils/playlist-metadata.js";

export async function updateGenreData(genre, viewCountType, updateAll = false) {
  try {
    showSkeletonLoaders();
    if (updateAll) {
      const { serviceOrder } = await graphqlClient.getPlaylistMetadata(genre);

      await Promise.all([
        displayPlaylistMetadata(genre),
        fetchAndDisplayPlaylistsWithOrder(genre, serviceOrder),
        updateMainPlaylist(genre, viewCountType),
      ]);
    } else {
      await updateMainPlaylist(genre, viewCountType);
    }
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
  genreSelector.addEventListener("change", async function () {
    const currentGenre = genreSelector.value;

    const genreObj = genreManager.availableGenres.find(
      (g) => g.name === currentGenre,
    );
    const genreDisplay = genreObj ? genreObj.displayName : currentGenre;
    document.title = `tunemeld - ${genreDisplay}`;

    const url = `/?genre=${encodeURIComponent(currentGenre)}`;
    window.history.pushState({}, "", url);

    await updateGenreData(currentGenre, stateManager.getViewCountType(), true);
  });
}

export function setupViewCountTypeSelector(viewCountTypeSelector) {
  viewCountTypeSelector.addEventListener("change", function () {
    const viewCountType = viewCountTypeSelector.value;
    stateManager.setViewCountType(viewCountType);
    sortTable(
      stateManager.getCurrentColumn(),
      stateManager.getCurrentOrder(),
      viewCountType,
    );
  });
}
