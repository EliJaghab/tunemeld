import hashlib
import json
import time
from enum import Enum
from typing import Any

from core.utils.utils import get_logger
from django.core.cache import caches

logger = get_logger(__name__)

# Default TTL values
SEVEN_DAYS_TTL = 7 * 24 * 60 * 60
NO_EXPIRATION_TTL = None


class CachePrefix(str, Enum):
    """Redis cache key prefixes for different data types."""

    GQL_PLAYLIST_METADATA = "gql_playlist_metadata"
    GQL_PLAYLIST = "gql_playlist"
    GQL_PLAY_COUNT = "gql_play_count"
    GQL_GENRES = "gql_genres"
    GQL_SERVICE_CONFIGS = "gql_service_configs"
    GQL_IFRAME_CONFIGS = "gql_iframe_configs"
    GQL_IFRAME_URL = "gql_iframe_url"
    GQL_BUTTON_LABELS = "gql_button_labels"
    GQL_TRACK = "gql_track"
    TRENDING_ISRCS = "trending_isrcs"


def _generate_cache_key(prefix: CachePrefix, key_data: str) -> str:
    """Generate deterministic Redis key while preserving the prefix for clears."""
    full_key = f"{prefix.value}:{key_data}"
    hashed_suffix = hashlib.md5(full_key.encode()).hexdigest()
    return f"{prefix.value}:{hashed_suffix}"


def redis_cache_get(prefix: CachePrefix, key_data: str) -> Any:
    """Get JSON data from Redis cache. Returns parsed data or None if not found."""

    start_time = time.time()
    cache_key = _generate_cache_key(prefix, key_data)

    try:
        redis_cache = caches["redis"]
        json_data = redis_cache.get(cache_key)
        elapsed = time.time() - start_time

        if json_data is not None:
            logger.info(f"Cache HIT (redis): {prefix.value}:{key_data} ({elapsed:.3f}s)")
            # Parse JSON string back to Python dict
            return json.loads(json_data) if isinstance(json_data, str) else json_data
        else:
            logger.info(f"Cache MISS (redis): {prefix.value}:{key_data} ({elapsed:.3f}s)")
            return None
    except Exception as e:
        logger.warning(f"Redis cache error: {prefix.value}:{key_data}: {e}")
        return None


def redis_cache_set(prefix: CachePrefix, key_data: str, value: Any, ttl: int | None = None) -> None:
    """Store JSON-serializable data in Redis cache."""

    cache_key = _generate_cache_key(prefix, key_data)

    try:
        redis_cache = caches["redis"]
        # Serialize to JSON string
        json_value = json.dumps(value, default=str)  # default=str handles datetime/UUID objects

        if ttl is None:
            ttl = SEVEN_DAYS_TTL  # Default TTL

        redis_cache.set(cache_key, json_value, ttl)
        logger.info(f"Cached (redis): {prefix.value}:{key_data} (TTL: {ttl}s)")
    except Exception as e:
        logger.warning(f"Failed to cache in Redis: {prefix.value}:{key_data}: {e}")


def redis_cache_clear(prefix: CachePrefix) -> int:
    """Clear Redis cache entries for the provided prefix only."""

    pattern = f"{prefix.value}:*"

    try:
        redis_cache = caches["redis"]
        delete_pattern = getattr(redis_cache, "delete_pattern", None)
        if callable(delete_pattern):
            deleted = delete_pattern(pattern)
            cleared = deleted if isinstance(deleted, int) else 0
        else:
            redis_cache.clear()
            cleared = 0
        logger.info(f"Cleared {cleared} Redis cache entries for {prefix.value}")
        return cleared
    except Exception as e:
        logger.warning(f"Failed to clear Redis cache: {e}")
        return 0
