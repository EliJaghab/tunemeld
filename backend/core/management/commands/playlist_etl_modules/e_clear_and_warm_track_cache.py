import logging

from core.constants import GenreName
from core.utils.redis_cache import CachePrefix, redis_cache_clear
from django.core.management.base import BaseCommand

from gql.schema import schema

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clear and warm track/playlist GraphQL cache"

    def handle(self, *args, **options):
        total_cleared = 0

        # Clear all GraphQL cache prefixes
        total_cleared += redis_cache_clear(CachePrefix.GQL_PLAYLIST)
        total_cleared += redis_cache_clear(CachePrefix.GQL_PLAYLIST_METADATA)
        total_cleared += redis_cache_clear(CachePrefix.GQL_GENRES)
        total_cleared += redis_cache_clear(CachePrefix.GQL_SERVICE_CONFIGS)
        total_cleared += redis_cache_clear(CachePrefix.GQL_IFRAME_CONFIGS)
        total_cleared += redis_cache_clear(CachePrefix.GQL_IFRAME_URL)
        total_cleared += redis_cache_clear(CachePrefix.GQL_BUTTON_LABELS)
        total_cleared += redis_cache_clear(CachePrefix.GQL_TRACK)

        logger.info(f"Cleared {total_cleared} GraphQL cache entries")

        self._warm_track_caches()
        logger.info("Track/playlist cache warmed")

    def _warm_track_caches(self):
        """Execute EXACTLY the same GraphQL queries that frontend makes."""

        # Warm cache for each genre with the EXACT 2 queries that frontend makes
        for genre in GenreName:
            # 1. GetInitialPageData query (frontend query #1) - EXACT MATCH
            schema.execute_sync(
                """
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
                """,
                variable_values={"genre": genre.value},
            )

            # 2. First GetServicePlaylists query - TuneMeld ONLY (frontend query #2a)
            schema.execute_sync(
                """
                query GetServicePlaylists($genre: String!) {
                  tuneMeldPlaylist: playlist(genre: $genre, service: "tunemeld") {
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
                      trackDetailUrlSpotify: trackDetailUrl(
                        genre: $genre, rank: "tunemeld-rank", player: "spotify"
                      )
                      trackDetailUrlAppleMusic: trackDetailUrl(
                        genre: $genre, rank: "tunemeld-rank", player: "apple_music"
                      )
                      trackDetailUrlSoundcloud: trackDetailUrl(
                        genre: $genre, rank: "tunemeld-rank", player: "soundcloud"
                      )
                      trackDetailUrlYoutube: trackDetailUrl(
                        genre: $genre, rank: "tunemeld-rank", player: "youtube"
                      )
                    }
                  }
                }
                """,
                variable_values={"genre": genre.value},
            )

            # 3. Second GetServicePlaylists query - Other services ONLY (frontend query #2b)
            schema.execute_sync(
                """
                query GetServicePlaylists($genre: String!) {
                  spotifyPlaylist: playlist(genre: $genre, service: "spotify") {
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
                      trackDetailUrlSpotify: trackDetailUrl(
                        genre: $genre, rank: "spotify-rank", player: "spotify"
                      )
                      trackDetailUrlAppleMusic: trackDetailUrl(
                        genre: $genre, rank: "spotify-rank", player: "apple_music"
                      )
                      trackDetailUrlSoundcloud: trackDetailUrl(
                        genre: $genre, rank: "spotify-rank", player: "soundcloud"
                      )
                      trackDetailUrlYoutube: trackDetailUrl(
                        genre: $genre, rank: "spotify-rank", player: "youtube"
                      )
                    }
                  }
                  appleMusicPlaylist: playlist(genre: $genre, service: "apple_music") {
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
                      trackDetailUrlSpotify: trackDetailUrl(
                        genre: $genre, rank: "apple-music-rank", player: "spotify"
                      )
                      trackDetailUrlAppleMusic: trackDetailUrl(
                        genre: $genre, rank: "apple-music-rank", player: "apple_music"
                      )
                      trackDetailUrlSoundcloud: trackDetailUrl(
                        genre: $genre, rank: "apple-music-rank", player: "soundcloud"
                      )
                      trackDetailUrlYoutube: trackDetailUrl(
                        genre: $genre, rank: "apple-music-rank", player: "youtube"
                      )
                    }
                  }
                  soundcloudPlaylist: playlist(genre: $genre, service: "soundcloud") {
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
                      trackDetailUrlSpotify: trackDetailUrl(
                        genre: $genre, rank: "soundcloud-rank", player: "spotify"
                      )
                      trackDetailUrlAppleMusic: trackDetailUrl(
                        genre: $genre, rank: "soundcloud-rank", player: "apple_music"
                      )
                      trackDetailUrlSoundcloud: trackDetailUrl(
                        genre: $genre, rank: "soundcloud-rank", player: "soundcloud"
                      )
                      trackDetailUrlYoutube: trackDetailUrl(
                        genre: $genre, rank: "soundcloud-rank", player: "youtube"
                      )
                    }
                  }
                }
                """,
                variable_values={"genre": genre.value},
            )

        logger.info("Cache warmed with EXACT frontend queries for all genres")
