import logging

from core.constants import GenreName, ServiceName
from core.graphql.schema import schema
from core.utils.local_cache import CachePrefix, local_cache_clear
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clear and warm track/playlist GraphQL cache"

    def handle(self, *args, **options):
        # Clear track/playlist caches only
        playlist_cleared = local_cache_clear(CachePrefix.GQL_PLAYLIST)
        metadata_cleared = local_cache_clear(CachePrefix.GQL_PLAYLIST_METADATA)

        total_cleared = playlist_cleared + metadata_cleared
        logger.info(f"Cleared {total_cleared} track/playlist cache entries")

        # Warm track/playlist caches
        self._warm_track_caches()
        logger.info("Track/playlist cache warmed")

    def _warm_track_caches(self):
        """Execute GraphQL queries to warm track/playlist cache."""
        # Warm playlist metadata cache
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

        # Warm playlist tracks cache
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
