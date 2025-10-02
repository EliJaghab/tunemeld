import {
  hideShimmerLoaders,
  showGenreSwitchShimmer,
} from "@/components/shimmer";
import {
  addToggleEventListeners,
  populatePlayCountMap,
  renderPlaylistTracks,
  resetCollapseStates,
  setPlaylistData,
  sortTable,
  updateMainPlaylist,
} from "@/components/playlist";
import { loadAndRenderRankButtons } from "@/components/rankButton";
import { setupBodyClickListener } from "@/components/servicePlayer";
import { stateManager } from "@/state/StateManager";
import { appRouter } from "@/routing/router";
import { graphqlClient } from "@/services/graphql-client";
import { SERVICE_NAMES } from "@/config/constants";
import { updatePlaylistHeaderSync } from "@/components/playlistHeader";
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
      const allData = await fetchAllGenreData(genre);
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
    } else {
      await updateMainPlaylist(genre);
    }
    await loadAndRenderRankButtons();
    const currentColumn = stateManager.getCurrentColumn();
    if (currentColumn) {
      sortTable(currentColumn, stateManager.getCurrentOrder());
    }
    hideShimmerLoaders();
    resetCollapseStates();
    await addToggleEventListeners();
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
