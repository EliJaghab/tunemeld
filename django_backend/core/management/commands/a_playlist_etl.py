import time
from typing import Any

from core.management.commands.playlist_etl.b_genre_service import Command as GenreServiceCommand
from core.management.commands.playlist_etl.c_clear_raw_playlist_cache import Command as ClearCacheCommand
from core.management.commands.playlist_etl.d_raw_playlist import Command as RawPlaylistCommand
from core.management.commands.playlist_etl.e_playlist_service_track import Command as ServiceTrackCommand
from core.management.commands.playlist_etl.f_track import Command as TrackCommand
from core.management.commands.playlist_etl.g_aggregate import Command as AggregateCommand
from core.management.commands.playlist_etl.h_clear_gql_cache import Command as ClearGqlCacheCommand
from core.management.commands.playlist_etl.i_warm_gql_cache import Command as WarmGqlCacheCommand
from core.utils.utils import get_logger
from django.core.management.base import BaseCommand, CommandError

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Run the complete playlist ETL pipeline"

    def handle(self, *args: Any, **options: Any) -> None:
        start_time = time.time()

        try:
            logger.info("Step 1: Setting up genres and services...")
            GenreServiceCommand().handle()

            logger.info("Step 2: Clearing raw playlist cache if within scheduled window...")
            ClearCacheCommand().handle()

            logger.info("Step 3: Extracting raw playlist data...")
            RawPlaylistCommand().handle()

            logger.info("Step 4: Creating service tracks...")
            ServiceTrackCommand().handle()

            logger.info("Step 5: Creating canonical tracks with YouTube URLs...")
            TrackCommand().handle()

            logger.info("Step 6: Aggregating tracks...")
            AggregateCommand().handle()

            logger.info("Step 7: Clearing GraphQL cache...")
            ClearGqlCacheCommand().handle()

            logger.info("Step 8: Warming GraphQL cache...")
            WarmGqlCacheCommand().handle()

            elapsed_time = time.time() - start_time
            logger.info(f"ETL pipeline completed in {elapsed_time:.2f} seconds")

        except Exception as e:
            logger.error(f"ETL pipeline failed: {e}")
            raise CommandError(f"ETL pipeline failed: {e}") from e
