import { updatePlaylistHeader } from "@/components/playlistHeader";
import {
  hideShimmerLoaders,
  showGenreSwitchShimmer,
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
import type { Playlist, Rank } from "@/types/index";

// Global data store for initial page load data
let globalPageData: AllGenreData | null = null;

// AGGRESSIVE DEBUG: Global request counter
let requestCounter = 0;
function logRequest(source: string, description: string) {
  requestCounter++;
  console.log(`🚀 REQUEST #${requestCounter} from ${source}: ${description}`, {
    timestamp: new Date().toISOString(),
    stackTrace: new Error().stack?.split("\n").slice(1, 3),
  });
}

export function getGlobalPageData(): AllGenreData | null {
  return globalPageData;
}

function setGlobalPageData(data: AllGenreData): void {
  globalPageData = data;
}

interface AllGenreData {
  metadata: { serviceOrder: string[]; playlists: Playlist[] };
  mainPlaylist: { playlist: Playlist | null };
  ranks: { ranks: Rank[] };
  genres: { genres: any[]; defaultGenre: string };
  servicePlaylists: ({ playlist: Playlist } | null)[];
  serviceOrder: string[];
  buttonLabels: {
    closePlayer: any[];
    themeToggleLight: any[];
    themeToggleDark: any[];
    acceptTerms: any[];
    moreButtonAppleMusic: any[];
    moreButtonSoundcloud: any[];
    moreButtonSpotify: any[];
    moreButtonYoutube: any[];
  };
  // Individual service playlists from focused query
  spotifyPlaylist?: { playlist: Playlist } | undefined;
  appleMusicPlaylist?: { playlist: Playlist } | undefined;
  soundcloudPlaylist?: { playlist: Playlist } | undefined;
}

// FAST initial load: Service headers + buttons + TuneMeld playlist ONLY (~50KB)
export async function fetchInitialPageData(
  genre: string,
): Promise<AllGenreData> {
  logRequest("fetchInitialPageData", `Initial page data for genre: ${genre}`);
  const query = `
    query GetInitialPageData($genre: String!) {
      # 1. Service headers and metadata (FAST)
      serviceOrder
      playlistsByGenre(genre: $genre) {
        playlistName
        playlistCoverUrl
        playlistCoverDescriptionText
        playlistUrl
        genreName
        serviceName
        serviceIconUrl
        debugCacheStatus
      }

      # 2. Genre buttons (FAST)
      genres {
        id
        name
        displayName
        iconUrl
      }

      # 3. Rank buttons (FAST)
      ranks {
        name
        displayName
        sortField
        sortOrder
        isDefault
        dataField
      }

      # 4. Button labels (FAST)
      closePlayerLabels: miscButtonLabels(buttonType: "close_player") {
        buttonType
        context
        title
        ariaLabel
      }
      themeToggleLightLabels: miscButtonLabels(buttonType: "theme_toggle", context: "light") {
        buttonType
        context
        title
        ariaLabel
      }
      themeToggleDarkLabels: miscButtonLabels(buttonType: "theme_toggle", context: "dark") {
        buttonType
        context
        title
        ariaLabel
      }
      acceptTermsLabels: miscButtonLabels(buttonType: "accept_terms") {
        buttonType
        context
        title
        ariaLabel
      }
      moreButtonAppleMusicLabels: miscButtonLabels(buttonType: "more_button", context: "apple_music") {
        buttonType
        context
        title
        ariaLabel
      }
      moreButtonSoundcloudLabels: miscButtonLabels(buttonType: "more_button", context: "soundcloud") {
        buttonType
        context
        title
        ariaLabel
      }
      moreButtonSpotifyLabels: miscButtonLabels(buttonType: "more_button", context: "spotify") {
        buttonType
        context
        title
        ariaLabel
      }
      moreButtonYoutubeLabels: miscButtonLabels(buttonType: "more_button", context: "youtube") {
        buttonType
        context
        title
        ariaLabel
      }

      # TuneMeld playlist moved to GetServicePlaylists for better performance
    }
  `;

  const data = await graphqlClient.query(query, { genre });

  return {
    metadata: {
      serviceOrder: data.serviceOrder,
      playlists: data.playlistsByGenre,
    },
    mainPlaylist: { playlist: null }, // Will be loaded in background
    ranks: { ranks: data.ranks },
    genres: {
      genres: data.genres,
      defaultGenre: data.genres?.[0]?.name || "pop",
    },
    servicePlaylists: [], // Will be loaded separately!
    serviceOrder: data.serviceOrder,
    buttonLabels: {
      closePlayer: data.closePlayerLabels,
      themeToggleLight: data.themeToggleLightLabels,
      themeToggleDark: data.themeToggleDarkLabels,
      acceptTerms: data.acceptTermsLabels,
      moreButtonAppleMusic: data.moreButtonAppleMusicLabels,
      moreButtonSoundcloud: data.moreButtonSoundcloudLabels,
      moreButtonSpotify: data.moreButtonSpotifyLabels,
      moreButtonYoutube: data.moreButtonYoutubeLabels,
    },
    // Service playlists will be loaded in background
    spotifyPlaylist: undefined,
    appleMusicPlaylist: undefined,
    soundcloudPlaylist: undefined,
  };
}

// FAST background loading of service playlists (2nd request)
async function fetchServicePlaylists(genre: string): Promise<void> {
  logRequest(
    "fetchServicePlaylists",
    `Background service playlists for genre: ${genre}`,
  );
  const query = `
    query GetServicePlaylists($genre: String!) {
      # All playlists including TuneMeld (moved here for faster initial page load)
      tuneMeldPlaylist: playlist(genre: $genre, service: "${SERVICE_NAMES.TUNEMELD}") {
        genreName
        serviceName
        tracks {
          tunemeldRank
          spotifyRank
          appleMusicRank
          soundcloudRank
          isrc
          trackName
          artistName
          fullTrackName
          fullArtistName
          albumName
          albumCoverUrl
          youtubeUrl
          spotifyUrl
          appleMusicUrl
          soundcloudUrl
          buttonLabels {
            buttonType
            context
            title
            ariaLabel
          }
          spotifySource {
            name
            displayName
            url
            iconUrl
          }
          appleMusicSource {
            name
            displayName
            url
            iconUrl
          }
          soundcloudSource {
            name
            displayName
            url
            iconUrl
          }
          youtubeSource {
            name
            displayName
            url
            iconUrl
          }
          trackDetailUrlSpotify: trackDetailUrl(genre: $genre, rank: "tunemeld-rank", player: "${SERVICE_NAMES.SPOTIFY}")
          trackDetailUrlAppleMusic: trackDetailUrl(genre: $genre, rank: "tunemeld-rank", player: "${SERVICE_NAMES.APPLE_MUSIC}")
          trackDetailUrlSoundcloud: trackDetailUrl(genre: $genre, rank: "tunemeld-rank", player: "${SERVICE_NAMES.SOUNDCLOUD}")
          trackDetailUrlYoutube: trackDetailUrl(genre: $genre, rank: "tunemeld-rank", player: "${SERVICE_NAMES.YOUTUBE}")
        }
      }
      spotifyPlaylist: playlist(genre: $genre, service: "${SERVICE_NAMES.SPOTIFY}") {
        genreName
        serviceName
        tracks {
          tunemeldRank
          spotifyRank
          appleMusicRank
          soundcloudRank
          isrc
          trackName
          artistName
          fullTrackName
          fullArtistName
          albumName
          albumCoverUrl
          youtubeUrl
          spotifyUrl
          appleMusicUrl
          soundcloudUrl
          buttonLabels {
            buttonType
            context
            title
            ariaLabel
          }
          spotifySource {
            name
            displayName
            url
            iconUrl
          }
          appleMusicSource {
            name
            displayName
            url
            iconUrl
          }
          soundcloudSource {
            name
            displayName
            url
            iconUrl
          }
          youtubeSource {
            name
            displayName
            url
            iconUrl
          }
          trackDetailUrlSpotify: trackDetailUrl(genre: $genre, rank: "tunemeld-rank", player: "${SERVICE_NAMES.SPOTIFY}")
          trackDetailUrlAppleMusic: trackDetailUrl(genre: $genre, rank: "tunemeld-rank", player: "${SERVICE_NAMES.APPLE_MUSIC}")
          trackDetailUrlSoundcloud: trackDetailUrl(genre: $genre, rank: "tunemeld-rank", player: "${SERVICE_NAMES.SOUNDCLOUD}")
          trackDetailUrlYoutube: trackDetailUrl(genre: $genre, rank: "tunemeld-rank", player: "${SERVICE_NAMES.YOUTUBE}")
        }
      }
      appleMusicPlaylist: playlist(genre: $genre, service: "${SERVICE_NAMES.APPLE_MUSIC}") {
        genreName
        serviceName
        tracks {
          tunemeldRank
          spotifyRank
          appleMusicRank
          soundcloudRank
          isrc
          trackName
          artistName
          fullTrackName
          fullArtistName
          albumName
          albumCoverUrl
          youtubeUrl
          spotifyUrl
          appleMusicUrl
          soundcloudUrl
          buttonLabels {
            buttonType
            context
            title
            ariaLabel
          }
          spotifySource {
            name
            displayName
            url
            iconUrl
          }
          appleMusicSource {
            name
            displayName
            url
            iconUrl
          }
          soundcloudSource {
            name
            displayName
            url
            iconUrl
          }
          youtubeSource {
            name
            displayName
            url
            iconUrl
          }
          trackDetailUrlSpotify: trackDetailUrl(genre: $genre, rank: "tunemeld-rank", player: "${SERVICE_NAMES.SPOTIFY}")
          trackDetailUrlAppleMusic: trackDetailUrl(genre: $genre, rank: "tunemeld-rank", player: "${SERVICE_NAMES.APPLE_MUSIC}")
          trackDetailUrlSoundcloud: trackDetailUrl(genre: $genre, rank: "tunemeld-rank", player: "${SERVICE_NAMES.SOUNDCLOUD}")
          trackDetailUrlYoutube: trackDetailUrl(genre: $genre, rank: "tunemeld-rank", player: "${SERVICE_NAMES.YOUTUBE}")
        }
      }
      soundcloudPlaylist: playlist(genre: $genre, service: "${SERVICE_NAMES.SOUNDCLOUD}") {
        genreName
        serviceName
        tracks {
          tunemeldRank
          spotifyRank
          appleMusicRank
          soundcloudRank
          isrc
          trackName
          artistName
          fullTrackName
          fullArtistName
          albumName
          albumCoverUrl
          youtubeUrl
          spotifyUrl
          appleMusicUrl
          soundcloudUrl
          buttonLabels {
            buttonType
            context
            title
            ariaLabel
          }
          spotifySource {
            name
            displayName
            url
            iconUrl
          }
          appleMusicSource {
            name
            displayName
            url
            iconUrl
          }
          soundcloudSource {
            name
            displayName
            url
            iconUrl
          }
          youtubeSource {
            name
            displayName
            url
            iconUrl
          }
          trackDetailUrlSpotify: trackDetailUrl(genre: $genre, rank: "tunemeld-rank", player: "${SERVICE_NAMES.SPOTIFY}")
          trackDetailUrlAppleMusic: trackDetailUrl(genre: $genre, rank: "tunemeld-rank", player: "${SERVICE_NAMES.APPLE_MUSIC}")
          trackDetailUrlSoundcloud: trackDetailUrl(genre: $genre, rank: "tunemeld-rank", player: "${SERVICE_NAMES.SOUNDCLOUD}")
          trackDetailUrlYoutube: trackDetailUrl(genre: $genre, rank: "tunemeld-rank", player: "${SERVICE_NAMES.YOUTUBE}")
        }
      }
    }
  `;

  const data = await graphqlClient.query(query, { genre });

  // CRITICAL PERFORMANCE FIX: Render playlists asynchronously with timing
  const renderTasks = [];
  const renderTimings: Array<{ service: string; time: number }> = [];

  // Render TuneMeld playlist first (it's the main one)
  if (data.tuneMeldPlaylist) {
    renderTasks.push(() => {
      const startTime = performance.now();
      renderPlaylistTracks(
        [data.tuneMeldPlaylist],
        "main-playlist-data-placeholder",
        SERVICE_NAMES.TUNEMELD,
      );
      const renderTime = performance.now() - startTime;
      renderTimings.push({ service: "TuneMeld", time: renderTime });
      console.log(
        `🎵 TuneMeld playlist rendered in ${renderTime.toFixed(2)}ms`,
      );
    });
  }

  // Render each service playlist
  if (data.spotifyPlaylist) {
    renderTasks.push(() => {
      const startTime = performance.now();
      renderPlaylistTracks(
        [data.spotifyPlaylist],
        `${SERVICE_NAMES.SPOTIFY}-data-placeholder`,
        SERVICE_NAMES.SPOTIFY,
      );
      const renderTime = performance.now() - startTime;
      renderTimings.push({ service: "Spotify", time: renderTime });
      console.log(`🎵 Spotify playlist rendered in ${renderTime.toFixed(2)}ms`);
    });
  }
  if (data.appleMusicPlaylist) {
    renderTasks.push(() => {
      const startTime = performance.now();
      renderPlaylistTracks(
        [data.appleMusicPlaylist],
        `${SERVICE_NAMES.APPLE_MUSIC}-data-placeholder`,
        SERVICE_NAMES.APPLE_MUSIC,
      );
      const renderTime = performance.now() - startTime;
      renderTimings.push({ service: "Apple Music", time: renderTime });
      console.log(
        `🎵 Apple Music playlist rendered in ${renderTime.toFixed(2)}ms`,
      );
    });
  }
  if (data.soundcloudPlaylist) {
    renderTasks.push(() => {
      const startTime = performance.now();
      renderPlaylistTracks(
        [data.soundcloudPlaylist],
        `${SERVICE_NAMES.SOUNDCLOUD}-data-placeholder`,
        SERVICE_NAMES.SOUNDCLOUD,
      );
      const renderTime = performance.now() - startTime;
      renderTimings.push({ service: "SoundCloud", time: renderTime });
      console.log(
        `🎵 SoundCloud playlist rendered in ${renderTime.toFixed(2)}ms`,
      );
    });
  }

  // Execute render tasks asynchronously with better scheduling
  let taskIndex = 0;
  const overallStartTime = performance.now();

  function renderNextTask() {
    if (taskIndex < renderTasks.length) {
      const taskStartTime = performance.now();
      renderTasks[taskIndex]();
      const taskTime = performance.now() - taskStartTime;

      taskIndex++;

      console.log(
        `⚡ Task ${taskIndex}/${
          renderTasks.length
        } completed in ${taskTime.toFixed(2)}ms`,
      );

      // Use requestIdleCallback with timeout for better scheduling
      if (window.requestIdleCallback) {
        requestIdleCallback(renderNextTask, { timeout: 33 }); // 33ms = ~30fps
      } else {
        setTimeout(renderNextTask, 0);
      }
    } else {
      // All tasks completed
      const totalTime = performance.now() - overallStartTime;
      console.log(
        `🏁 All playlists rendered in ${totalTime.toFixed(2)}ms total`,
      );
      console.table(renderTimings);

      // Hide shimmer after completion
      requestAnimationFrame(() => {
        hideShimmerLoaders();
      });
    }
  }

  console.log(`🚀 Starting async render of ${renderTasks.length} playlists...`);
  renderNextTask();
}

export async function updateGenreData(
  genre: string,
  updateAll: boolean = false,
  skipInitialShimmer: boolean = false,
): Promise<void> {
  try {
    // Only show shimmer if this isn't the initial load (router handles initial shimmer)
    if (!skipInitialShimmer) {
      showGenreSwitchShimmer();

      // Show playlist shimmer immediately when switching genres
      if (updateAll) {
        showShimmerLoaders(false);
      }
    }

    // Always fetch the initial data and update global state
    const allData = await fetchInitialPageData(genre);
    setGlobalPageData(allData);

    if (updateAll) {
      updatePlaylistHeaderSync(
        allData.metadata.playlists,
        allData.metadata.serviceOrder,
        genre,
        null,
      );

      // Don't render TuneMeld playlist here since it's null initially
      // It will be rendered when GetServicePlaylists completes

      // Load service playlists in background (fast 2nd request!)
      fetchServicePlaylists(genre).catch((error) => {
        console.error("Failed to load service playlists:", error);
      });
    } else {
      // Non-updateAll case: TuneMeld playlist will come from service playlists query
      // Don't render anything here
    }

    await loadAndRenderRankButtons();
    const currentColumn = stateManager.getCurrentColumn();
    if (currentColumn) {
      sortTable(currentColumn, stateManager.getCurrentOrder());
    }
    // Note: hideShimmerLoaders() is called in fetchServicePlaylists when complete
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
