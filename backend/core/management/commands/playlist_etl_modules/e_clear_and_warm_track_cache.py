import asyncio
import logging

from core.constants import GenreName, ServiceName
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
        """Execute GraphQL queries to warm track/playlist cache with ALL frontend queries."""

        # 1. Warm getAvailableGenres() query
        await schema.execute("""
            query GetAvailableGenres {
                genres {
                    id
                    name
                    displayName
                    iconUrl
                    buttonLabels {
                        buttonType
                        context
                        title
                        ariaLabel
                    }
                }
                defaultGenre
            }
        """)

        # 2. Warm fetchPlaylistRanks() query
        await schema.execute("""
            query GetPlaylistRanks {
                ranks {
                    name
                    displayName
                    sortField
                    sortOrder
                    isDefault
                    dataField
                }
            }
        """)

        # 3. Warm getServiceConfigs() query
        await schema.execute("""
            query GetServiceConfigs {
                serviceConfigs {
                    name
                    displayName
                    iconUrl
                    urlField
                    sourceField
                    buttonLabels {
                        buttonType
                        context
                        title
                        ariaLabel
                    }
                }
            }
        """)

        # 4. Warm getIframeConfigs() query
        await schema.execute("""
            query GetIframeConfigs {
                iframeConfigs {
                    serviceName
                    embedBaseUrl
                    embedParams
                    allow
                    height
                    referrerPolicy
                }
            }
        """)

        # 5. Warm getPlaylistMetadata() query for each genre
        for genre in GenreName:
            await schema.execute(f"""
                query GetPlaylistMetadata {{
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
                }}
            """)

        # 6. Warm getPlaylistTracks() query for each genre/service combination with FULL field set
        for genre in GenreName:
            for service in [ServiceName.SPOTIFY, ServiceName.APPLE_MUSIC, ServiceName.SOUNDCLOUD, ServiceName.TUNEMELD]:
                await schema.execute(f"""
                    query GetPlaylistTracks {{
                        playlist(genre: "{genre.value}", service: "{service.value}") {{
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
                                    genre: "{genre.value}",
                                    rank: "tunemeld-rank",
                                    player: "spotify"
                                )
                                trackDetailUrlAppleMusic: trackDetailUrl(
                                    genre: "{genre.value}",
                                    rank: "tunemeld-rank",
                                    player: "apple_music"
                                )
                                trackDetailUrlSoundcloud: trackDetailUrl(
                                    genre: "{genre.value}",
                                    rank: "tunemeld-rank",
                                    player: "soundcloud"
                                )
                                trackDetailUrlYoutube: trackDetailUrl(
                                    genre: "{genre.value}",
                                    rank: "tunemeld-rank",
                                    player: "youtube"
                                )
                            }}
                        }}
                    }}
                """)

        # 7. Warm getRankButtonLabels() for each rank type
        rank_types = ["tunemeld-rank", "spotify-rank", "apple-music-rank", "soundcloud-rank"]
        for rank_type in rank_types:
            await schema.execute(f"""
                query GetRankButtonLabels {{
                    rankButtonLabels(rankType: "{rank_type}") {{
                        buttonType
                        context
                        title
                        ariaLabel
                    }}
                }}
            """)

        # 8. Warm getMiscButtonLabels() for ALL button types used by frontend
        misc_button_types = [
            ("close_player", None),
            ("service_player_button", "spotify"),
            ("service_player_button", "apple_music"),
            ("service_player_button", "soundcloud"),
            ("service_player_button", "youtube"),
            ("more_button", "spotify"),
            ("more_button", "apple_music"),
            ("more_button", "soundcloud"),
            ("more_button", "tunemeld"),
            ("collapse_button", "spotify_collapsed"),
            ("collapse_button", "spotify_expanded"),
            ("collapse_button", "apple_music_collapsed"),
            ("collapse_button", "apple_music_expanded"),
            ("collapse_button", "soundcloud_collapsed"),
            ("collapse_button", "soundcloud_expanded"),
            ("collapse_button", "main_collapsed"),
            ("collapse_button", "main_expanded"),
        ]
        for button_type, context in misc_button_types:
            if context:
                await schema.execute(f"""
                    query GetMiscButtonLabels {{
                        miscButtonLabels(buttonType: "{button_type}", context: "{context}") {{
                            buttonType
                            context
                            title
                            ariaLabel
                        }}
                    }}
                """)
            else:
                await schema.execute(f"""
                    query GetMiscButtonLabels {{
                        miscButtonLabels(buttonType: "{button_type}") {{
                            buttonType
                            context
                            title
                            ariaLabel
                        }}
                    }}
                """)
