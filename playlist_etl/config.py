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

# Performance configuration - imported from centralized config
# SPOTIFY_ERROR_THRESHOLD, SPOTIFY_VIEW_COUNT_XPATH are now imported
