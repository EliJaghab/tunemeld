import os

from core.constants import GraphQLCacheKey
from core.utils.redis_cache import CachePrefix, redis_cache_get
from django.core.cache import caches
from django.http import JsonResponse


def debug_cache_keys(request):
    """Debug endpoint to inspect Redis cache keys and values."""

    genres = ["pop", "dance", "rap", "country"]
    debug_info = {
        "redis_url": os.getenv("REDIS_URL", "NOT_SET"),
        "cache_status": {},
        "genres_tested": genres,
        "timestamp": request.GET.get("t", "no_timestamp"),
    }

    # Check Redis connection
    try:
        caches["redis"]
        debug_info["redis_connection"] = "CONNECTED"
    except Exception as e:
        debug_info["redis_connection"] = f"ERROR: {e!s}"
        return JsonResponse(debug_info)

    # Check cache keys for each genre
    for genre in genres:
        cache_key = GraphQLCacheKey.playlists_by_genre(genre)
        cache_value = redis_cache_get(CachePrefix.GQL_PLAYLIST_METADATA, cache_key)

        debug_info["cache_status"][genre] = {
            "cache_key": cache_key,
            "full_redis_key": f"{CachePrefix.GQL_PLAYLIST_METADATA}:{cache_key}",
            "has_cached_value": cache_value is not None,
            "cache_value_type": type(cache_value).__name__ if cache_value else None,
            "cache_value_length": len(cache_value) if isinstance(cache_value, (list, dict, str)) else None,
        }

    # Try to get all keys with the pattern
    try:
        import redis

        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            r = redis.from_url(redis_url)
            all_keys = r.keys(f"{CachePrefix.GQL_PLAYLIST_METADATA}:*")
            debug_info["existing_cache_keys"] = [key.decode() for key in all_keys]
        else:
            debug_info["existing_cache_keys"] = "REDIS_URL_NOT_SET"
    except Exception as e:
        debug_info["existing_cache_keys"] = f"ERROR: {e!s}"

    return JsonResponse(debug_info, json_dumps_params={"indent": 2})
