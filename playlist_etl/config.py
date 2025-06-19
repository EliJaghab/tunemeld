import os

# Import centralized configuration
import sys
from datetime import datetime

from playlist_etl.models import TrackSourceServiceName

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

CURRENT_TIMESTAMP = datetime.now()

# Use centralized configuration
RANK_PRIORITY = [
    TrackSourceServiceName.APPLE_MUSIC,
    TrackSourceServiceName.SOUNDCLOUD,
    TrackSourceServiceName.SPOTIFY,
]

# Database configuration - imported from centralized config
# PLAYLIST_ETL_DATABASE, RAW_PLAYLISTS_COLLECTION, etc. are now imported

# Database Configuration
PLAYLIST_ETL_DATABASE = "playlist_etl"

# Database Collections
RAW_PLAYLISTS_COLLECTION = "raw_playlists"
TRACK_COLLECTION = "tracks"
TRACK_PLAYLIST_COLLECTION = "track_playlists"
ISRC_CACHE_COLLECTION = "isrc_cache"
YOUTUBE_URL_CACHE_COLLECTION = "youtube_url_cache"

# Performance configuration
SPOTIFY_VIEW_COUNT_XPATH = "//span[@class='Type__TypeElement-sc-goli3j-0 fZDcWX']"
