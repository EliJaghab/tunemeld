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

FEATURES:
- Uses Django fixtures for consistent sample data
- Realistic JSON data matching actual API responses
- Complete ETL pipeline test without external API calls
- Safe for staging/development environments
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
        logger.info("🚀 Setting up staging environment...")

        # Step 0: Ensure migrations are applied
        logger.info("🔄 Running database migrations...")
        call_command("migrate", verbosity=0)

        # Step 1: Clear existing data
        logger.info("🧹 Clearing existing data...")
        from core.models import Genre, PlaylistTrack, RawPlaylistData, Service, Track, TrackData

        RawPlaylistData.objects.all().delete()
        PlaylistTrack.objects.all().delete()
        TrackData.objects.all().delete()
        Track.objects.all().delete()
        Genre.objects.all().delete()
        Service.objects.all().delete()

        # Step 2: Load sample data fixtures (includes lookup tables)
        logger.info("📦 Loading staging fixtures...")
        call_command("loaddata", "staging_data.json")

        if not options["skip_etl"]:
            # Step 3: Run normalization on fixture data
            logger.info("🔄 Running playlist normalization...")
            call_command("c_normalize_raw_playlists")

            # Step 4: Run track hydration (with mocked Spotify for staging)
            logger.info("🎵 Running track hydration...")
            call_command("d_hydrate_tracks")

            # Step 5: Show results
            self.show_staging_results()
        else:
            logger.info("⏭️  Skipped ETL pipeline (use --skip-etl=false to run)")

        logger.info("✅ Staging environment setup complete!")
        logger.info("🔗 Database: SQLite staging.db")
        logger.info("📋 Sample data loaded from fixtures")
        logger.info("🧪 Ready for end-to-end testing")

    def show_staging_results(self):
        """Show staging environment statistics."""
        from core.models import PlaylistTrack, RawPlaylistData, Track, TrackData

        logger.info("📈 Staging Environment Results:")
        logger.info(f"   Raw playlist records: {RawPlaylistData.objects.count()}")
        logger.info(f"   Normalized playlist tracks: {PlaylistTrack.objects.count()}")
        logger.info(f"   Unique tracks: {Track.objects.count()}")
        logger.info(f"   Track data entries: {TrackData.objects.count()}")
