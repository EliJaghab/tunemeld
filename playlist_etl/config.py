from datetime import datetime

from playlist_etl.models import TrackSourceServiceName

CURRENT_TIMESTAMP = datetime.now()

RANK_PRIORITY = [
    TrackSourceServiceName.APPLE_MUSIC,
    TrackSourceServiceName.SOUNDCLOUD,
    TrackSourceServiceName.SPOTIFY,
]


PLAYLIST_ETL_DATABASE = "playlist_etl"
RAW_PLAYLISTS_COLLECTION = "raw_playlists"
TRACK_COLLECTION = "track"
TRACK_PLAYLIST_COLLECTION = "track_playlist"

# caches
ISRC_CACHE_COLLECTION = "isrc_cache"
YOUTUBE_URL_CACHE_COLLECTION = "youtube_cache"
APPLE_MUSIC_ALBUM_COVER_CACHE_COLLECTION = "apple_music_album_cover_cache"

# view count vars
SPOTIFY_ERROR_THRESHOLD = 5
SPOTIFY_VIEW_COUNT_XPATH = (
    '(//*[contains(concat(" ", @class, " "), concat(" ", "w1TBi3o5CTM7zW1EB3Bm", " "))])[4]'
)
