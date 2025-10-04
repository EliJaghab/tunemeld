"""
Direct Redis cache debugging API to test cache connectivity and performance.
"""

import time

from core.constants import GraphQLCacheKey
from core.utils.redis_cache import CachePrefix, redis_cache_get, redis_cache_set
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


@csrf_exempt
@require_http_methods(["GET"])
def test_redis_cache(request):
    """Test Redis cache connectivity and performance."""

    start_time = time.time()

    # Test basic cache operations
    test_key = "redis_debug_test"
    test_data = {
        "timestamp": start_time,
        "test_data": "Redis cache test successful",
        "server_time": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
    }

    # Test cache SET
    set_start = time.time()
    try:
        redis_cache_set(CachePrefix.GQL_PLAYLIST_METADATA, test_key, test_data)
        set_success = True
        set_duration = (time.time() - set_start) * 1000
    except Exception as e:
        set_success = False
        set_duration = 0
        set_error = str(e)

    # Test cache GET
    get_start = time.time()
    try:
        retrieved_data = redis_cache_get(CachePrefix.GQL_PLAYLIST_METADATA, test_key)
        get_success = True
        get_duration = (time.time() - get_start) * 1000
        data_matches = retrieved_data == test_data if retrieved_data else False
    except Exception as e:
        get_success = False
        get_duration = 0
        get_error = str(e)
        retrieved_data = None
        data_matches = False

    # Test the actual cache key used by playlists_by_genre
    playlist_cache_key = GraphQLCacheKey.playlists_by_genre("pop")
    playlist_cache_start = time.time()
    try:
        playlist_cache_data = redis_cache_get(CachePrefix.GQL_PLAYLIST_METADATA, playlist_cache_key)
        playlist_cache_success = True
        playlist_cache_duration = (time.time() - playlist_cache_start) * 1000
        playlist_cache_hit = playlist_cache_data is not None
        playlist_cache_size = len(str(playlist_cache_data)) if playlist_cache_data else 0
    except Exception as e:
        playlist_cache_success = False
        playlist_cache_duration = 0
        playlist_cache_error = str(e)
        playlist_cache_hit = False
        playlist_cache_size = 0
        playlist_cache_data = None

    total_duration = (time.time() - start_time) * 1000

    response_data = {
        "redis_test_results": {
            "overall_success": set_success and get_success,
            "total_duration_ms": round(total_duration, 2),
            "cache_set": {
                "success": set_success,
                "duration_ms": round(set_duration, 2),
                "error": set_error if not set_success else None,
            },
            "cache_get": {
                "success": get_success,
                "duration_ms": round(get_duration, 2),
                "data_matches": data_matches,
                "retrieved_data": retrieved_data,
                "error": get_error if not get_success else None,
            },
            "playlist_cache_check": {
                "cache_key": playlist_cache_key,
                "success": playlist_cache_success,
                "cache_hit": playlist_cache_hit,
                "duration_ms": round(playlist_cache_duration, 2),
                "data_size_bytes": playlist_cache_size,
                "error": playlist_cache_error if not playlist_cache_success else None,
                "has_data": playlist_cache_data is not None,
            },
        },
        "environment_info": {
            "server_time": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "cache_prefix": CachePrefix.GQL_PLAYLIST_METADATA.value,
            "test_performed_at": start_time,
        },
    }

    return JsonResponse(response_data, json_dumps_params={"indent": 2})


@csrf_exempt
@require_http_methods(["GET"])
def check_individual_playlist_cache(request):
    """Check if individual playlist cache keys exist that GetServicePlaylists needs."""

    start_time = time.time()

    # Check the specific cache keys that GetServicePlaylists query needs
    services = ["tunemeld", "spotify", "apple_music", "soundcloud"]
    genre = "pop"

    cache_status = {}

    for service in services:
        cache_key = GraphQLCacheKey.resolve_playlist(genre, service)

        try:
            cache_data = redis_cache_get(CachePrefix.GQL_PLAYLIST, cache_key)
            cache_status[service] = {
                "cache_key": cache_key,
                "has_data": cache_data is not None,
                "data_size": len(str(cache_data)) if cache_data else 0,
                "error": None,
            }
        except Exception as e:
            cache_status[service] = {"cache_key": cache_key, "has_data": False, "data_size": 0, "error": str(e)}

    duration = (time.time() - start_time) * 1000

    response_data = {
        "individual_playlist_cache_check": {
            "genre": genre,
            "services_checked": services,
            "cache_status": cache_status,
            "total_duration_ms": round(duration, 2),
            "summary": {
                "cached_services": [s for s, status in cache_status.items() if status["has_data"]],
                "missing_services": [s for s, status in cache_status.items() if not status["has_data"]],
                "total_cached": sum(1 for status in cache_status.values() if status["has_data"]),
                "total_missing": sum(1 for status in cache_status.values() if not status["has_data"]),
            },
        }
    }

    return JsonResponse(response_data, json_dumps_params={"indent": 2})


@csrf_exempt
@require_http_methods(["POST"])
def clear_playlist_cache(request):
    """Clear the playlist cache for debugging."""

    start_time = time.time()

    # Clear the specific cache key that's causing issues
    playlist_cache_key = GraphQLCacheKey.playlists_by_genre("pop")

    try:
        # Try to get the current data first
        current_data = redis_cache_get(CachePrefix.GQL_PLAYLIST_METADATA, playlist_cache_key)
        had_data = current_data is not None

        # Clear by setting to None or using a delete operation
        redis_cache_set(CachePrefix.GQL_PLAYLIST_METADATA, playlist_cache_key, None)

        # Verify it's cleared
        verification_data = redis_cache_get(CachePrefix.GQL_PLAYLIST_METADATA, playlist_cache_key)
        is_cleared = verification_data is None

        success = True

    except Exception as e:
        success = False
        error = str(e)
        had_data = False
        is_cleared = False

    duration = (time.time() - start_time) * 1000

    response_data = {
        "cache_clear_results": {
            "success": success,
            "cache_key": playlist_cache_key,
            "had_data_before": had_data,
            "is_cleared_after": is_cleared,
            "duration_ms": round(duration, 2),
            "error": error if not success else None,
        },
        "message": "Playlist cache cleared - next request will be a cache miss" if success else "Failed to clear cache",
    }

    return JsonResponse(response_data, json_dumps_params={"indent": 2})
