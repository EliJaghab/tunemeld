import { updatePlaylistHeader } from "@/components/playlistHeader";
import {
  hideShimmerLoaders,
  showGenreSwitchShimmer,
} from "@/components/shimmer";
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
} from "@/components/playlist";
import { loadAndRenderRankButtons } from "@/components/rankButton";
import { setupBodyClickListener } from "@/components/servicePlayer";
import { stateManager } from "@/state/StateManager";
import { appRouter } from "@/routing/router";
import { graphqlClient } from "@/services/graphql-client";
import { SERVICE_NAMES } from "@/config/constants";
import { updatePlaylistHeaderSync } from "@/components/playlistHeader";
import type { Playlist, Rank } from "@/types/index";

interface AllGenreData {
  metadata: { serviceOrder: string[]; playlists: Playlist[] };
  mainPlaylist: { playlist: Playlist };
  ranks: { ranks: Rank[] };
  servicePlaylists: ({ playlist: Playlist } | null)[];
  serviceOrder: string[];
}

async function fetchAllGenreData(genre: string): Promise<AllGenreData> {
  const metadataResult = await graphqlClient.getPlaylistMetadata(genre);
  const { serviceOrder, playlists } = metadataResult;

  const [mainPlaylistResult, ranksResult, ...servicePlaylistResults] =
    await Promise.all([
      graphqlClient.getPlaylistTracks(genre, SERVICE_NAMES.TUNEMELD),
      graphqlClient.fetchPlaylistRanks(),
      ...serviceOrder.map((service: string) =>
        graphqlClient
          .getPlaylistTracks(genre, service)
          .catch((error: Error) => {
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

export async function updateGenreData(
  genre: string,
  updateAll: boolean = false,
): Promise<void> {
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

      const isrcs = mainPlaylistData.flatMap((playlist: Playlist) =>
        playlist.tracks.map((track) => track.isrc),
      );
      await populatePlayCountMap(isrcs);

      renderPlaylistTracks(
        mainPlaylistData,
        "main-playlist-data-placeholder",
        SERVICE_NAMES.TUNEMELD,
      );

      allData.serviceOrder.forEach((service: string, index: number) => {
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
  } catch (error: unknown) {
    console.error("Error updating genre data:", error);
    hideShimmerLoaders();
  }
}

export function setupGenreSelector(genreSelector: HTMLSelectElement): void {
  genreSelector.addEventListener("change", async function (): Promise<void> {
    const currentGenre = genreSelector.value;
    appRouter.navigateToGenre(currentGenre);
  });
}
