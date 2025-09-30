import logging

from core.constants import GenreName, ServiceName
from core.graphql.schema import schema
from core.utils.redis_cache import CachePrefix, redis_cache_clear
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clear and warm track/playlist GraphQL cache"

    def handle(self, *args, **options):
        total_cleared = 0

        total_cleared += redis_cache_clear(CachePrefix.GQL_PLAYLIST)
        total_cleared += redis_cache_clear(CachePrefix.GQL_PLAYLIST_METADATA)

        logger.info(f"Cleared {total_cleared} track/playlist cache entries")

        self._warm_track_caches()
        logger.info("Track/playlist cache warmed")

    def _warm_track_caches(self):
        """Execute GraphQL queries to warm track/playlist cache with ALL frontend queries."""

        # 1. Warm getAvailableGenres() query
        schema.execute("""
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
        schema.execute("""
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
        schema.execute("""
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
        schema.execute("""
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
            schema.execute(f"""
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
                schema.execute(f"""
                    query GetPlaylistTracks {{
                        playlist(genre: "{genre.value}", service: "{service.value}") {{
                            genreName
                            serviceName
                            tracks {{
                                tunemeldRank(genre: "{genre.value}", service: "{service.value}")
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
                                seenOnSpotify
                                seenOnAppleMusic
                                seenOnSoundcloud
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
            schema.execute(f"""
                query GetRankButtonLabels {{
                    rankButtonLabels(rankType: "{rank_type}") {{
                        buttonType
                        context
                        title
                        ariaLabel
                    }}
                }}
            """)

        # 8. Warm getMiscButtonLabels() for common button types
        misc_button_types = [
            ("close_player", None),
            ("service_player_button", "spotify"),
            ("service_player_button", "apple_music"),
            ("service_player_button", "soundcloud"),
            ("service_player_button", "youtube"),
        ]
        for button_type, context in misc_button_types:
            if context:
                schema.execute(f"""
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
                schema.execute(f"""
                    query GetMiscButtonLabels {{
                        miscButtonLabels(buttonType: "{button_type}") {{
                            buttonType
                            context
                            title
                            ariaLabel
                        }}
                    }}
                """)
