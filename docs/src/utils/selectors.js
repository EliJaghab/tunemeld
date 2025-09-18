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
  sortTable,
  updateMainPlaylist,
} from "@/components/playlist.js";
import { loadAndRenderRankButtons } from "@/components/ranks.js";
import { setupBodyClickListener } from "@/components/servicePlayer.js";
import { stateManager } from "@/state/StateManager.js";
import { appRouter } from "@/routing/router.js";
import { graphqlClient } from "@/services/graphql-client.js";
import { displayPlaylistMetadata } from "@/utils/playlist-metadata.js";

export async function updateGenreData(genre, updateAll = false) {
  try {
    showSkeletonLoaders();
    if (updateAll) {
      const { serviceOrder } = await graphqlClient.getPlaylistMetadata(genre);

      await Promise.all([
        displayPlaylistMetadata(genre),
        fetchAndDisplayPlaylistsWithOrder(genre, serviceOrder),
        updateMainPlaylist(genre),
      ]);
      // Only render rank buttons on full update (genre change)
      await loadAndRenderRankButtons();
    } else {
      await updateMainPlaylist(genre);
    }
    sortTable(stateManager.getCurrentColumn(), stateManager.getCurrentOrder());
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
    appRouter.navigateToGenre(currentGenre);
  });
}
