import asyncio
import logging

from core.constants import GenreName
from core.utils.redis_cache import CachePrefix, redis_cache_clear
from django.core.management.base import BaseCommand

from gql.schema import schema

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clear and warm track/playlist GraphQL cache"

    def handle(self, *args, **options):
        asyncio.run(self.async_handle(*args, **options))

    async def async_handle(self, *args, **options):
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

        await self._warm_track_caches()
        logger.info("Track/playlist cache warmed")

    async def _warm_track_caches(self):
        """Execute EXACTLY the same GraphQL queries that frontend makes."""

        # Warm cache for each genre with the EXACT 2 queries that frontend makes
        for genre in GenreName:
            # 1. GetInitialPageData query (frontend query #1)
            await schema.execute(f"""
                query GetInitialPageData {{
                    # 1. Service headers and metadata (FAST)
                    serviceOrder
                    playlistsByGenre(genre: "{genre.value}") {{
                        playlistName
                        playlistCoverUrl
                        playlistCoverDescriptionText
                        playlistUrl
                        genreName
                        serviceName
                        serviceIconUrl
                    }}

                    # 2. Genre buttons (FAST)
                    genres {{
                        id
                        name
                        displayName
                        iconUrl
                    }}

                    # 3. Rank buttons (FAST)
                    ranks {{
                        name
                        displayName
                        sortField
                        sortOrder
                        isDefault
                        dataField
                    }}

                    # 4. Button labels (FAST)
                    closePlayerLabels: miscButtonLabels(buttonType: "close_player") {{
                        buttonType
                        context
                        title
                        ariaLabel
                    }}
                    themeToggleLightLabels: miscButtonLabels(buttonType: "theme_toggle", context: "light") {{
                        buttonType
                        context
                        title
                        ariaLabel
                    }}
                    themeToggleDarkLabels: miscButtonLabels(buttonType: "theme_toggle", context: "dark") {{
                        buttonType
                        context
                        title
                        ariaLabel
                    }}
                    acceptTermsLabels: miscButtonLabels(buttonType: "accept_terms") {{
                        buttonType
                        context
                        title
                        ariaLabel
                    }}
                    moreButtonAppleMusicLabels: miscButtonLabels(buttonType: "more_button", context: "apple_music") {{
                        buttonType
                        context
                        title
                        ariaLabel
                    }}
                    moreButtonSoundcloudLabels: miscButtonLabels(buttonType: "more_button", context: "soundcloud") {{
                        buttonType
                        context
                        title
                        ariaLabel
                    }}
                    moreButtonSpotifyLabels: miscButtonLabels(buttonType: "more_button", context: "spotify") {{
                        buttonType
                        context
                        title
                        ariaLabel
                    }}
                    moreButtonYoutubeLabels: miscButtonLabels(buttonType: "more_button", context: "youtube") {{
                        buttonType
                        context
                        title
                        ariaLabel
                    }}

                    # TuneMeld playlist moved to GetServicePlaylists for better performance
                }}
            """)

            # 2. GetServicePlaylists query (frontend query #2)
            await schema.execute(f"""
                query GetServicePlaylists {{
                    # All playlists including TuneMeld (moved here for faster initial page load)
                    tuneMeldPlaylist: playlist(genre: "{genre.value}", service: "tunemeld") {{
                        genreName
                        serviceName
                        tracks {{
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
                            buttonLabels {{
                                buttonType
                                context
                                title
                                ariaLabel
                            }}
                            spotifySource {{
                                name
                                displayName
                                url
                                iconUrl
                            }}
                            appleMusicSource {{
                                name
                                displayName
                                url
                                iconUrl
                            }}
                            soundcloudSource {{
                                name
                                displayName
                                url
                                iconUrl
                            }}
                            youtubeSource {{
                                name
                                displayName
                                url
                                iconUrl
                            }}
                            trackDetailUrlSpotify: trackDetailUrl(
                                genre: "{genre.value}", rank: "tunemeld-rank", player: "spotify"
                            )
                            trackDetailUrlAppleMusic: trackDetailUrl(
                                genre: "{genre.value}", rank: "tunemeld-rank", player: "apple_music"
                            )
                            trackDetailUrlSoundcloud: trackDetailUrl(
                                genre: "{genre.value}", rank: "tunemeld-rank", player: "soundcloud"
                            )
                            trackDetailUrlYoutube: trackDetailUrl(
                                genre: "{genre.value}", rank: "tunemeld-rank", player: "youtube"
                            )
                        }}
                    }}
                    spotifyPlaylist: playlist(genre: "{genre.value}", service: "spotify") {{
                        genreName
                        serviceName
                        tracks {{
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
                            buttonLabels {{
                                buttonType
                                context
                                title
                                ariaLabel
                            }}
                            spotifySource {{
                                name
                                displayName
                                url
                                iconUrl
                            }}
                            appleMusicSource {{
                                name
                                displayName
                                url
                                iconUrl
                            }}
                            soundcloudSource {{
                                name
                                displayName
                                url
                                iconUrl
                            }}
                            youtubeSource {{
                                name
                                displayName
                                url
                                iconUrl
                            }}
                            trackDetailUrlSpotify: trackDetailUrl(
                                genre: "{genre.value}", rank: "tunemeld-rank", player: "spotify"
                            )
                            trackDetailUrlAppleMusic: trackDetailUrl(
                                genre: "{genre.value}", rank: "tunemeld-rank", player: "apple_music"
                            )
                            trackDetailUrlSoundcloud: trackDetailUrl(
                                genre: "{genre.value}", rank: "tunemeld-rank", player: "soundcloud"
                            )
                            trackDetailUrlYoutube: trackDetailUrl(
                                genre: "{genre.value}", rank: "tunemeld-rank", player: "youtube"
                            )
                        }}
                    }}
                    appleMusicPlaylist: playlist(genre: "{genre.value}", service: "apple_music") {{
                        genreName
                        serviceName
                        tracks {{
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
                            buttonLabels {{
                                buttonType
                                context
                                title
                                ariaLabel
                            }}
                            spotifySource {{
                                name
                                displayName
                                url
                                iconUrl
                            }}
                            appleMusicSource {{
                                name
                                displayName
                                url
                                iconUrl
                            }}
                            soundcloudSource {{
                                name
                                displayName
                                url
                                iconUrl
                            }}
                            youtubeSource {{
                                name
                                displayName
                                url
                                iconUrl
                            }}
                            trackDetailUrlSpotify: trackDetailUrl(
                                genre: "{genre.value}", rank: "tunemeld-rank", player: "spotify"
                            )
                            trackDetailUrlAppleMusic: trackDetailUrl(
                                genre: "{genre.value}", rank: "tunemeld-rank", player: "apple_music"
                            )
                            trackDetailUrlSoundcloud: trackDetailUrl(
                                genre: "{genre.value}", rank: "tunemeld-rank", player: "soundcloud"
                            )
                            trackDetailUrlYoutube: trackDetailUrl(
                                genre: "{genre.value}", rank: "tunemeld-rank", player: "youtube"
                            )
                        }}
                    }}
                    soundcloudPlaylist: playlist(genre: "{genre.value}", service: "soundcloud") {{
                        genreName
                        serviceName
                        tracks {{
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
                            buttonLabels {{
                                buttonType
                                context
                                title
                                ariaLabel
                            }}
                            spotifySource {{
                                name
                                displayName
                                url
                                iconUrl
                            }}
                            appleMusicSource {{
                                name
                                displayName
                                url
                                iconUrl
                            }}
                            soundcloudSource {{
                                name
                                displayName
                                url
                                iconUrl
                            }}
                            youtubeSource {{
                                name
                                displayName
                                url
                                iconUrl
                            }}
                            trackDetailUrlSpotify: trackDetailUrl(
                                genre: "{genre.value}", rank: "tunemeld-rank", player: "spotify"
                            )
                            trackDetailUrlAppleMusic: trackDetailUrl(
                                genre: "{genre.value}", rank: "tunemeld-rank", player: "apple_music"
                            )
                            trackDetailUrlSoundcloud: trackDetailUrl(
                                genre: "{genre.value}", rank: "tunemeld-rank", player: "soundcloud"
                            )
                            trackDetailUrlYoutube: trackDetailUrl(
                                genre: "{genre.value}", rank: "tunemeld-rank", player: "youtube"
                            )
                        }}
                    }}
                }}
            """)

        logger.info("Cache warmed with EXACT frontend queries for all genres")
