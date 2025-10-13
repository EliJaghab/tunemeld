import time
from typing import Any

from core.management.commands.audio_features_etl_modules.a_populate_audio_features import (
    Command as AudioFeaturesCommand,
)
from core.models.track import TrackFeatureModel, TrackModel
from core.utils.utils import get_logger
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Run the audio features ETL pipeline"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, help="Limit tracks to process for testing")
        parser.add_argument(
            "--force-refresh", action="store_true", help="Force refresh audio features even if they already exist"
        )

    def handle(self, *args: Any, **options: Any) -> None:
        start_time = time.time()
        limit = options.get("limit")
        force_refresh = options.get("force_refresh", False)

        try:
            logger.info("Starting Audio Features ETL Pipeline")

            logger.info("Step 1: Populating Spotify audio features...")
            audio_features_command = AudioFeaturesCommand()
            audio_features_command.handle(limit=limit, force_refresh=force_refresh)

            connection.close()

            duration = time.time() - start_time
            logger.info(f"Audio Features ETL Pipeline completed in {duration:.1f} seconds")

            self._print_final_summary()

        except Exception as e:
            logger.error(f"Audio Features ETL Pipeline failed: {e}")
            duration = time.time() - start_time
            logger.info(f"Pipeline failed after {duration:.1f} seconds")
            raise CommandError(f"Audio Features ETL Pipeline failed: {e}") from e

    def _print_final_summary(self):
        total_tracks = TrackModel.objects.count()
        tracks_with_spotify = TrackModel.objects.filter(spotify_url__isnull=False).count()
        tracks_with_features = TrackFeatureModel.objects.count()

        logger.info("\nAudio Features ETL Summary:")
        logger.info(f"Total tracks in database: {total_tracks}")
        logger.info(f"Tracks with Spotify URLs: {tracks_with_spotify}")
        logger.info(f"Tracks with audio features: {tracks_with_features}")

        if tracks_with_spotify > 0:
            coverage_percentage = (tracks_with_features / tracks_with_spotify) * 100
            logger.info(f"Audio features coverage: {coverage_percentage:.1f}%")
