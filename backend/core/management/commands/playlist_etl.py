import time
import uuid
from typing import Any

from core.management.commands.playlist_etl_modules.a_genre_service import Command as GenreServiceCommand
from core.management.commands.playlist_etl_modules.b_clear_raw_playlist_cache import Command as ClearCacheCommand
from core.management.commands.playlist_etl_modules.c_raw_playlist import Command as RawPlaylistCommand
from core.management.commands.playlist_etl_modules.d_playlist_service_track import Command as ServiceTrackCommand
from core.management.commands.playlist_etl_modules.e_track import Command as TrackCommand
from core.management.commands.playlist_etl_modules.f_aggregate import Command as AggregateCommand
from core.management.commands.playlist_etl_modules.g_clear_playlist_cache import Command as ClearPlaylistCacheCommand
from core.management.commands.playlist_etl_modules.h_warm_gql_cache import Command as WarmGqlCacheCommand
from core.models import PlaylistModel as Playlist
from core.models import RawPlaylistData, ServiceTrack, Track
from core.utils.utils import get_logger
from django.core.management.base import BaseCommand, CommandError

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Run the complete playlist ETL pipeline"

    def handle(self, *args: Any, **options: Any) -> None:
        start_time = time.time()
        etl_run_id = uuid.uuid4()

        try:
            logger.info(f"Starting ETL pipeline with run ID: {etl_run_id}")

            logger.info("Step 1: Setting up genres and services...")
            GenreServiceCommand().handle()

            logger.info("Step 2: Clearing raw playlist cache if within scheduled window...")
            ClearCacheCommand().handle()

            logger.info("Step 3: Extracting raw playlist data...")
            RawPlaylistCommand().handle(etl_run_id=etl_run_id)

            logger.info("Step 4: Creating service tracks...")
            ServiceTrackCommand().handle(etl_run_id=etl_run_id)

            logger.info("Step 5: Creating canonical tracks with YouTube URLs...")
            TrackCommand().handle(etl_run_id=etl_run_id)

            logger.info("Step 6: Aggregating tracks...")
            AggregateCommand().handle(etl_run_id=etl_run_id)

            logger.info("Step 7: Clearing playlist GraphQL cache...")
            ClearPlaylistCacheCommand().handle()

            logger.info("Step 8: Warming GraphQL cache...")
            WarmGqlCacheCommand().handle()

            logger.info("Step 9: Removing previous ETL run data...")
            self.remove_previous_etl_run(etl_run_id)

            elapsed_time = time.time() - start_time
            logger.info(f"ETL pipeline completed in {elapsed_time:.2f} seconds")

        except Exception as e:
            logger.error(f"ETL pipeline failed: {e}")
            raise CommandError(f"ETL pipeline failed: {e}") from e

    def remove_previous_etl_run(self, current_etl_run_id: uuid.UUID) -> None:
        """Blue Green deployment of data - only wipe prod data after full pipeline has run."""
        logger.info(f"Removing previous ETL run data, keeping run ID: {current_etl_run_id}")
        RawPlaylistData.objects.exclude(etl_run_id=current_etl_run_id).delete()
        ServiceTrack.objects.exclude(etl_run_id=current_etl_run_id).delete()
        Playlist.objects.exclude(etl_run_id=current_etl_run_id).delete()
        Track.objects.exclude(etl_run_id=current_etl_run_id).delete()
