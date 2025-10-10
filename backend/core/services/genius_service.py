import os

from core.utils.cloudflare_cache import CachePrefix, cloudflare_cache_get, cloudflare_cache_set
from core.utils.utils import get_logger
from django.conf import settings

if settings.ETL_DEPENDENCIES_AVAILABLE:
    from lyricsgenius import Genius
else:
    Genius = None  # type: ignore

logger = get_logger(__name__)


def get_genius_url(track_name: str, artist_name: str, api_key: str | None = None) -> str | None:
    """Get Genius lyrics page URL for a track."""
    if not settings.ETL_DEPENDENCIES_AVAILABLE:
        logger.warning("Genius URL lookup disabled - ETL dependencies not available")
        return None

    api_key = api_key or os.getenv("GENIUS_ACCESS_TOKEN")
    if not api_key:
        logger.warning("Genius API token not provided")
        return None

    key_data = f"{track_name}|{artist_name}"
    cached_url = cloudflare_cache_get(CachePrefix.GENIUS_URL, key_data)
    if cached_url:
        logger.info(f"Genius URL for {track_name} by {artist_name} retrieved from cache")
        return str(cached_url)

    try:
        genius = Genius(api_key)  # type: ignore
        genius.verbose = False

        song = genius.search_song(track_name, artist_name)  # type: ignore

        if song:
            genius_url = song.url
            cloudflare_cache_set(CachePrefix.GENIUS_URL, key_data, genius_url)
            logger.info(f"Found Genius URL for {track_name} by {artist_name}: {genius_url}")
            return genius_url
        else:
            logger.info(f"No Genius page found for {track_name} by {artist_name}")
            return None

    except Exception as e:
        logger.error(f"Error fetching Genius URL for {track_name} by {artist_name}: {e}")
        return None


def get_genius_lyrics(genius_url: str, api_key: str | None = None) -> str | None:
    """Get lyrics text from a Genius URL."""
    if not settings.ETL_DEPENDENCIES_AVAILABLE:
        logger.warning("Genius lyrics disabled - ETL dependencies not available")
        return None

    api_key = api_key or os.getenv("GENIUS_ACCESS_TOKEN")
    if not api_key:
        logger.warning("Genius API token not provided")
        return None

    cached_lyrics = cloudflare_cache_get(CachePrefix.GENIUS_LYRICS, genius_url)
    if cached_lyrics:
        logger.info(f"Genius lyrics for {genius_url} retrieved from cache")
        return str(cached_lyrics)

    try:
        genius = Genius(api_key)  # type: ignore
        genius.verbose = False
        genius.remove_section_headers = True

        song_id = genius_url.split("/")[-1].split("-")[-1]
        song = genius.song(song_id)  # type: ignore

        if song and "lyrics" in song:
            lyrics_text = song["lyrics"]
            cloudflare_cache_set(CachePrefix.GENIUS_LYRICS, genius_url, lyrics_text)
            logger.info(f"Retrieved lyrics from Genius URL: {genius_url}")
            return lyrics_text
        else:
            logger.info(f"No lyrics found at Genius URL: {genius_url}")
            return None

    except Exception as e:
        logger.error(f"Error fetching lyrics from {genius_url}: {e}")
        return None
