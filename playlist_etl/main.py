import os

from playlist_etl.aggregate import Aggregate
from playlist_etl.config import ISRC_CACHE_COLLECTION, YOUTUBE_URL_CACHE_COLLECTION
from playlist_etl.extract import PLAYLIST_GENRES, SERVICE_CONFIGS, RapidAPIClient, run_extraction
from playlist_etl.helpers import set_secrets
from playlist_etl.services import AppleMusicService, SpotifyService, YouTubeService
from playlist_etl.transform_playlist import Transform
from playlist_etl.transform_playlist_metadata import transform_all_spotify_metadata
from playlist_etl.utils import CacheManager, MongoDBClient, WebDriverManager, clear_collection, get_mongo_client
from playlist_etl.view_count import ViewCountTrackProcessor


def transform(
    mongo_client: MongoDBClient,
    spotify_service: SpotifyService,
    youtube_service: YouTubeService,
    apple_music_service: AppleMusicService,
) -> None:
    transform = Transform(mongo_client, spotify_service, youtube_service, apple_music_service)
    transform.transform()


def aggregate(mongo_client: MongoDBClient) -> None:
    aggregate = Aggregate(mongo_client)
    aggregate.aggregate()


def extract() -> None:
    """Run the extract step of the ETL pipeline"""
    client = RapidAPIClient()
    mongo_client = get_mongo_client()

    # Clear the raw_playlists collection before extraction
    clear_collection(mongo_client, "raw_playlists")

    # Extract data from all services and genres
    for service_name, _config in SERVICE_CONFIGS.items():
        for genre in PLAYLIST_GENRES:
            run_extraction(mongo_client, client, service_name, genre)


def update_view_counts(
    mongo_client: MongoDBClient, spotify_service: SpotifyService, youtube_service: YouTubeService
) -> None:
    view_count = ViewCountTrackProcessor(mongo_client, spotify_service, youtube_service)
    view_count.update_view_counts()


def main() -> None:
    set_secrets()
    mongo_client = MongoDBClient()
    webdriver_manager = WebDriverManager()

    try:
        spotify_service = SpotifyService(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            isrc_cache_manager=CacheManager(mongo_client, ISRC_CACHE_COLLECTION),
            webdriver_manager=webdriver_manager,
        )
        youtube_service = YouTubeService(
            api_key=os.getenv("GOOGLE_API_KEY"),
            cache_manager=CacheManager(mongo_client, YOUTUBE_URL_CACHE_COLLECTION),
        )
        apple_music_service = AppleMusicService(CacheManager(mongo_client, YOUTUBE_URL_CACHE_COLLECTION))

        # ETL Pipeline: Extract → Transform → Aggregate → View counts
        extract()
        transform(mongo_client, spotify_service, youtube_service, apple_music_service)
        transform_all_spotify_metadata()
        aggregate(mongo_client)
        update_view_counts(mongo_client, spotify_service, youtube_service)
    finally:
        # Ensure WebDriver is properly closed
        webdriver_manager.close_driver()


if __name__ == "__main__":
    main()
