import datetime

CURRENT_TIMESTAMP = datetime.now().isoformat()

GENRE_NAMES = ["pop", "dance", "country", "rap"]

SPOTIFY = "Spotify"
APPLE_MUSIC = "AppleMusic"
SOUNDCLOUD = "SoundCloud"
SERVICE_NAMES = [SPOTIFY, APPLE_MUSIC, SOUNDCLOUD]
RANK_PRIORITY = [APPLE_MUSIC, SOUNDCLOUD, SPOTIFY]
AGGREGATE = "Aggregate"

PLAYLIST_ETL_DATABASE = "playlist_etl"
RAW_PLAYLISTS_COLLECTION = "raw_playlists"
TRACK_COLLECTION = "track"
TRACK_PLAYLIST_COLLECTION = "track_playlist"
ISRC_CACHE_COLLECTION = "isrc_cache"
YOUTUBE_CACHE_COLLECTION = "youtube_cache"
APPLE_MUSIC_ALBUM_COVER_CACHE_COLLECTION = "apple_music_album_cover_cache"

# view count vars
SPOTIFY_VIEW_COUNT_XPATH = (
    '(//*[contains(concat(" ", @class, " "), concat(" ", "w1TBi3o5CTM7zW1EB3Bm", " "))])[4]'
)