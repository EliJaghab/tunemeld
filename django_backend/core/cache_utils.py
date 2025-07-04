import json
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

from django.core.cache import cache
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class CacheManager:
    """Centralized cache management for TuneMeld application"""

    # Cache key prefixes for different data types
    GRAPH_DATA_PREFIX = "graph_data"
    PLAYLIST_DATA_PREFIX = "playlist_data"
    SERVICE_PLAYLIST_PREFIX = "service_playlist"
    LAST_UPDATED_PREFIX = "last_updated"
    HEADER_ART_PREFIX = "header_art"

    # Cache timeouts (in seconds)
    GRAPH_DATA_TIMEOUT = 3600  # 1 hour
    PLAYLIST_DATA_TIMEOUT = 1800  # 30 minutes
    SERVICE_PLAYLIST_TIMEOUT = 900  # 15 minutes
    LAST_UPDATED_TIMEOUT = 300  # 5 minutes
    HEADER_ART_TIMEOUT = 7200  # 2 hours

    @staticmethod
    def get_cache_key(prefix: str, *args) -> str:
        """Generate a cache key with prefix and arguments"""
        key_parts = [prefix] + [str(arg) for arg in args]
        return ":".join(key_parts)

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Get value from cache with error handling"""
        try:
            return cache.get(key, default)
        except Exception as e:
            logger.warning(f"Cache get failed for key '{key}': {e}")
            return default

    @staticmethod
    def set(key: str, value: Any, timeout: int | None = None) -> bool:
        """Set value in cache with error handling"""
        try:
            cache.set(key, value, timeout)
            logger.debug(f"Cache set successful for key '{key}'")
            return True
        except Exception as e:
            logger.warning(f"Cache set failed for key '{key}': {e}")
            return False

    @staticmethod
    def delete(key: str) -> bool:
        """Delete value from cache with error handling"""
        try:
            cache.delete(key)
            logger.debug(f"Cache delete successful for key '{key}'")
            return True
        except Exception as e:
            logger.warning(f"Cache delete failed for key '{key}': {e}")
            return False

    @staticmethod
    def clear_pattern(pattern: str) -> bool:
        """Clear cache keys matching a pattern"""
        try:
            cache.delete_pattern(pattern)
            logger.debug(f"Cache clear pattern successful for pattern '{pattern}'")
            return True
        except Exception as e:
            logger.warning(f"Cache clear pattern failed for pattern '{pattern}': {e}")
            return False

    @staticmethod
    def get_or_set(key: str, callable_or_value: Callable | Any, timeout: int | None = None) -> Any:
        """Get value from cache or set it if not found"""
        try:
            return cache.get_or_set(key, callable_or_value, timeout)
        except Exception as e:
            logger.warning(f"Cache get_or_set failed for key '{key}': {e}")
            # If cache fails, execute the callable directly if it's a function
            if callable(callable_or_value):
                return callable_or_value()
            return callable_or_value

    @classmethod
    def invalidate_genre_cache(cls, genre: str) -> None:
        """Invalidate all cache entries for a specific genre"""
        patterns = [
            f"{cls.GRAPH_DATA_PREFIX}:{genre}",
            f"{cls.PLAYLIST_DATA_PREFIX}:{genre}",
            f"{cls.SERVICE_PLAYLIST_PREFIX}:{genre}:*",
            f"{cls.LAST_UPDATED_PREFIX}:{genre}",
            f"{cls.HEADER_ART_PREFIX}:{genre}",
        ]

        for pattern in patterns:
            cls.clear_pattern(pattern)

        logger.info(f"Invalidated all cache entries for genre '{genre}'")

    @classmethod
    def get_cache_status(cls) -> dict:
        """Get cache connection status and basic info"""
        try:
            # Test cache connection
            test_key = "cache_status_test"
            cache.set(test_key, "test_value", 1)
            test_result = cache.get(test_key)
            cache.delete(test_key)

            return {
                "connected": test_result == "test_value",
                "backend": cache._cache.__class__.__name__,
                "location": getattr(cache._cache, "_server", "unknown"),
            }
        except Exception as e:
            logger.error(f"Cache status check failed: {e}")
            return {
                "connected": False,
                "error": str(e),
                "backend": "unknown",
                "location": "unknown",
            }


def cache_response(timeout: int | None = None, key_prefix: str = "view"):
    """
    Decorator to cache Django view responses

    Args:
        timeout: Cache timeout in seconds (None for default)
        key_prefix: Prefix for cache key generation
    """

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Generate cache key from view name and arguments
            cache_key = CacheManager.get_cache_key(key_prefix, view_func.__name__, request.path, *args)

            # Try to get cached response
            cached_response = CacheManager.get(cache_key)
            if cached_response is not None:
                logger.debug(f"Cache hit for key '{cache_key}'")
                return cached_response

            # Execute view function
            response = view_func(request, *args, **kwargs)

            # Cache the response if it's successful
            if hasattr(response, "status_code") and response.status_code == 200:
                CacheManager.set(cache_key, response, timeout)
                logger.debug(f"Cached response for key '{cache_key}'")

            return response

        return wrapper

    return decorator


def cache_json_response(timeout: int | None = None, key_prefix: str = "json"):
    """
    Decorator to cache JSON responses from Django views

    Args:
        timeout: Cache timeout in seconds (None for default)
        key_prefix: Prefix for cache key generation
    """

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Generate cache key from view name and arguments
            cache_key = CacheManager.get_cache_key(key_prefix, view_func.__name__, request.path, *args)

            # Try to get cached data
            cached_data = CacheManager.get(cache_key)
            if cached_data is not None:
                logger.debug(f"Cache hit for key '{cache_key}'")
                return JsonResponse(cached_data)

            # Execute view function
            response = view_func(request, *args, **kwargs)

            # Cache the response data if it's a JsonResponse
            if isinstance(response, JsonResponse) and response.status_code == 200:
                try:
                    # Extract JSON data from response
                    response_data = json.loads(response.content)
                    CacheManager.set(cache_key, response_data, timeout)
                    logger.debug(f"Cached JSON response for key '{cache_key}'")
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON response for caching: {cache_key}")

            return response

        return wrapper

    return decorator
