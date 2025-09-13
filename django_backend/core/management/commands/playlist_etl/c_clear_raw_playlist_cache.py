import logging

from core.utils.cache_utils import (
    ScheduleConfig,
    _generate_cache_key,
    get_all_raw_playlist_cache_keys,
    is_within_scheduled_time_window,
)
from django.core.cache import cache
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clear raw playlist cache (RapidAPI + Spotify) only within scheduled ETL window"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force", action="store_true", help="Force clear raw playlist cache regardless of schedule"
        )

    def handle(self, *args, **options):
        schedule_config = ScheduleConfig()

        if options.get("force") or is_within_scheduled_time_window(schedule_config):
            if options.get("force"):
                logger.info("Force clearing raw playlist cache (--force flag used)")
            else:
                logger.info("Within scheduled ETL window - clearing raw playlist cache for fresh data")

            cache_keys_with_prefixes = get_all_raw_playlist_cache_keys()

            cleared_count = 0
            for prefix, key_data in cache_keys_with_prefixes:
                cache_key = _generate_cache_key(prefix, key_data)
                if cache.get(cache_key):
                    cache.delete(cache_key)
                    cleared_count += 1
                    logger.info(f"Cleared {prefix.value} cache: {key_data}")

            logger.info(f"Raw playlist cache clearing completed - {cleared_count} keys cleared")
        else:
            logger.info("Outside scheduled ETL window - preserving raw playlist cache to avoid rate limits")
            logger.info(
                f"Next scheduled ETL: Saturdays at 5 PM UTC (±{schedule_config.cache_clear_window_minutes} min window)"
            )

        logger.info("Raw playlist cache clearing completed")
