import { updatePlaylistHeader } from "@/components/playlistHeader";
import { debugLog } from "@/config/config";
import { hideShimmerLoaders } from "@/components/shimmer";
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

// Cached playlist data for rendering after shimmer (services only)
let cachedSpotifyData: Playlist[] | null = null;
let cachedAppleMusicData: Playlist[] | null = null;
let cachedSoundcloudData: Playlist[] | null = null;

const selectorsDebug = (message: string, meta?: unknown) => {
  debugLog("Selectors", message, meta);
};

export function renderCachedPlaylists(): void {
  if (cachedSpotifyData) {
    const spotifyPlaceholder = document.getElementById(
      "spotify-data-placeholder",
    );
    const alreadyRendered =
      spotifyPlaceholder?.getAttribute("data-rendered") === "true";
    if (spotifyPlaceholder && !alreadyRendered) {
      renderPlaylistTracks(
        cachedSpotifyData,
        "spotify-data-placeholder",
        SERVICE_NAMES.SPOTIFY,
      );
    }
  }
  if (cachedAppleMusicData) {
    const applePlaceholder = document.getElementById(
      "apple_music-data-placeholder",
    );
    const alreadyRendered =
      applePlaceholder?.getAttribute("data-rendered") === "true";
    if (applePlaceholder && !alreadyRendered) {
      renderPlaylistTracks(
        cachedAppleMusicData,
        "apple_music-data-placeholder",
        SERVICE_NAMES.APPLE_MUSIC,
      );
    }
  }
  if (cachedSoundcloudData) {
    const soundcloudPlaceholder = document.getElementById(
      "soundcloud-data-placeholder",
    );
    const alreadyRendered =
      soundcloudPlaceholder?.getAttribute("data-rendered") === "true";
    if (soundcloudPlaceholder && !alreadyRendered) {
      renderPlaylistTracks(
        cachedSoundcloudData,
        "soundcloud-data-placeholder",
        SERVICE_NAMES.SOUNDCLOUD,
      );
    }
  }
}

// Listen for the event to render cached playlists
window.addEventListener("renderCachedPlaylists", renderCachedPlaylists);

interface AllGenreData {
  metadata: { serviceOrder: string[]; playlists: Playlist[] };
  tuneMeldPlaylist: { playlist: Playlist | null };
  servicePlaylists: ({ playlist: Playlist } | null)[];
  serviceOrder: string[];
  // Individual service playlists from focused query
  spotifyPlaylist?: { playlist: Playlist } | undefined;
  appleMusicPlaylist?: { playlist: Playlist } | undefined;
  soundcloudPlaylist?: { playlist: Playlist } | undefined;
}

// FAST genre switch: Service headers metadata ONLY
async function fetchInitialPageData(genre: string): Promise<AllGenreData> {
  const metadata = await graphqlClient.getPlaylistMetadata(genre);

  return {
    metadata,
    tuneMeldPlaylist: { playlist: null }, // Will be loaded in background
    servicePlaylists: [], // Will be loaded separately!
    serviceOrder: metadata.serviceOrder,
    // Service playlists will be loaded in background
    spotifyPlaylist: undefined,
    appleMusicPlaylist: undefined,
    soundcloudPlaylist: undefined,
  };
}

// FAST background loading of service playlists (2nd request)
async function fetchServicePlaylists(genre: string): Promise<void> {
  selectorsDebug("fetchServicePlaylists:start", { genre });
  const tuneMeldPlaylist = await graphqlClient.getPlaylist(
    genre,
    SERVICE_NAMES.TUNEMELD,
  );
  selectorsDebug("fetchServicePlaylists: tunemeld playlist data fetched");

  if (tuneMeldPlaylist) {
    const data = [tuneMeldPlaylist];

    setPlaylistData(data);

    const isInitial = stateManager.isInitialLoad();
    selectorsDebug(
      "fetchServicePlaylists: rendering tunemeld playlist tracks",
      {
        isInitial,
      },
    );

    // Sort data immediately after fetching if current rank is not default
    const currentColumn = stateManager.getCurrentColumn();
    const currentOrder = stateManager.getCurrentOrder();
    if (currentColumn) {
      sortTable(currentColumn, currentOrder);
    } else {
      // No current column - just render with backend order
      renderPlaylistTracks(
        data,
        "main-playlist-data-placeholder",
        SERVICE_NAMES.TUNEMELD,
        null,
        { forceRender: !isInitial },
      );
    }
  }

  // Don't hide shimmer here - let StateManager coordinate when everything is loaded

  // Load service playlists AFTER TuneMeld playlist is rendered
  try {
    selectorsDebug("fetchServicePlaylists: loading other service playlists");
    await loadOtherServicePlaylists(genre);
    selectorsDebug("fetchServicePlaylists: other service playlists loaded");
  } catch (error) {
    console.error("Failed to load other service playlists:", error);
  }
}

async function loadOtherServicePlaylists(genre: string): Promise<void> {
  selectorsDebug(`loadOtherServicePlaylists: start, genre=${genre}`);
  const [spotifyPlaylist, appleMusicPlaylist, soundcloudPlaylist] =
    await Promise.all([
      graphqlClient.getPlaylist(genre, SERVICE_NAMES.SPOTIFY),
      graphqlClient.getPlaylist(genre, SERVICE_NAMES.APPLE_MUSIC),
      graphqlClient.getPlaylist(genre, SERVICE_NAMES.SOUNDCLOUD),
    ]);

  selectorsDebug(
    "loadOtherServicePlaylists: other service playlists data fetched",
  );

  // Cache the data
  if (spotifyPlaylist) {
    cachedSpotifyData = [spotifyPlaylist];
  }
  if (appleMusicPlaylist) {
    cachedAppleMusicData = [appleMusicPlaylist];
  }
  if (soundcloudPlaylist) {
    cachedSoundcloudData = [soundcloudPlaylist];
  }

  selectorsDebug("loadOtherServicePlaylists: rendering tracks");
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

  selectorsDebug("loadOtherServicePlaylists: end");
}

export async function updateGenreData(
  genre: string,
  updateAll: boolean = false,
  skipInitialShimmer: boolean = false,
): Promise<void> {
  selectorsDebug(
    `updateGenreData: start, genre=${genre}, updateAll=${updateAll}, skipInitialShimmer=${skipInitialShimmer}`,
  );
  try {
    // Clear cached data when switching genres
    if (!skipInitialShimmer) {
      cachedSpotifyData = null;
      cachedAppleMusicData = null;
      cachedSoundcloudData = null;
    }

    // Shimmer is now handled by button click handlers and initial load
    // No shimmer logic needed here

    // Always fetch the initial data
    selectorsDebug("updateGenreData: fetching initial page data");
    const allData = await fetchInitialPageData(genre);
    selectorsDebug("updateGenreData: initial page data fetched");

    if (updateAll) {
      updatePlaylistHeaderSync(
        allData.metadata.playlists,
        allData.metadata.serviceOrder,
        genre,
        null,
      );

      // Mark playlist header as loaded for shimmer coordination
      selectorsDebug("updateGenreData: marking playlistDataLoaded as loaded");
      stateManager.markLoaded("playlistDataLoaded");

      // Load service playlists in background (fast 2nd request!)
      selectorsDebug("updateGenreData: fetching service playlists");
      fetchServicePlaylists(genre).catch((error) => {
        console.error("Failed to load service playlists:", error);
      });
    }

    selectorsDebug("updateGenreData: loading rank buttons");
    await loadAndRenderRankButtons();

    // Mark rank buttons as loaded for shimmer coordination
    // Only mark as loaded when NOT initial load (skipInitialShimmer would be false for genre switch)
    if (!skipInitialShimmer) {
      selectorsDebug("updateGenreData: marking rankButtonsLoaded as loaded");
      stateManager.markLoaded("rankButtonsLoaded");
    }

    // Note: Sorting is now handled in fetchServicePlaylists after data is loaded
    // Note: Shimmer is hidden by StateManager when all components are loaded
    resetCollapseStates();
    await addToggleEventListeners();
    setupBodyClickListener(genre);
    selectorsDebug("updateGenreData: end");
  } catch (error: unknown) {
    console.error("Error updating genre data:", error);
    hideShimmerLoaders();
  }
}
