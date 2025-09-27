import time
from typing import Any

from core.management.commands.genre_service import Command as GenreServiceCommand
from core.management.commands.playlist_etl_modules.b_clear_raw_playlist_cache import Command as ClearCacheCommand
from core.management.commands.playlist_etl_modules.c_raw_playlist import Command as RawPlaylistCommand
from core.management.commands.playlist_etl_modules.d_playlist_service_track import Command as ServiceTrackCommand
from core.management.commands.playlist_etl_modules.e_track import Command as TrackCommand
from core.management.commands.playlist_etl_modules.f_aggregate import Command as AggregateCommand
from core.management.commands.playlist_etl_modules.g_clear_and_warm_track_cache import (
    Command as ClearAndWarmTrackCacheCommand,
)
from core.utils.utils import get_logger
from django.core.management.base import BaseCommand, CommandError

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Run the complete playlist ETL pipeline"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force-refresh",
            action="store_true",
            help="Force refresh by skipping RapidAPI cache and pulling fresh data",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        force_refresh = options.get("force_refresh", False)
        start_time = time.time()

        try:
            logger.info("Starting ETL pipeline...")

            logger.info("Step 1: Setting up genres and services...")
            GenreServiceCommand().handle()

            logger.info("Step 2: Clearing raw playlist cache if within scheduled window...")
            ClearCacheCommand().handle()

            logger.info("Step 3: Extracting raw playlist data...")
            RawPlaylistCommand().handle(force_refresh=force_refresh)

            logger.info("Step 4: Creating service tracks...")
            ServiceTrackCommand().handle()

            logger.info("Step 5: Creating canonical tracks with YouTube URLs...")
            TrackCommand().handle()

            logger.info("Step 6: Aggregating tracks...")
            AggregateCommand().handle()

            logger.info("Step 7: Clearing and warming track cache...")
            ClearAndWarmTrackCacheCommand().handle()

            elapsed_time = time.time() - start_time
            logger.info(f"ETL pipeline completed in {elapsed_time:.2f} seconds")

        except Exception as e:
            logger.error(f"ETL pipeline failed: {e}")
            raise CommandError(f"ETL pipeline failed: {e}") from e
