import os
import time
import uuid
from typing import Any

from core.management.commands.genre_service import Command as GenreServiceCommand
from core.management.commands.play_count_modules.a_historical_play_count import Command as HistoricalPlayCountCommand
from core.management.commands.play_count_modules.b_aggregate_play_count import Command as AggregatePlayCountCommand
from core.management.commands.play_count_modules.c_clear_and_warm_play_count_cache import (
    Command as WarmPlayCountCacheCommand,
)
from core.models.genre_service import GenreModel, ServiceModel
from core.models.play_counts import HistoricalTrackPlayCountModel
from core.models.playlist import RankModel
from core.utils.utils import get_logger
from django.core.management.base import BaseCommand
from django.db import models, transaction
from django.utils import timezone

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Run the complete play count ETL pipeline"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, help="Limit tracks to process for testing")

    def handle(self, *args: Any, **options: Any) -> None:
        start_time = time.time()
        limit = options.get("limit")
        etl_run_id = uuid.uuid4()

        try:
            with transaction.atomic():
                logger.info(f"Starting Play Count ETL Pipeline with run ID: {etl_run_id}")

                logger.info("Step 1: Setting up genres and services...")
                GenreServiceCommand().handle(etl_run_id=etl_run_id)

                logger.info("Step 2: Running Historical Play Count extraction")
                historical_command = HistoricalPlayCountCommand()
                historical_command.handle(limit=limit)

                logger.info("Step 3: Computing aggregate play counts with weekly changes")
                aggregate_command = AggregatePlayCountCommand()
                aggregate_command.handle()

                logger.info("Step 4: Clearing and warming play count cache...")
                WarmPlayCountCacheCommand().handle()

                logger.info("Step 5: Removing previous ETL run data...")
                self.remove_previous_etl_run(etl_run_id)

                duration = time.time() - start_time
                logger.info(f"Play Count ETL Pipeline completed in {duration:.1f} seconds")

                self._print_final_summary()

        except Exception as e:
            logger.error(f"Play Count ETL Pipeline failed: {e}")
            duration = time.time() - start_time
            logger.info(f"Pipeline failed after {duration:.1f} seconds")
            raise

    def remove_previous_etl_run(self, current_etl_run_id: uuid.UUID) -> None:
        """Blue Green deployment of data - only wipe genre/service/rank data after full pipeline has run."""
        logger.info(f"Removing previous ETL run genre/service/rank data, keeping run ID: {current_etl_run_id}")

        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

        GenreModel.objects.exclude(etl_run_id=current_etl_run_id).delete()
        ServiceModel.objects.exclude(etl_run_id=current_etl_run_id).delete()
        RankModel.objects.exclude(etl_run_id=current_etl_run_id).delete()

        del os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"]

    def _print_final_summary(self):
        today = timezone.now().date()
        records = HistoricalTrackPlayCountModel.objects.filter(recorded_date=today)
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
