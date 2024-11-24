import os

from playlist_etl.aggregate2 import Aggregate
from playlist_etl.config import ISRC_CACHE_COLLECTION, YOUTUBE_URL_CACHE_COLLECTION
from playlist_etl.helpers import set_secrets
from playlist_etl.services import AppleMusicService, SpotifyService, YouTubeService
from playlist_etl.transform2 import Transform
from playlist_etl.utils import CacheManager, MongoDBClient


class Main:
    def __init__(self):
        set_secrets()
        self.mongo_client = MongoDBClient()
        self.spotify_service = SpotifyService(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            isrc_cache_manager=CacheManager(self.mongo_client, ISRC_CACHE_COLLECTION),
        )
        self.youtube_service = YouTubeService(
            api_key=os.getenv("GOOGLE_API_KEY"),
            cache_manager=CacheManager(self.mongo_client, YOUTUBE_URL_CACHE_COLLECTION),
        )
        self.apple_music_service = AppleMusicService(
            CacheManager(self.mongo_client, YOUTUBE_URL_CACHE_COLLECTION)
        )

    def main(self):
        # self.extract()
        self.transform()
        self.aggregate()

    def transform(self):
        transform = Transform(
            self.mongo_client, self.spotify_service, self.youtube_service, self.apple_music_service
        )
        transform.transform()

    def aggregate(self):
        aggregate = Aggregate(self.mongo_client)
        aggregate.aggregate()


if __name__ == "__main__":
    main = Main()
    main.main()
