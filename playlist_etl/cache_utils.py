import hashlib
from enum import Enum
from typing import Any

from core.utils.utils import get_logger
from django.core.cache import cache


class CachePrefix(str, Enum):
    """Strongly typed cache prefixes for different data types"""

    RAPIDAPI = "rapidapi"
    YOUTUBE_URL = "youtube_url"
    SPOTIFY_ISRC = "spotify_isrc"
    APPLE_COVER = "apple_cover"


logger = get_logger(__name__)

SEVEN_DAYS_TTL = 7 * 24 * 60 * 60
NO_EXPIRATION_TTL = None

CACHE_TTL_MAP = {
    CachePrefix.RAPIDAPI: SEVEN_DAYS_TTL,
    CachePrefix.YOUTUBE_URL: NO_EXPIRATION_TTL,
    CachePrefix.SPOTIFY_ISRC: NO_EXPIRATION_TTL,
    CachePrefix.APPLE_COVER: NO_EXPIRATION_TTL,
}


def _generate_cache_key(prefix: CachePrefix, key_data: str) -> str:
    full_key = f"{prefix.value}:{key_data}"
    return hashlib.md5(full_key.encode()).hexdigest()


def cache_get(prefix: CachePrefix, key_data: str) -> Any:
    cache_key = _generate_cache_key(prefix, key_data)
    cached_data = cache.get(cache_key)

    if cached_data:
        logger.info(f"Cache HIT: {prefix.value}:{key_data}")
        return cached_data

    logger.info(f"Cache MISS: {prefix.value}:{key_data}")
    return None


def cache_set(prefix: CachePrefix, key_data: str, value: Any, ttl: int | None = None) -> None:
    if ttl is None:
        ttl = CACHE_TTL_MAP.get(prefix, NO_EXPIRATION_TTL)

    cache_key = _generate_cache_key(prefix, key_data)

    if ttl is None:
        cache.set(cache_key, value)
        logger.info(f"Cached: {prefix.value}:{key_data} (TTL: no expiration)")
    else:
        cache.set(cache_key, value, ttl)
        logger.info(f"Cached: {prefix.value}:{key_data} (TTL: {ttl}s)")
