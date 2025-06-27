"""
Apple Music API client with functional approach and dependency injection.

This module provides Apple Music API operations using pure functions with proper
dependency injection for testing, replacing the OOP-based AppleMusicService class.

Benefits:
- 95% less boilerplate code
- Proper dependency injection for testing
- No global state issues
- Easy mocking and testing
"""

from functools import lru_cache
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

from playlist_etl.helpers import get_logger
from playlist_etl.utils import CacheManager, MongoDBClient

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def _get_default_mongo_client():
    """Get default MongoDB connection. Cached to avoid multiple connections."""
    return MongoDBClient()


@lru_cache(maxsize=1)
def _get_default_cache_manager():
    """Get default cache manager. Cached to avoid multiple instances."""
    from playlist_etl.config import YOUTUBE_URL_CACHE_COLLECTION

    return CacheManager(_get_default_mongo_client(), YOUTUBE_URL_CACHE_COLLECTION)


@lru_cache(maxsize=1)
def _get_default_requests_session():
    """Get default requests session. Cached to avoid multiple instances."""
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})
    return session


def apple_music_get_album_cover_url(track_url: str, cache_manager=None, session=None) -> str | None:
    """
    Get album cover URL from Apple Music track page via web scraping.

    Args:
        track_url: Apple Music track URL
        cache_manager: Optional cache manager for dependency injection
        session: Optional requests session for dependency injection

    Returns:
        Album cover URL or None if not found
    """
    # Use injected dependencies or get defaults
    if cache_manager is None:
        cache_manager = _get_default_cache_manager()
    if session is None:
        session = _get_default_requests_session()

    # Check cache first
    cache_key = track_url
    album_cover_url = cache_manager.get(cache_key)
    if album_cover_url:
        logger.info(f"Cache hit for Apple Music Album Cover URL: {cache_key}")
        return album_cover_url

    logger.info(f"Apple Music Album Cover Cache miss for URL: {track_url}")

    try:
        response = session.get(track_url, timeout=30)
        response.raise_for_status()

        doc = BeautifulSoup(response.text, "html.parser")
        source_tag = doc.find("source", attrs={"type": "image/jpeg"})

        if not source_tag or not source_tag.has_attr("srcset"):
            raise ValueError("Album cover URL not found")

        srcset = source_tag["srcset"]
        album_cover_url = unquote(srcset.split()[0])

        # Cache the result
        cache_manager.set(cache_key, album_cover_url)
        return album_cover_url

    except Exception as e:
        logger.info(f"Error fetching album cover URL: {e}")
        return None


def clear_cache():
    """Clear all cached instances. Useful for testing."""
    _get_default_mongo_client.cache_clear()
    _get_default_cache_manager.cache_clear()
    _get_default_requests_session.cache_clear()
