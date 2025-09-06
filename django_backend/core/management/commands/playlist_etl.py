import time
from typing import Any

from core.utils.utils import get_logger
from django.core.management import call_command
from django.core.management.base import BaseCommand

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Run the complete playlist ETL pipeline"

    def add_arguments(self, parser):
        pass

    def handle(self, *args: Any, **options: Any) -> None:
        start_time = time.time()

        logger.info("Step 1: Setting up genres and services...")
        call_command("a_genre_service")

        logger.info("Step 2: Extracting raw playlist data...")
        call_command("b_raw_playlist")

        logger.info("Step 3: Creating service tracks...")
        call_command("c_playlist_service_track")

        logger.info("Step 4: Creating canonical tracks with YouTube URLs...")
        call_command("d_track")

        logger.info("Step 5: Aggregating tracks...")
        call_command("e_aggregate")

        logger.info("Step 6: Refreshing cache...")
        call_command("f_clear_cache")
        call_command("g_warm_cache")

        elapsed_time = time.time() - start_time
        logger.info(f"ETL pipeline completed in {elapsed_time:.2f} seconds")
