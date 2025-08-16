"""
Raw playlist data extraction Django management command.
Initializes genre/service lookup tables and extracts playlist data from RapidAPI.

Usage:
    python manage.py b_raw_extract
"""

import os

from core.models import Genre, RawPlaylistData, Service
from core.utils import initialize_lookup_tables
from django.core.management import call_command
from django.core.management.base import BaseCommand

from playlist_etl.constants import PLAYLIST_GENRES, SERVICE_CONFIGS
from playlist_etl.extract import (
    AppleMusicFetcher,
    SoundCloudFetcher,
    SpotifyFetcher,
)
from playlist_etl.helpers import get_logger

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Extract raw playlist data from RapidAPI and save to PostgreSQL"

    def handle(self, *args, **options):
        if os.getenv("STAGING_MODE") == "true":
            call_command("setup_staging")
            return

        initialize_lookup_tables()

        deleted_count = RawPlaylistData.objects.all().delete()[0]
        logger.info(f"Cleared {deleted_count} existing records")

        successful = 0
        failed = 0

        for service_name in SERVICE_CONFIGS:
            for genre in PLAYLIST_GENRES:
                try:
                    self.get_and_save_playlist(service_name, genre)
                    successful += 1
                except Exception as e:
                    logger.error(f"Failed {service_name}/{genre}: {e}")
                    failed += 1

        logger.info(f"Complete: {successful} success, {failed} failed")

    def get_and_save_playlist(self, service_name: str, genre: str) -> RawPlaylistData:
        """Extract playlist data for a specific genre from a specific service."""
        service = Service.objects.get(name=service_name)
        genre_obj = Genre.objects.get(name=genre)

        if service_name == "AppleMusic":
            extractor = AppleMusicFetcher(service_name, genre)
        elif service_name == "SoundCloud":
            extractor = SoundCloudFetcher(service_name, genre)
        elif service_name == "Spotify":
            extractor = SpotifyFetcher(service_name, genre)
        else:
            raise ValueError(f"Unknown service: {service_name}")

        extractor.set_playlist_details()
        playlist_data = extractor.get_playlist()

        raw_data = RawPlaylistData(
            genre=genre_obj,
            service=service,
            playlist_url=extractor.playlist_url,
            playlist_name=extractor.playlist_name,
            playlist_cover_url=getattr(extractor, "playlist_cover_url", ""),
            playlist_cover_description_text=getattr(extractor, "playlist_cover_description_text", ""),
            data=playlist_data,
        )
        raw_data.save()

        if hasattr(extractor, "webdriver_manager"):
            extractor.webdriver_manager.close_driver()

        return raw_data
