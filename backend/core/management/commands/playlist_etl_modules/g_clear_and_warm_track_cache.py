import logging

from core.constants import GenreName, ServiceName
from core.graphql.schema import schema
from core.utils.local_cache import CachePrefix, local_cache_clear
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clear and warm track/playlist GraphQL cache"

    def handle(self, *args, **options):
        total_cleared = 0

        total_cleared += local_cache_clear(CachePrefix.GQL_PLAYLIST)
        total_cleared += local_cache_clear(CachePrefix.GQL_PLAYLIST_METADATA)

        logger.info(f"Cleared {total_cleared} track/playlist cache entries")

        self._warm_track_caches()
        logger.info("Track/playlist cache warmed")

    def _warm_track_caches(self):
        """Execute GraphQL queries to warm track/playlist cache."""
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
                    }}
                }}
            """)

        for genre in GenreName:
            for service in [ServiceName.SPOTIFY, ServiceName.APPLE_MUSIC, ServiceName.SOUNDCLOUD, ServiceName.TUNEMELD]:
                schema.execute(f"""
                    query GetPlaylistTracks {{
                        playlist(genre: "{genre.value}", service: "{service.value}") {{
                            genreName
                            serviceName
                            tracks {{
                                trackName
                                artistName
                                albumName
                                isrc
                                spotifyUrl
                                appleMusicUrl
                                youtubeUrl
                                soundcloudUrl
                                albumCoverUrl
                                aggregateRank
                                aggregateScore
                            }}
                        }}
                    }}
                """)
