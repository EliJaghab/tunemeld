import { updatePlaylistHeader } from "@/components/playlistHeader.js";
import {
  hideShimmerLoaders,
  showGenreSwitchShimmer,
} from "@/components/shimmer.js";
import {
  addToggleEventListeners,
  fetchAndDisplayPlaylists,
  fetchAndDisplayPlaylistsWithOrder,
  populatePlayCountMap,
  renderPlaylistTracks,
  resetCollapseStates,
  setPlaylistData,
  sortTable,
  updateMainPlaylist,
} from "@/components/playlist.js";
import { loadAndRenderRankButtons } from "@/components/rankButton.js";
import { setupBodyClickListener } from "@/components/servicePlayer.js";
import { stateManager } from "@/state/StateManager.js";
import { appRouter } from "@/routing/router.js";
import { graphqlClient } from "@/services/graphql-client.js";
import { SERVICE_NAMES } from "@/config/constants.js";
import { updatePlaylistHeaderSync } from "@/components/playlistHeader.js";

async function fetchAllGenreData(genre) {
  const metadataResult = await graphqlClient.getPlaylistMetadata(genre);
  const { serviceOrder, playlists } = metadataResult;

  const [mainPlaylistResult, ranksResult, ...servicePlaylistResults] =
    await Promise.all([
      graphqlClient.getPlaylistTracks(genre, SERVICE_NAMES.TUNEMELD),
      graphqlClient.fetchPlaylistRanks(),
      ...serviceOrder.map((service) =>
        graphqlClient.getPlaylistTracks(genre, service).catch((error) => {
          console.error(`Error fetching ${service} playlist:`, error);
          return null;
        }),
      ),
    ]);

  return {
    metadata: { serviceOrder, playlists },
    mainPlaylist: mainPlaylistResult,
    ranks: ranksResult,
    servicePlaylists: servicePlaylistResults,
    serviceOrder,
  };
}

export async function updateGenreData(genre, updateAll = false) {
  try {
    showGenreSwitchShimmer();
    if (updateAll) {
      // Fetch all data first, then update DOM synchronously
      const allData = await fetchAllGenreData(genre);

      // Update playlist header synchronously
      updatePlaylistHeaderSync(
        allData.metadata.playlists,
        allData.metadata.serviceOrder,
        genre,
        null,
      );

      const mainPlaylistData = [allData.mainPlaylist.playlist];
      setPlaylistData(mainPlaylistData);

      const isrcs = mainPlaylistData.flatMap((playlist) =>
        playlist.tracks.map((track) => track.isrc),
      );
      await populatePlayCountMap(isrcs);

      renderPlaylistTracks(
        mainPlaylistData,
        "main-playlist-data-placeholder",
        SERVICE_NAMES.TUNEMELD,
      );

      // Render service playlists
      allData.serviceOrder.forEach((service, index) => {
        const servicePlaylistResult = allData.servicePlaylists[index];
        if (servicePlaylistResult) {
          const servicePlaylistData = [servicePlaylistResult.playlist];
          renderPlaylistTracks(
            servicePlaylistData,
            `${service}-data-placeholder`,
            service,
          );
        }
      });

      // Load rank buttons (this is synchronous DOM manipulation)
      await loadAndRenderRankButtons();
    } else {
      await updateMainPlaylist(genre);
    }
    sortTable(stateManager.getCurrentColumn(), stateManager.getCurrentOrder());
    hideShimmerLoaders();
    resetCollapseStates();
    addToggleEventListeners();
    setupBodyClickListener(genre);
  } catch (error) {
    console.error("Error updating genre data:", error);
    hideShimmerLoaders();
  }
}

export function setupGenreSelector(genreSelector) {
  genreSelector.addEventListener("change", async function () {
    const currentGenre = genreSelector.value;
    appRouter.navigateToGenre(currentGenre);
  });
}
