import time
from typing import Any

from core.management.commands.clear_and_warm_cache import Command as ClearAndWarmCacheCommand
from core.management.commands.play_count_modules.a_historical_play_count import Command as HistoricalPlayCountCommand
from core.management.commands.play_count_modules.b_aggregate_play_count import Command as AggregatePlayCountCommand
from core.management.commands.play_count_modules.c_clear_play_count_cache import Command as ClearPlayCountCacheCommand
from core.models.play_counts import HistoricalTrackPlayCount
from core.utils.utils import get_logger
from django.core.management.base import BaseCommand
from django.db import models
from django.utils import timezone

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Run the complete play count ETL pipeline"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, help="Limit tracks to process for testing")

    def handle(self, *args: Any, **options: Any) -> None:
        start_time = time.time()
        limit = options.get("limit")

        try:
            logger.info("Starting Play Count ETL Pipeline")

            logger.info("Step 1: Running Historical Play Count extraction")
            historical_command = HistoricalPlayCountCommand()
            historical_command.handle(limit=limit)

            logger.info("Step 2: Computing aggregate play counts with weekly changes")
            aggregate_command = AggregatePlayCountCommand()
            aggregate_command.handle()

            logger.info("Step 3: Clearing play count GraphQL cache...")
            clear_cache_command = ClearPlayCountCacheCommand()
            clear_cache_command.handle()

            logger.info("Step 4: Clearing and warming GraphQL cache...")
            ClearAndWarmCacheCommand().handle()

            duration = time.time() - start_time
            logger.info(f"Play Count ETL Pipeline completed in {duration:.1f} seconds")

            self._print_final_summary()

        except Exception as e:
            logger.error(f"Play Count ETL Pipeline failed: {e}")
            duration = time.time() - start_time
            logger.info(f"Pipeline failed after {duration:.1f} seconds")
            raise

    def _print_final_summary(self):
        today = timezone.now().date()
        records = HistoricalTrackPlayCount.objects.filter(recorded_date=today)
        total_records = records.count()

        if total_records == 0:
            logger.info("No historical track play count records found for today")
            return

        service_breakdown = records.values("service__name").annotate(count=models.Count("id"))

        logger.info("\nHistorical Track Play Count ETL Results:")
        logger.info(f"Historical track play count records: {total_records}")
        logger.info("\nBreakdown by service:")

        for service in service_breakdown:
            service_name = service["service__name"].lower()
            count = service["count"]
            logger.info(f"{service_name}: {count} historical play count records")
