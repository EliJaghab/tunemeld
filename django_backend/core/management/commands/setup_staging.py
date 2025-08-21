"""
Setup Staging Environment with Sample Data

This command sets up a complete staging environment with realistic sample data
for end-to-end testing without hitting external APIs.

WHAT THIS DOES:
1. Clears existing data
2. Loads fixtures with sample raw playlist data
3. Runs the full ETL pipeline on sample data
4. Provides staging environment ready for testing

USAGE:
    python manage.py setup_staging
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand

from playlist_etl.helpers import get_logger

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Setup staging environment with sample data and run full ETL pipeline"

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-etl",
            action="store_true",
            help="Skip running the ETL pipeline, just load fixtures",
        )

    def handle(self, *args, **options):
        logger.info("Setting up staging environment...")

        # Step 0: Ensure migrations are applied
        logger.info("Running database migrations...")
        call_command("migrate", verbosity=0)

        # Step 1: Clear existing data
        logger.info("Clearing existing data...")
        from core.models import Genre, PlaylistModel, RawPlaylistData, Service, ServiceTrack, Track
        from django.db import connection

        # Check if tables exist before trying to delete
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in cursor.fetchall()}

        if "raw_playlist_data" in existing_tables:
            RawPlaylistData.objects.all().delete()
        if "playlists" in existing_tables:
            PlaylistModel.objects.all().delete()
        if "service_tracks" in existing_tables:
            ServiceTrack.objects.all().delete()
        if "tracks" in existing_tables:
            Track.objects.all().delete()
        if "genres" in existing_tables:
            Genre.objects.all().delete()
        if "services" in existing_tables:
            Service.objects.all().delete()

        # Step 2: Load real API data from files (includes lookup tables)
        logger.info("Loading real API data from files...")
        call_command("load_real_api_data")

        if not options["skip_etl"]:
            # Step 3: Run normalization on fixture data
            logger.info("Running playlist normalization...")
            call_command("c_playlist_service_track")

            # Step 4: Run track hydration (with mocked Spotify for staging)
            logger.info("Running track hydration...")
            call_command("d_track")

            # Step 5: Show results
            self.show_staging_results()
        else:
            logger.info("Skipped ETL pipeline (use --skip-etl=false to run)")

        logger.info("Staging environment setup complete!")
        logger.info("Database: SQLite staging.db")
        logger.info("Real API data loaded from files")
        logger.info("Ready for end-to-end testing")

    def show_staging_results(self):
        """Show staging environment statistics."""
        from core.models import PlaylistModel, RawPlaylistData, ServiceTrack, Track

        logger.info("Staging Environment Results:")
        logger.info(f"   Raw playlist records: {RawPlaylistData.objects.count()}")
        logger.info(f"   Normalized playlist tracks: {ServiceTrack.objects.count()}")
        logger.info(f"   Playlist positions: {PlaylistModel.objects.count()}")
        logger.info(f"   Unique tracks: {Track.objects.count()}")
