import os

from playlist_etl.config import ISRC_CACHE_COLLECTION, YOUTUBE_URL_CACHE_COLLECTION
from playlist_etl.helpers import set_secrets
from playlist_etl.main import update_view_counts
from playlist_etl.services import SpotifyService, YouTubeService
from playlist_etl.utils import CacheManager, MongoDBClient, WebDriverManager

if __name__ == "__main__":
    set_secrets()
    mongo_client = MongoDBClient()
    webdriver_manager = WebDriverManager()

    try:
        spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
        spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        google_api_key = os.getenv("GOOGLE_API_KEY")

        if not spotify_client_id:
            raise ValueError("SPOTIFY_CLIENT_ID environment variable is required")
        if not spotify_client_secret:
            raise ValueError("SPOTIFY_CLIENT_SECRET environment variable is required")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")

        spotify_service = SpotifyService(
            client_id=spotify_client_id,
            client_secret=spotify_client_secret,
            isrc_cache_manager=CacheManager(mongo_client, ISRC_CACHE_COLLECTION),
            webdriver_manager=webdriver_manager,
        )
        youtube_service = YouTubeService(
            api_key=google_api_key,
            cache_manager=CacheManager(mongo_client, YOUTUBE_URL_CACHE_COLLECTION),
        )

        update_view_counts(mongo_client, spotify_service, youtube_service)
    finally:
        webdriver_manager.close_driver()
