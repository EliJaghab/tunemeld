from pydantic import BaseModel

from playlist_etl.config import (
    AGGREGATE,
    APPLE_MUSIC,
    GENRE_NAMES,
    PLAYLIST_ETL_DATABASE,
    RAW_PLAYLISTS_COLLECTION,
    RANK_PRIORITY,
    SERVICE_NAMES,
    SOUNDCLOUD,
    TRACK_COLLECTION,
    TRACK_PLAYLIST_COLLECTION,
    YOUTUBE_CACHE_COLLECTION,
)
from playlist_etl.mongo_db_client import MongoDBClient
from playlist_etl.utils import get_logger

logger = get_logger(__name__)

class TrackServiceViewCount(BaseModel):
    service_name: str
    start_view_count: int
    start_timestamp: str
    current_view_count: int
    current_timestamp: str

class TrackViewCount(BaseModel):
    isrc: str
    spotify_view_count: TrackServiceViewCount
    youtube_view_count: TrackServiceViewCount




    