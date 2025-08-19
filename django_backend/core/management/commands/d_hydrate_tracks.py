import concurrent.futures
import os
from typing import Any

from core.models import Track
from django.core.management.base import BaseCommand

from playlist_etl.config import ISRC_CACHE_COLLECTION, YOUTUBE_URL_CACHE_COLLECTION
from playlist_etl.helpers import get_logger
from playlist_etl.mongo_db_client import MongoDBClient
from playlist_etl.services import AppleMusicService, SpotifyService, YouTubeService
from playlist_etl.utils import CacheManager, WebDriverManager

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Hydrate tracks with missing ISRC and YouTube links"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        mongo_client = MongoDBClient()
        self.spotify_service = SpotifyService(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            isrc_cache_manager=CacheManager(mongo_client, ISRC_CACHE_COLLECTION),
            webdriver_manager=WebDriverManager(),
        )
        self.youtube_service = YouTubeService(
            api_key=os.getenv("GOOGLE_API_KEY"),
            cache_manager=CacheManager(mongo_client, YOUTUBE_URL_CACHE_COLLECTION),
        )
        self.apple_music_service = AppleMusicService(
            cache_service=CacheManager(mongo_client, YOUTUBE_URL_CACHE_COLLECTION)
        )

    def handle(self, *args: Any, **options: Any) -> None:
        logger.info("Starting incremental track hydration...")

        tracks = Track.objects.all()
        if not tracks.exists():
            logger.warning("No tracks found to hydrate.")
            return

        logger.info(f"Hydrating {tracks.count()} tracks...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.hydrate_single_track, track) for track in tracks]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error hydrating track: {e}")
        logger.info("Track hydration complete")

    def hydrate_single_track(self, track: Track) -> None:
        if not track.youtube_url:
            track.youtube_url = self.youtube_service.get_youtube_url(track.track_name, track.artist_name)

        if not track.album_cover_url and track.apple_music_url:
            track.album_cover_url = self.apple_music_service.get_album_cover_url(track.apple_music_url)

        track.save()
