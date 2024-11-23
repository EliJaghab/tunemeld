from pydantic import BaseModel

from playlist_etl.config import (AGGREGATE, APPLE_MUSIC, GENRE_NAMES,
                                 PLAYLIST_ETL_DATABASE, RANK_PRIORITY,
                                 RAW_PLAYLISTS_COLLECTION, SERVICE_NAMES,
                                 SOUNDCLOUD, SPOTIFY, TRACK_COLLECTION,
                                 TRACK_PLAYLIST_COLLECTION, YOUTUBE,
                                 YOUTUBE_URL_CACHE_COLLECTION)
from playlist_etl.models import Track
from playlist_etl.mongo_db_client import MongoDBClient
from playlist_etl.services import YouTubeService
from playlist_etl.utils import WebDriverManager, get_logger

logger = get_logger(__name__)

class ViewCount:
    def __init__(self,
                 mongo_client: MongoDBClient,
                 web_driver: WebDriverManager,
                 youtube_service: YouTubeService
                 ):
        self.mongo_client = mongo_client
        self.web_driver = web_driver
        self.youtube_service = youtube_service
    
    def update_current_view_counts(self):
        track_collection = self.mongo_client.get_collection(TRACK_COLLECTION)
    
    def _get_current_view_counts
        
    
    def get_service_url(self, service_name: str, isrc: str) -> int:
        if service_name == SPOTIFY:
            return self.web_driver.get_spotify_track_view_count(isrc)
        elif service_name == YOUTUBE:
            return self.youtube_service.get_youtube_track_view_count(isrc)
        else:
            raise ValueError("Unexpected service name")
            
        
        




    