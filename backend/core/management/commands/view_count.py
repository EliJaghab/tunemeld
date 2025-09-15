import time
from typing import Any

from core.management.commands.view_count_modules.a_historical_view_count import Command as HistoricalViewCountCommand
from core.management.commands.view_count_modules.b_delta_view_count import Command as DeltaViewCountCommand
from core.management.commands.view_count_modules.c_clear_view_count_cache import Command as ClearViewCountCacheCommand
from core.management.commands.view_count_modules.d_warm_gql_cache import Command as WarmGqlCacheCommand
from core.models.view_counts import HistoricalTrackViewCount
from core.utils.utils import get_logger
from django.core.management.base import BaseCommand
from django.db import models

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Run the complete view count ETL pipeline"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, help="Limit tracks to process for testing")

    def handle(self, *args: Any, **options: Any) -> None:
        start_time = time.time()
        limit = options.get("limit")

        try:
            logger.info("Starting View Count ETL Pipeline")

            logger.info("Step 1: Running Historical View Count extraction")
            historical_command = HistoricalViewCountCommand()
            historical_command.handle(limit=limit)

            logger.info("Step 2: Computing delta view counts")
            delta_command = DeltaViewCountCommand()
            delta_command.handle()

            logger.info("Step 3: Clearing view count GraphQL cache...")
            clear_cache_command = ClearViewCountCacheCommand()
            clear_cache_command.handle()

            logger.info("Step 4: Warming view count GraphQL cache...")
            warm_cache_command = WarmGqlCacheCommand()
            warm_cache_command.handle()

            duration = time.time() - start_time
            logger.info(f"View Count ETL Pipeline completed in {duration:.1f} seconds")

            self._print_final_summary()

        except Exception as e:
            logger.error(f"View Count ETL Pipeline failed: {e}")
            duration = time.time() - start_time
            logger.info(f"Pipeline failed after {duration:.1f} seconds")
            raise

    def _print_final_summary(self):
        from django.utils import timezone

        today = timezone.now().date()
        records = HistoricalTrackViewCount.objects.filter(recorded_date=today)
        total_records = records.count()

        if total_records == 0:
            logger.info("No historical track view count records found for today")
            return

        service_breakdown = records.values("service__name").annotate(count=models.Count("id"))

        logger.info("\nHistorical Track View Count ETL Results:")
        logger.info(f"Historical track view count records: {total_records}")
        logger.info("\nBreakdown by service:")

        for service in service_breakdown:
            service_name = service["service__name"].lower()
            count = service["count"]
            logger.info(f"{service_name}: {count} historical view count records")
