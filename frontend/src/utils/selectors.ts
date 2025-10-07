import { updatePlaylistHeader } from "@/components/playlistHeader";
import {
  hideShimmerLoaders,
  showServiceHeaderAndTrackShimmer,
  showTrackShimmer,
  showShimmerLoaders,
} from "@/components/shimmer";
import {
  addToggleEventListeners,
  renderPlaylistTracks,
  resetCollapseStates,
  setPlaylistData,
  sortTable,
} from "@/components/playlist";
import { loadAndRenderRankButtons } from "@/components/rankButton";
import { setupBodyClickListener } from "@/components/servicePlayer";
import { stateManager } from "@/state/StateManager";
import { appRouter } from "@/routing/router";
import { graphqlClient } from "@/services/graphql-client";
import { SERVICE_NAMES } from "@/config/constants";
import { updatePlaylistHeaderSync } from "@/components/playlistHeader";
import type { Playlist } from "@/types/index";

// Load TuneMeld playlist first (fast display)
async function fetchTuneMeldPlaylist(genre: string): Promise<void> {
  const playlist = await graphqlClient.getPlaylist(
    genre,
    SERVICE_NAMES.TUNEMELD,
  );

  if (playlist) {
    const data = [playlist];
    setPlaylistData(data);
    renderPlaylistTracks(
      data,
      "main-playlist-data-placeholder",
      SERVICE_NAMES.TUNEMELD,
    );
  }

  requestAnimationFrame(() => {
    hideShimmerLoaders();
  });

  // Load other services in background
  (async () => {
    try {
      await loadOtherServicePlaylists(genre);
    } catch (error) {
      console.error("Failed to load other service playlists:", error);
    }
  })();
}

async function loadOtherServicePlaylists(genre: string): Promise<void> {
  // Load other service playlists in parallel for better performance
  const [spotifyPlaylist, appleMusicPlaylist, soundcloudPlaylist] =
    await Promise.all([
      graphqlClient.getPlaylist(genre, SERVICE_NAMES.SPOTIFY),
      graphqlClient.getPlaylist(genre, SERVICE_NAMES.APPLE_MUSIC),
      graphqlClient.getPlaylist(genre, SERVICE_NAMES.SOUNDCLOUD),
    ]);

  if (spotifyPlaylist) {
    renderPlaylistTracks(
      [spotifyPlaylist],
      "spotify-data-placeholder",
      SERVICE_NAMES.SPOTIFY,
    );
  }

  if (appleMusicPlaylist) {
    renderPlaylistTracks(
      [appleMusicPlaylist],
      "apple_music-data-placeholder",
      SERVICE_NAMES.APPLE_MUSIC,
    );
  }

  if (soundcloudPlaylist) {
    renderPlaylistTracks(
      [soundcloudPlaylist],
      "soundcloud-data-placeholder",
      SERVICE_NAMES.SOUNDCLOUD,
    );
  }
}

export async function updateGenreData(
  genre: string,
  updateAll: boolean = false,
): Promise<void> {
  try {
    // Show appropriate shimmer based on update type
    if (updateAll) {
      // Genre change or initial load: show service header and track shimmer
      showServiceHeaderAndTrackShimmer();
    } else {
      // Rank change: show only track shimmer
      showTrackShimmer();
    }

    // Fetch metadata and service order first (lightweight, no tracks)
    const metadata = await graphqlClient.getPlaylistMetadata(genre);

    // Always update the header with playlist metadata
    updatePlaylistHeaderSync(
      metadata.playlists,
      metadata.serviceOrder,
      genre,
      null,
    );

    if (updateAll) {
      // Load TuneMeld playlist first, then others in background
      fetchTuneMeldPlaylist(genre).catch((error) => {
        console.error("Failed to load TuneMeld playlist:", error);
      });
    }

    await loadAndRenderRankButtons();
    const currentColumn = stateManager.getCurrentColumn();
    if (currentColumn) {
      sortTable(currentColumn, stateManager.getCurrentOrder());
    }
    // Note: hideShimmerLoaders() is called in fetchTuneMeldPlaylist when complete
    resetCollapseStates();
    await addToggleEventListeners();
    setupBodyClickListener(genre);
  } catch (error: unknown) {
    console.error("Error updating genre data:", error);
    hideShimmerLoaders();
  }
}
