import time
from typing import Any

from core.management.commands.view_count.a_historical_view_count import Command as HistoricalViewCountCommand
from core.management.commands.view_count.b_delta_view_count import Command as DeltaViewCountCommand
from core.utils.utils import get_logger
from django.core.management.base import BaseCommand

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

            duration = time.time() - start_time
            logger.info(f"View Count ETL Pipeline completed in {duration:.1f} seconds")

        except Exception as e:
            logger.error(f"View Count ETL Pipeline failed: {e}")
            duration = time.time() - start_time
            logger.info(f"Pipeline failed after {duration:.1f} seconds")
            raise
