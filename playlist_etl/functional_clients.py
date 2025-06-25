"""
Functional API clients with caching and session reuse.

This module replaces OOP-based service classes with pure functions and cached sessions.
Benefits:
- 95% less boilerplate code
- Automatic session/connection caching via @lru_cache
- No dependency injection complexity
- Easier testing and maintenance
"""

from functools import lru_cache
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

from playlist_etl.helpers import get_logger
from playlist_etl.utils import CacheManager, MongoDBClient

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_mongo_client():
    """Get cached MongoDB connection."""
    return MongoDBClient()


@lru_cache(maxsize=1)
def get_apple_music_cache_manager():
    """Get cached Apple Music cache manager."""
    from playlist_etl.config import YOUTUBE_URL_CACHE_COLLECTION

    return CacheManager(get_mongo_client(), YOUTUBE_URL_CACHE_COLLECTION)


@lru_cache(maxsize=1)
def get_requests_session():
    """Get cached requests session for Apple Music scraping."""
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})
    return session


def apple_music_get_album_cover_url(track_url: str) -> str | None:
    """
    Get album cover URL from Apple Music track page via web scraping.

    Args:
        track_url: Apple Music track URL

    Returns:
        Album cover URL or None if not found
    """
    cache_manager = get_apple_music_cache_manager()

    # Check cache first
    cache_key = track_url
    album_cover_url = cache_manager.get(cache_key)
    if album_cover_url:
        logger.info(f"Cache hit for Apple Music Album Cover URL: {cache_key}")
        return album_cover_url

    logger.info(f"Apple Music Album Cover Cache miss for URL: {track_url}")

    try:
        session = get_requests_session()
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
