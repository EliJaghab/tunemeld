import logging

from core.utils.cache_utils import ScheduleConfig, is_within_scheduled_time_window
from django.core.cache import cache
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clear GraphQL and other non-RapidAPI caches only within scheduled ETL window"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Force clear GraphQL cache regardless of schedule")

    def handle(self, *args, **options):
        schedule_config = ScheduleConfig(cache_clear_window_minutes=20)

        if options.get("force") or is_within_scheduled_time_window(schedule_config):
            if options.get("force"):
                logger.info("Force clearing GraphQL cache (--force flag used)")
            else:
                logger.info("Within scheduled ETL window - clearing GraphQL cache for fresh data")

            cache.clear()
            logger.info("GraphQL and other caches cleared")
        else:
            logger.info("Outside scheduled ETL window - preserving GraphQL cache")
            logger.info(
                f"Next scheduled ETL: Saturdays at 5 PM UTC (±{schedule_config.cache_clear_window_minutes} min window)"
            )
