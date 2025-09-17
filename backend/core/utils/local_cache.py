import datetime
import hashlib
import time
import uuid
from enum import Enum
from typing import Any

from core.utils.utils import get_logger
from django.core.cache import caches

logger = get_logger(__name__)

SEVEN_DAYS_TTL = 7 * 24 * 60 * 60
NO_EXPIRATION_TTL = None

LOCAL_CACHE_TTL_MAP = {
    "gql_playlist_metadata": SEVEN_DAYS_TTL,
    "gql_playlist": NO_EXPIRATION_TTL,
}


class CachePrefix(str, Enum):
    GQL_PLAYLIST_METADATA = "gql_playlist_metadata"
    GQL_PLAYLIST = "gql_playlist"


def _generate_cache_key(prefix: CachePrefix, key_data: str) -> str:
    full_key = f"{prefix.value}:{key_data}"
    return hashlib.md5(full_key.encode()).hexdigest()


def _serialize_for_local_cache(data):
    """Simple serialization for local cache storage."""
    # Handle basic GraphQL-ready data structures
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            result[key] = _serialize_for_local_cache(value)
        return result
    elif isinstance(data, list):
        return [_serialize_for_local_cache(item) for item in data]
    elif isinstance(data, (datetime.datetime, datetime.date)):
        return data.isoformat()
    elif isinstance(data, uuid.UUID):
        return str(data)
    else:
        return data


def _deserialize_from_local_cache(data):
    """Simple deserialization for basic data types."""
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # Handle datetime strings
            if isinstance(value, str) and "T" in value and ":" in value:
                try:
                    result[key] = datetime.datetime.fromisoformat(value)
                    continue
                except ValueError:
                    pass
            result[key] = _deserialize_from_local_cache(value)
        return result
    elif isinstance(data, list):
        return [_deserialize_from_local_cache(item) for item in data]
    else:
        return data


def local_cache_get(prefix: CachePrefix, key_data: str) -> Any:
    """Get data from local memory cache."""
    start_time = time.time()
    cache_key = _generate_cache_key(prefix, key_data)

    try:
        local_cache = caches["local"]
        data = local_cache.get(cache_key)
        elapsed = time.time() - start_time

        if data is not None:
            logger.info(f"Cache HIT (local): {prefix.value}:{key_data} ({elapsed:.3f}s)")
            # Return cached data as-is (already GraphQL-ready)
            return _deserialize_from_local_cache(data)
        else:
            logger.info(f"Cache MISS (local): {prefix.value}:{key_data} ({elapsed:.3f}s)")
        return data
    except Exception as e:
        logger.warning(f"Local cache error: {prefix.value}:{key_data}: {e}")
        return None


def local_cache_set(prefix: CachePrefix, key_data: str, value: Any, ttl: int | None = None) -> None:
    """Set data in local memory cache."""
    cache_key = _generate_cache_key(prefix, key_data)

    # Serialize complex objects for storage
    serialized_value = _serialize_for_local_cache(value)

    try:
        local_cache = caches["local"]
        if ttl is None:
            ttl = LOCAL_CACHE_TTL_MAP.get(prefix.value, SEVEN_DAYS_TTL)
        local_cache.set(cache_key, serialized_value, ttl)
        logger.info(f"Cached (local): {prefix.value}:{key_data}")
    except Exception as e:
        logger.warning(f"Failed to cache locally: {prefix.value}:{key_data}: {e}")


def local_cache_clear(prefix: CachePrefix) -> int:
    """Clear local memory cache."""
    try:
        local_cache = caches["local"]
        local_cache.clear()
        logger.info(f"Cleared local cache for {prefix.value}")
        return 1
    except Exception as e:
        logger.warning(f"Failed to clear local cache: {e}")
        return 0


def _execute_cache_warming_queries():
    """Execute GraphQL queries to warm the cache."""
    # Import here to avoid circular imports
    from core.constants import GenreName, ServiceName
    from core.graphql.schema import schema

    # Warm playlist metadata cache
    for genre in GenreName:
        schema.execute(f"""
            query GetPlaylistMetadata {{
                serviceOrder
                playlistsByGenre(genre: "{genre.value}") {{
                    playlistName
                    playlistCoverUrl
                    playlistCoverDescriptionText
                    playlistUrl
                    genreName
                    serviceName
                }}
            }}
        """)

    # Warm playlist tracks cache
    for genre in GenreName:
        for service in [ServiceName.SPOTIFY, ServiceName.APPLE_MUSIC, ServiceName.SOUNDCLOUD, ServiceName.TUNEMELD]:
            schema.execute(f"""
                query GetPlaylistTracks {{
                    playlist(genre: "{genre.value}", service: "{service.value}") {{
                        genreName
                        serviceName
                        tracks {{
                            rank(genre: "{genre.value}", service: "{service.value}")
                            isrc
                            trackName
                            artistName
                            albumName
                            albumCoverUrl
                            youtubeUrl
                            spotifyUrl
                            appleMusicUrl
                            soundcloudUrl
                            youtubeCurrentViewCount
                            spotifyCurrentViewCount
                            spotifySource {{
                                name
                                displayName
                                url
                                iconUrl
                            }}
                            appleMusicSource {{
                                name
                                displayName
                                url
                                iconUrl
                            }}
                            soundcloudSource {{
                                name
                                displayName
                                url
                                iconUrl
                            }}
                            youtubeSource {{
                                name
                                displayName
                                url
                                iconUrl
                            }}
                        }}
                    }}
                }}
            """)


def warm_local_cache_from_postgres() -> int:
    """
    Warm local cache by loading GraphQL data directly from Postgres on startup.

    PURPOSE: Automatically called during Django app startup (apps.py) to pre-populate
    the local cache with frequently accessed GraphQL data. This reduces response times
    for the first requests after server restart.

    USAGE:
    - Automatic: Called on server startup via apps.py
    - Manual: Available for debugging, but prefer management commands for manual use
    """
    start_time = time.time()

    try:
        logger.info("Warming local cache from Postgres...")
        _execute_cache_warming_queries()

        elapsed = time.time() - start_time
        logger.info(f"Warmed local cache from Postgres in {elapsed:.3f}s")

        return 1  # Success indicator

    except Exception as e:
        elapsed = time.time() - start_time
        logger.warning(f"Failed to warm local cache from Postgres ({elapsed:.3f}s): {e}")
        return 0
