"""
Refactored services - function-based approach with LRU caching.

This file replaces the class-based services with simple, cached functions.
Each service is separated into its own function rather than being wrapped in classes.
"""

import os
import re
from functools import lru_cache
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup
from spotipy import Spotify
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials
from tenacity import retry, stop_after_attempt, wait_exponential

from playlist_etl.cache_utils import CachePrefix, cache_get, cache_set
from playlist_etl.config import CURRENT_TIMESTAMP
from playlist_etl.helpers import get_logger
from playlist_etl.models import HistoricalView, Track
from playlist_etl.utils import WebDriverManager, get_delta_view_count

logger = get_logger(__name__)

# =============================================================================
# CACHED CLIENT FACTORIES
# =============================================================================


@lru_cache(maxsize=1)
def get_cached_webdriver() -> WebDriverManager:
    """Get cached WebDriver instance. Reuses same instance across calls."""
    return WebDriverManager()


@lru_cache(maxsize=4)  # Cache different client_id/secret combinations
def get_cached_spotify_client(client_id: str, client_secret: str) -> Spotify:
    """Get cached Spotify client. Avoids recreating OAuth credentials."""
    if not client_id or not client_secret:
        raise ValueError("Spotify client ID or client secret not provided.")

    return Spotify(
        client_credentials_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    )


def cleanup_cached_clients():
    """Cleanup all cached clients and WebDriver."""
    webdriver = get_cached_webdriver()
    webdriver.close_driver()

    # Clear caches
    get_cached_webdriver.cache_clear()
    get_cached_spotify_client.cache_clear()


# =============================================================================
# SPOTIFY FUNCTIONS
# =============================================================================


def get_spotify_isrc(
    track_name: str, artist_name: str, client_id: str | None = None, client_secret: str | None = None
) -> str | None:
    """Get ISRC from Spotify for a track."""
    # Use environment variables if not provided
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
    """Get Spotify track URL using ISRC."""
    client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET")

    spotify_client = get_cached_spotify_client(client_id, client_secret)
    return _get_track_url_by_isrc_with_retry(spotify_client, isrc)


def update_spotify_track_view_count(track: Track) -> bool:
    """Update Spotify view count for a track."""
    if not track.spotify_track_data.track_url:
        return False

    webdriver = get_cached_webdriver()

    # Update start view if needed
    if track.spotify_view.start_view.timestamp is None:
        view_count = _get_spotify_view_count(webdriver, track.spotify_track_data.track_url)
        if view_count is None:
            return False
        track.spotify_view.start_view.view_count = view_count
        track.spotify_view.start_view.timestamp = CURRENT_TIMESTAMP

    # Update current view
    view_count = _get_spotify_view_count(webdriver, track.spotify_track_data.track_url)
    if view_count is None:
        return False

    track.spotify_view.current_view.view_count = view_count
    track.spotify_view.current_view.timestamp = CURRENT_TIMESTAMP

    # Update historical view
    _update_spotify_historical_view(track, view_count)
    return True


# =============================================================================
# YOUTUBE FUNCTIONS
# =============================================================================


def get_youtube_url(track_name: str, artist_name: str, api_key: str | None = None) -> str | None:
    """Get YouTube URL for a track."""
    api_key = api_key or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("YouTube API key not provided.")

    key_data = f"{track_name}|{artist_name}"
    youtube_url = cache_get(CachePrefix.YOUTUBE_URL, key_data)
    if youtube_url:
        return str(youtube_url)

    query = f"{track_name} {artist_name}"
    youtube_search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&key={api_key}"

    response = requests.get(youtube_search_url)
    if response.status_code == 200:
        data = response.json()
        if data.get("items"):
            video_id = data["items"][0]["id"].get("videoId")
            if video_id:
                youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                logger.info(f"Found YouTube URL for {track_name} by {artist_name}: {youtube_url}")
                cache_set(CachePrefix.YOUTUBE_URL, key_data, youtube_url)
                return youtube_url
        logger.info(f"No video found for {track_name} by {artist_name}")
        return None
    else:
        logger.info(f"Error fetching YouTube URL: {response.status_code}, {response.text}")
        if response.status_code == 403 and "quotaExceeded" in response.text:
            raise ValueError(f"Could not get YouTube URL for {track_name} {artist_name} because Quota Exceeded")
        return None


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(3),
    reraise=True,
)
def get_youtube_track_view_count(youtube_url: str, api_key: str | None = None) -> int:
    """Get YouTube track view count."""
    api_key = api_key or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("YouTube API key not provided.")

    video_id = youtube_url.split("v=")[-1]
    youtube_api_url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={video_id}&key={api_key}"

    try:
        response = requests.get(youtube_api_url)
        response.raise_for_status()

        data = response.json()
        if data["items"]:
            view_count = data["items"][0]["statistics"]["viewCount"]
            logger.info(f"Video ID {video_id} has {view_count} views.")
            return int(view_count)
        else:
            logger.error(f"No video found for ID {video_id}")
            return 0

    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        raise ValueError(f"Unexpected error occurred for {youtube_url}: {e}") from e


def update_youtube_track_view_count(track: Track) -> bool:
    """Update YouTube view count for a track."""
    if not track.youtube_url:
        return False

    # Update start view if needed
    if track.youtube_view.start_view.timestamp is None:
        view_count = _get_youtube_view_count(track.youtube_url)
        if view_count is None:
            return False
        track.youtube_view.start_view.view_count = view_count
        track.youtube_view.start_view.timestamp = CURRENT_TIMESTAMP

    # Update current view
    view_count = _get_youtube_view_count(track.youtube_url)
    if view_count is None:
        return False

    track.youtube_view.current_view.view_count = view_count
    track.youtube_view.current_view.timestamp = CURRENT_TIMESTAMP

    # Update historical view
    _update_youtube_historical_view(track, view_count)
    return True


# =============================================================================
# APPLE MUSIC FUNCTIONS
# =============================================================================


def get_apple_music_album_cover_url(track_url: str) -> str | None:
    """Get Apple Music album cover URL."""
    album_cover_url = cache_get(CachePrefix.APPLE_COVER, track_url)
    if album_cover_url:
        return str(album_cover_url)

    logger.info(f"Apple Music Album Cover Cache miss for URL: {track_url}")
    try:
        response = requests.get(track_url, timeout=30)
        response.raise_for_status()
        doc = BeautifulSoup(response.text, "html.parser")

        source_tag = doc.find("source", attrs={"type": "image/jpeg"})
        if not source_tag or not source_tag.has_attr("srcset"):
            raise ValueError("Album cover URL not found")

        srcset = source_tag["srcset"]
        album_cover_url = unquote(srcset.split()[0])
        cache_set(CachePrefix.APPLE_COVER, track_url, album_cover_url)
        return album_cover_url
    except Exception as e:
        logger.info(f"Error fetching album cover URL: {e}")
        return None


# =============================================================================
# HELPER FUNCTIONS (Private)
# =============================================================================


def _clean_track_name(track_name: str) -> str:
    """Remove parenthetical content from track names."""
    return re.sub(r"\([^()]*\)", "", track_name.lower())


def _search_spotify_for_isrc(spotify_client: Spotify, query: str) -> str | None:
    """Search Spotify for ISRC using a query."""
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
    """Get track URL by ISRC with retry logic."""
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


def _get_spotify_view_count(webdriver: WebDriverManager, track_url: str) -> int | None:
    """Get Spotify track view count using WebDriver."""
    try:
        return webdriver.get_spotify_track_view_count(track_url)
    except Exception as e:
        logger.error(f"Error getting Spotify view count for {track_url}: {e}")
        return None


def _get_youtube_view_count(youtube_url: str) -> int | None:
    """Get YouTube view count."""
    try:
        return get_youtube_track_view_count(youtube_url)
    except Exception as e:
        logger.error(f"Error getting Youtube view count for {youtube_url}: {e}")
        return None


def _update_spotify_historical_view(track: Track, current_view_count: int) -> None:
    """Update Spotify historical view data."""
    if current_view_count is None:
        return

    historical_view = HistoricalView()
    historical_view.total_view_count = current_view_count
    delta_view_count = get_delta_view_count(
        track.spotify_view.historical_view,
        current_view_count,
    )
    historical_view.delta_view_count = delta_view_count
    historical_view.timestamp = CURRENT_TIMESTAMP
    track.spotify_view.historical_view.append(historical_view)


def _update_youtube_historical_view(track: Track, current_view_count: int) -> None:
    """Update YouTube historical view data."""
    if current_view_count is None:
        return

    historical_view = HistoricalView()
    historical_view.total_view_count = current_view_count
    delta_view_count = get_delta_view_count(
        track.youtube_view.historical_view,
        current_view_count,
    )
    historical_view.delta_view_count = delta_view_count
    historical_view.timestamp = CURRENT_TIMESTAMP
    track.youtube_view.historical_view.append(historical_view)
