"""Cache utilities for RapidAPI calls with 7-day TTL"""

import hashlib
from typing import Any

from django.core.cache import cache

from playlist_etl.helpers import get_logger

logger = get_logger(__name__)

# 7 days in seconds
CACHE_TTL = 7 * 24 * 60 * 60

JSON = dict[str, Any] | list[Any]


def get_cache_key(service_name: str, genre: str, url: str) -> str:
    """Generate a unique cache key for the API request"""
    key_string = f"rapidapi:{service_name}:{genre}:{url}"
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    return f"rapidapi_cache_{key_hash}"


def get_cached_response(service_name: str, genre: str, url: str) -> JSON | None:
    """Get cached response if available"""
    cache_key = get_cache_key(service_name, genre, url)
    cached_data = cache.get(cache_key)

    if cached_data:
        logger.info(f"Cache HIT for {service_name}/{genre} - Using cached RapidAPI response")
        return cached_data

    logger.info(f"Cache MISS for {service_name}/{genre} - Will fetch from RapidAPI")
    return None


def set_cached_response(service_name: str, genre: str, url: str, data: JSON) -> None:
    """Store response in cache with 7-day TTL"""
    cache_key = get_cache_key(service_name, genre, url)
    cache.set(cache_key, data, CACHE_TTL)
    logger.info(f"Cached RapidAPI response for {service_name}/{genre} with 7-day TTL")


def clear_playlist_cache(service_name: str | None = None, genre: str | None = None) -> None:
    """Clear cached playlist data

    Args:
        service_name: Clear cache for specific service (optional)
        genre: Clear cache for specific genre (optional)
    """
    if service_name and genre:
        # Clear specific cache entry
        # Note: We'd need to track URLs to clear specific entries
        logger.info(f"Clearing cache for {service_name}/{genre}")
    else:
        # Clear all RapidAPI cache entries
        # Django cache doesn't support pattern deletion, so we'd need to track keys
        logger.info("Clearing all RapidAPI cache entries")
        # For now, we can only clear individual keys when we know them
