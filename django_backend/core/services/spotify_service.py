import os
import re
from functools import lru_cache

from core.utils.cache_utils import CachePrefix, cache_get, cache_set
from core.utils.helpers import get_logger
from spotipy import Spotify
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials
from tenacity import retry, stop_after_attempt, wait_exponential

logger = get_logger(__name__)


@lru_cache(maxsize=4)
def get_cached_spotify_client(client_id: str, client_secret: str) -> Spotify:
    if not client_id or not client_secret:
        raise ValueError("Spotify client ID or client secret not provided.")

    return Spotify(
        client_credentials_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    )


def get_spotify_isrc(
    track_name: str, artist_name: str, client_id: str | None = None, client_secret: str | None = None
) -> str | None:
    client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET")

    key_data = f"{track_name}|{artist_name}"
    isrc = cache_get(CachePrefix.SPOTIFY_ISRC, key_data)
    if isrc:
        return str(isrc)

    logger.info(f"ISRC Spotify Lookup Cache miss for {track_name} by {artist_name}")

    spotify_client = get_cached_spotify_client(client_id, client_secret)
    track_name_no_parens = _clean_track_name(track_name)

    queries = [
        f"track:{track_name_no_parens} artist:{artist_name}",
        f"{track_name_no_parens} {artist_name}",
        f"track:{track_name.lower()} artist:{artist_name}",
    ]

    for query in queries:
        isrc = _search_spotify_for_isrc(spotify_client, query)
        if isrc:
            logger.info(f"Found ISRC for {track_name} by {artist_name}: {isrc}")
            cache_set(CachePrefix.SPOTIFY_ISRC, key_data, isrc)
            return isrc

    logger.info(f"No track found on Spotify for {track_name} by {artist_name}")
    return None


def get_spotify_track_url_by_isrc(isrc: str, client_id: str | None = None, client_secret: str | None = None) -> str:
    client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET")

    spotify_client = get_cached_spotify_client(client_id, client_secret)
    return _get_track_url_by_isrc_with_retry(spotify_client, isrc)


def _clean_track_name(track_name: str) -> str:
    return re.sub(r"\([^()]*\)", "", track_name.lower())


def _search_spotify_for_isrc(spotify_client: Spotify, query: str) -> str | None:
    try:
        results = spotify_client.search(q=query, type="track", limit=1)
        tracks = results["tracks"]["items"]
        if tracks:
            isrc_value = tracks[0]["external_ids"].get("isrc")
            return str(isrc_value) if isrc_value is not None else None
        return None
    except Exception as e:
        logger.info(f"Error searching Spotify with query '{query}': {e}")
        return None


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(5),
    reraise=True,
)
def _get_track_url_by_isrc_with_retry(spotify_client: Spotify, isrc: str) -> str:
    try:
        results = spotify_client.search(q=f"isrc:{isrc}", type="track", limit=1)
        if results["tracks"]["items"]:
            spotify_url = results["tracks"]["items"][0]["external_urls"]["spotify"]
            return str(spotify_url)
        else:
            return ""
    except SpotifyException as e:
        logger.error(f"SpotifyException: {e}")
        raise
