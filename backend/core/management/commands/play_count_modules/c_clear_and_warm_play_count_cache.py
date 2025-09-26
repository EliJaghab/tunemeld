import logging

from core.api.playlist import get_playlist_isrcs
from core.graphql.schema import schema
from core.utils.local_cache import CachePrefix, local_cache_clear
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clear and warm play count GraphQL cache"

    def handle(self, *args, **options):
        play_count_cleared = local_cache_clear(CachePrefix.GQL_PLAY_COUNT)
        logger.info(f"Cleared {play_count_cleared} play count cache entries")

        self._warm_play_count_cache()
        logger.info("Play count cache warmed")

    def _warm_play_count_cache(self):
        """Execute GraphQL queries to warm play count cache."""
        playlist_isrcs = get_playlist_isrcs()

        if playlist_isrcs:
            logger.info(f"Warming play count cache for {len(playlist_isrcs)} playlist ISRCs")

            for isrc in playlist_isrcs:
                schema.execute(f"""
                    query GetTrackPlayCount {{
                        trackPlayCount(isrc: "{isrc}") {{
                            isrc
                            spotifyCurrentPlayCount
                            spotifyWeeklyChangePercentage
                            appleMusicCurrentPlayCount
                            appleMusicWeeklyChangePercentage
                            youtubeCurrentPlayCount
                            youtubeWeeklyChangePercentage
                            soundcloudCurrentPlayCount
                            soundcloudWeeklyChangePercentage
                            totalCurrentPlayCount
                            totalWeeklyChangePercentage
                        }}
                    }}
                """)
        else:
            logger.info("No tracks found in TuneMeld playlists for play count cache warming")
