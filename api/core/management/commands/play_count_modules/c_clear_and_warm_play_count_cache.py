import asyncio
import logging

from core.api.playlist import get_playlist_isrcs
from core.constants import ServiceName
from core.utils.redis_cache import CachePrefix, redis_cache_clear
from django.core.management.base import BaseCommand

from gql.schema import schema

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clear and warm play count GraphQL cache"

    def handle(self, *args, **options):
        asyncio.run(self.async_handle(*args, **options))

    async def async_handle(self, *args, **options):
        play_count_cleared = redis_cache_clear(CachePrefix.GQL_PLAY_COUNT)
        logger.info(f"Cleared {play_count_cleared} play count cache entries")

        await self._warm_play_count_cache()
        logger.info("Play count cache warmed")

    async def _warm_play_count_cache(self):
        """Execute GraphQL queries to warm play count cache."""
        playlist_isrcs = get_playlist_isrcs(ServiceName.TUNEMELD)

        if playlist_isrcs:
            logger.info(f"Warming play count cache for {len(playlist_isrcs)} playlist ISRCs")

            for isrc in playlist_isrcs:
                await schema.execute(f"""
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
