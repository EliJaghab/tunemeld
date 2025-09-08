import time
from typing import Any

from core.utils.utils import get_logger
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Run the complete playlist ETL pipeline"

    def add_arguments(self, parser):
        pass

    def handle(self, *args: Any, **options: Any) -> None:
        start_time = time.time()

        try:
            logger.info("Step 1: Setting up genres and services...")
            call_command("b_genre_service")

            logger.info("Step 2: Clearing raw playlist cache if within scheduled window...")
            call_command("c_clear_raw_playlist_cache")

            logger.info("Step 3: Extracting raw playlist data...")
            call_command("d_raw_playlist")

            logger.info("Step 4: Creating service tracks...")
            call_command("e_playlist_service_track")

            logger.info("Step 5: Creating canonical tracks with YouTube URLs...")
            call_command("f_track")

            logger.info("Step 6: Aggregating tracks...")
            call_command("g_aggregate")

            logger.info("Step 7: Clearing GraphQL cache...")
            call_command("h_clear_gql_cache")

            logger.info("Step 8: Warming GraphQL cache...")
            call_command("i_warm_gql_cache")

            elapsed_time = time.time() - start_time
            logger.info(f"ETL pipeline completed in {elapsed_time:.2f} seconds")

        except Exception as e:
            logger.error(f"ETL pipeline failed: {e}")
            raise CommandError(f"ETL pipeline failed: {e}") from e
