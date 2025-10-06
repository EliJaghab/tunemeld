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
import type { Playlist } from "@/types/index";

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
  const query = `
    query GetInitialPageData($genre: String!) {
      # Service headers and metadata (FAST)
      serviceOrder
      playlistsByGenre(genre: $genre) {
        playlistName
        playlistCoverUrl
        playlistCoverDescriptionText
        playlistUrl
        genreName
        serviceName
        serviceIconUrl
      }
    }
  `;

  const data = await graphqlClient.query(query, { genre });

  return {
    metadata: {
      serviceOrder: data.serviceOrder,
      playlists: data.playlistsByGenre,
    },
    tuneMeldPlaylist: { playlist: null }, // Will be loaded in background
    servicePlaylists: [], // Will be loaded separately!
    serviceOrder: data.serviceOrder,
    // Service playlists will be loaded in background
    spotifyPlaylist: undefined,
    appleMusicPlaylist: undefined,
    soundcloudPlaylist: undefined,
  };
}

// FAST background loading of service playlists (2nd request)
async function fetchServicePlaylists(genre: string): Promise<void> {
  const tuneMeldQuery = `
    query GetServicePlaylists($genre: String!) {
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
          totalCurrentPlayCount
          totalWeeklyChangePercentage
          spotifyCurrentPlayCount
          youtubeCurrentPlayCount
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

  const tuneMeldData = await graphqlClient.query(tuneMeldQuery, { genre });

  if (tuneMeldData.tuneMeldPlaylist) {
    const data = [tuneMeldData.tuneMeldPlaylist];

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

  (async () => {
    try {
      await loadOtherServicePlaylists(genre);
    } catch (error) {
      console.error("Failed to load other service playlists:", error);
    }
  })();
}

async function loadOtherServicePlaylists(genre: string): Promise<void> {
  const servicePlaylistsQuery = `
    query GetServicePlaylists($genre: String!) {
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
          totalCurrentPlayCount
          totalWeeklyChangePercentage
          spotifyCurrentPlayCount
          youtubeCurrentPlayCount
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
          trackDetailUrlSpotify: trackDetailUrl(genre: $genre, rank: "spotify-rank", player: "${SERVICE_NAMES.SPOTIFY}")
          trackDetailUrlAppleMusic: trackDetailUrl(genre: $genre, rank: "spotify-rank", player: "${SERVICE_NAMES.APPLE_MUSIC}")
          trackDetailUrlSoundcloud: trackDetailUrl(genre: $genre, rank: "spotify-rank", player: "${SERVICE_NAMES.SOUNDCLOUD}")
          trackDetailUrlYoutube: trackDetailUrl(genre: $genre, rank: "spotify-rank", player: "${SERVICE_NAMES.YOUTUBE}")
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
          totalCurrentPlayCount
          totalWeeklyChangePercentage
          spotifyCurrentPlayCount
          youtubeCurrentPlayCount
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
          trackDetailUrlSpotify: trackDetailUrl(genre: $genre, rank: "apple-music-rank", player: "${SERVICE_NAMES.SPOTIFY}")
          trackDetailUrlAppleMusic: trackDetailUrl(genre: $genre, rank: "apple-music-rank", player: "${SERVICE_NAMES.APPLE_MUSIC}")
          trackDetailUrlSoundcloud: trackDetailUrl(genre: $genre, rank: "apple-music-rank", player: "${SERVICE_NAMES.SOUNDCLOUD}")
          trackDetailUrlYoutube: trackDetailUrl(genre: $genre, rank: "apple-music-rank", player: "${SERVICE_NAMES.YOUTUBE}")
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
          totalCurrentPlayCount
          totalWeeklyChangePercentage
          spotifyCurrentPlayCount
          youtubeCurrentPlayCount
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
          trackDetailUrlSpotify: trackDetailUrl(genre: $genre, rank: "soundcloud-rank", player: "${SERVICE_NAMES.SPOTIFY}")
          trackDetailUrlAppleMusic: trackDetailUrl(genre: $genre, rank: "soundcloud-rank", player: "${SERVICE_NAMES.APPLE_MUSIC}")
          trackDetailUrlSoundcloud: trackDetailUrl(genre: $genre, rank: "soundcloud-rank", player: "${SERVICE_NAMES.SOUNDCLOUD}")
          trackDetailUrlYoutube: trackDetailUrl(genre: $genre, rank: "soundcloud-rank", player: "${SERVICE_NAMES.YOUTUBE}")
        }
      }
    }
  `;

  const data = await graphqlClient.query(servicePlaylistsQuery, { genre });

  if (data.spotifyPlaylist) {
    renderPlaylistTracks(
      [data.spotifyPlaylist],
      "spotify-data-placeholder",
      SERVICE_NAMES.SPOTIFY,
    );
  }

  if (data.appleMusicPlaylist) {
    renderPlaylistTracks(
      [data.appleMusicPlaylist],
      "apple_music-data-placeholder",
      SERVICE_NAMES.APPLE_MUSIC,
    );
  }

  if (data.soundcloudPlaylist) {
    renderPlaylistTracks(
      [data.soundcloudPlaylist],
      "soundcloud-data-placeholder",
      SERVICE_NAMES.SOUNDCLOUD,
    );
  }
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

    // Always fetch the initial data
    const allData = await fetchInitialPageData(genre);

    if (updateAll) {
      updatePlaylistHeaderSync(
        allData.metadata.playlists,
        allData.metadata.serviceOrder,
        genre,
        null,
      );

      // Load service playlists in background (fast 2nd request!)
      fetchServicePlaylists(genre).catch((error) => {
        console.error("Failed to load service playlists:", error);
      });
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
