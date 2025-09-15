import logging

from core.utils.cache_utils import CachePrefix, ScheduleConfig, clear_cache_by_prefix, is_within_scheduled_time_window
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clear playlist GraphQL cache only within scheduled ETL window"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Force clear playlist cache regardless of schedule")

    def handle(self, *args, **options):
        schedule_config = ScheduleConfig(cache_clear_window_minutes=20)

        if options.get("force") or is_within_scheduled_time_window(schedule_config):
            if options.get("force"):
                logger.info("Force clearing playlist GraphQL cache (--force flag used)")
            else:
                logger.info("Within scheduled ETL window - clearing playlist GraphQL cache for fresh data")

            clear_cache_by_prefix(CachePrefix.GQL_PLAYLIST)
            logger.info("Playlist GraphQL cache cleared")
        else:
            logger.info("Outside scheduled ETL window - preserving playlist GraphQL cache")
            logger.info(
                f"Next scheduled ETL: Daily at 5 PM UTC (±{schedule_config.cache_clear_window_minutes} min window)"
            )
