import os

from playlist_etl.aggregate2 import Aggregate
from playlist_etl.config import ISRC_CACHE_COLLECTION, YOUTUBE_URL_CACHE_COLLECTION
from playlist_etl.helpers import set_secrets
from playlist_etl.services import AppleMusicService, SpotifyService, YouTubeService
from playlist_etl.transform2 import Transform
from playlist_etl.utils import CacheManager, MongoDBClient, WebDriverManager
from playlist_etl.view_count2 import ViewCountTrackProcessor



def transform(self):
    transform = Transform(
        self.mongo_client, self.spotify_service, self.youtube_service, self.apple_music_service
    )
    transform.transform()

def aggregate(mongo_client: MongoDBClient) -> None:
    aggregate = Aggregate(mongo_client)
    aggregate.aggregate()

def update_view_counts(mongo_client: MongoDBClient, spotify_service: SpotifyService, youtube_service: YouTubeService) -> None:
    view_count = ViewCountTrackProcessor(mongo_client, spotify_service, youtube_service)
    view_count.update_view_counts()
        
def main() -> None:
    set_secrets()
    mongo_client = MongoDBClient()
    webdriver_manager = WebDriverManager()
    spotify_service = SpotifyService(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        isrc_cache_manager=CacheManager(mongo_client, ISRC_CACHE_COLLECTION),
        webdriver_manager=webdriver_manager
    )
    youtube_service = YouTubeService(
        api_key=os.getenv("GOOGLE_API_KEY"),
        cache_manager=CacheManager(mongo_client, YOUTUBE_URL_CACHE_COLLECTION),
    )
    apple_music_service = AppleMusicService(
        CacheManager(mongo_client, YOUTUBE_URL_CACHE_COLLECTION)
    )
    
    #transform(mongo_client, spotify_service, youtube_service, apple_music_service)
    #aggregate(mongo_client)
    update_view_counts(mongo_client, spotify_service, youtube_service)
        


if __name__ == "__main__":
    main()