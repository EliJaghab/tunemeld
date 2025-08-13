"""
Raw playlist data extraction Django management command.
Initializes genre/service lookup tables and extracts playlist data from RapidAPI.

Usage:
    python manage.py raw_extract
"""

from core.models import Genre, RawPlaylistData, Service
from core.utils import initialize_lookup_tables
from django.core.management.base import BaseCommand

from playlist_etl.constants import PLAYLIST_GENRES, SERVICE_CONFIGS
from playlist_etl.extract import (
    AppleMusicFetcher,
    RapidAPIClient,
    SoundCloudFetcher,
    SpotifyFetcher,
)
from playlist_etl.helpers import get_logger

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Extract raw playlist data from RapidAPI and save to PostgreSQL"

    def handle(self, *args, **options):
        initialize_lookup_tables()
        logger.info("Lookup tables initialized")

        deleted_count = RawPlaylistData.objects.all().delete()[0]
        logger.info(f"Cleared {deleted_count} existing records")

        client = RapidAPIClient()
        successful = 0
        failed = 0

        for service_name in SERVICE_CONFIGS:
            for genre in PLAYLIST_GENRES:
                try:
                    raw_data = self.extract_playlist(client, service_name, genre)
                    successful += 1
                    track_count = len(raw_data.data.get("tracks", []))
                    logger.info(f"{service_name}/{genre}: {track_count} tracks extracted")
                except Exception as e:
                    logger.error(f"Failed {service_name}/{genre}: {e}")
                    failed += 1

        logger.info(f"Complete: {successful} success, {failed} failed")

    def get_extractor(self, client: RapidAPIClient, service_name: str, genre: str):
        if service_name == "AppleMusic":
            return AppleMusicFetcher(client, service_name, genre)
        elif service_name == "SoundCloud":
            return SoundCloudFetcher(client, service_name, genre)
        elif service_name == "Spotify":
            return SpotifyFetcher(client, service_name, genre)
        else:
            raise ValueError(f"Unknown service: {service_name}")

    def extract_playlist(self, client: RapidAPIClient, service_name: str, genre: str) -> RawPlaylistData:
        """Extract playlist data for a specific genre from a specific service."""
        service = Service.objects.get(name=service_name)
        genre_obj = Genre.objects.get(name=genre)

        extractor = self.get_extractor(client, service_name, genre)
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
