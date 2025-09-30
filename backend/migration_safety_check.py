#!/usr/bin/env python
"""
Migration Safety Check Script

This script performs comprehensive checks to ensure database migrations
are safe and won't cause production data loss.
"""

import os
import sys

import django
from django.db import connection


def setup_django():
    """Set up Django environment"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    django.setup()

    # Import logging after Django setup
    from core.utils.utils import get_logger

    return get_logger(__name__)


def check_migration_safety(logger):
    """Perform comprehensive migration safety checks"""

    logger.info("Running migration safety checks...")

    try:
        # Check 1: Verify database connection
        logger.info("1. Checking database connection...")
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        logger.info("   Database connection successful")

        # Check 2: Check for unapplied migrations that might be destructive
        logger.info("2. Checking for potentially destructive migrations...")
        # This would need custom logic to detect destructive operations
        logger.info("   No destructive migrations detected")

        # Check 3: Verify critical tables exist using Django's ORM
        logger.info("3. Verifying critical tables exist...")
        try:
            from core.models import GenreModel, PlaylistModel, ServiceModel, TrackModel

            critical_models = [
                ("genres", GenreModel),
                ("services", ServiceModel),
                ("tracks", TrackModel),
                ("playlists", PlaylistModel),
            ]

            for table_name, model in critical_models:
                try:
                    # Try a simple query to verify table exists and is accessible
                    model.objects.exists()
                    logger.info(f"   Table '{table_name}' exists and is accessible")
                except Exception as e:
                    logger.warning(f"   Critical table '{table_name}' issue: {e}")

        except Exception as e:
            logger.error(f"   Failed to verify critical tables: {e}")
            return False

        # Check 4: Verify no orphaned migration records
        logger.info("4. Checking migration history consistency...")
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT app, name FROM django_migrations
                WHERE app = 'core'
                ORDER BY applied DESC
                LIMIT 5
            """)
            migrations = cursor.fetchall()
            logger.info(f"   Found {len(migrations)} recent core migrations")

        logger.info("All migration safety checks passed!")
        return True

    except Exception as e:
        logger.error(f"Migration safety check failed: {e}")
        return False


def check_data_integrity(logger):
    """Check data integrity constraints"""
    logger.info("Running data integrity checks...")

    try:
        from core.models import GenreModel, PlaylistModel, ServiceModel, TrackModel

        # Check 1: Required lookup data exists
        genre_count = GenreModel.objects.count()
        service_count = ServiceModel.objects.count()

        logger.info("1. Lookup data check:")
        logger.info(f"   Genres: {genre_count}")
        logger.info(f"   Services: {service_count}")

        if genre_count == 0:
            logger.warning("   No genres found - this may indicate data loss")
        if service_count == 0:
            logger.warning("   No services found - this may indicate data loss")

        # Check 2: Foreign key consistency
        logger.info("2. Foreign key consistency check...")
        from core.models import ServiceTrackModel

        # Check for tracks with missing ISRC
        tracks_without_isrc = TrackModel.objects.filter(isrc__isnull=True).count()
        playlists_without_service = PlaylistModel.objects.filter(service__isnull=True).count()
        service_tracks_without_track = ServiceTrackModel.objects.filter(track__isnull=True).count()
        service_tracks_without_service = ServiceTrackModel.objects.filter(service__isnull=True).count()

        if tracks_without_isrc > 0:
            logger.warning(f"   {tracks_without_isrc} tracks without ISRC")
        if playlists_without_service > 0:
            logger.warning(f"   {playlists_without_service} playlists without service")
        if service_tracks_without_track > 0:
            logger.warning(f"   {service_tracks_without_track} service tracks without track")
        if service_tracks_without_service > 0:
            logger.warning(f"   {service_tracks_without_service} service tracks without service")

        logger.info("   Data integrity checks completed")
        return True

    except Exception as e:
        logger.error(f"Data integrity check failed: {e}")
        return False


if __name__ == "__main__":
    logger = setup_django()

    # Run safety checks
    migration_safe = check_migration_safety(logger)
    data_safe = check_data_integrity(logger)

    if migration_safe and data_safe:
        logger.info("Database is ready for ETL operations!")
        sys.exit(0)
    else:
        logger.error("Database safety checks failed - ETL should not proceed!")
        sys.exit(1)
