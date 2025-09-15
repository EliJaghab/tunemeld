import hashlib
from collections.abc import Callable
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, NamedTuple

import pytz
import yaml
from core.constants import GenreName, ServiceName
from core.utils.utils import get_logger
from croniter import croniter
from django.core.cache import cache


class CachePrefix(str, Enum):
    RAPIDAPI = "rapidapi"
    SPOTIFY_PLAYLIST = "spotify_playlist"
    YOUTUBE_URL = "youtube_url"
    YOUTUBE_VIEW_COUNT = "youtube_view_count"
    SPOTIFY_ISRC = "spotify_isrc"
    APPLE_COVER = "apple_cover"
    GQL_PLAYLIST = "gql_playlist"
    GQL_VIEW_COUNT = "gql_view_count"


logger = get_logger(__name__)


def _load_centralized_schedule_config() -> dict:
    """Load schedule configuration from playlist_etl.yml workflow or use defaults"""
    workflow_file = Path(__file__).parent.parent.parent.parent / ".github" / "workflows" / "playlist_etl.yml"

    # Default configuration for production or when workflow file is not available
    default_config = {
        "cron_expression": "0 17 * * *",  # Daily at 5 PM UTC
        "timezone": "UTC",
        "cache_clear_window_minutes": 20
    }

    try:
        if not workflow_file.exists():
            logger.info(f"Workflow file not found at {workflow_file}, using default configuration")
            return default_config

        with open(workflow_file) as f:
            config = yaml.safe_load(f)
            # PyYAML parses 'on:' key as boolean True
            on_section = config.get("on") or config.get(True)
            if not on_section:
                logger.warning(f"Missing 'on' section in {workflow_file}, using default configuration")
                return default_config

            cron_expr = on_section["schedule"][0]["cron"]
            return {"cron_expression": cron_expr, "timezone": "UTC", "cache_clear_window_minutes": 20}
    except Exception as e:
        logger.warning(f"Failed to load workflow configuration from {workflow_file}: {e}, using default configuration")
        return default_config


_CENTRALIZED_CONFIG = _load_centralized_schedule_config()


class ScheduleConfig(NamedTuple):
    cron_expression: str = _CENTRALIZED_CONFIG["cron_expression"]
    timezone: str = _CENTRALIZED_CONFIG["timezone"]
    cache_clear_window_minutes: int = _CENTRALIZED_CONFIG["cache_clear_window_minutes"]


class SaturdayCacheClearScheduleConfig(NamedTuple):
    # we only clear the cache on Saturday because this is the only time that we get new
    # raw playlist data from services
    cron_expression: str = "0 17 * * 6"  # Saturdays at 5 PM UTC only
    timezone: str = "UTC"
    cache_clear_window_minutes: int = 20


SEVEN_DAYS_TTL = 7 * 24 * 60 * 60
TWENTY_FOUR_HOURS_TTL = 24 * 60 * 60
NO_EXPIRATION_TTL = None

CACHE_TTL_MAP = {
    CachePrefix.RAPIDAPI: SEVEN_DAYS_TTL,
    CachePrefix.SPOTIFY_PLAYLIST: SEVEN_DAYS_TTL,
    CachePrefix.YOUTUBE_URL: NO_EXPIRATION_TTL,
    CachePrefix.YOUTUBE_VIEW_COUNT: TWENTY_FOUR_HOURS_TTL,
    CachePrefix.SPOTIFY_ISRC: NO_EXPIRATION_TTL,
    CachePrefix.APPLE_COVER: SEVEN_DAYS_TTL,
    CachePrefix.GQL_PLAYLIST: SEVEN_DAYS_TTL,
    CachePrefix.GQL_VIEW_COUNT: TWENTY_FOUR_HOURS_TTL,
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


def is_within_scheduled_time_window(schedule_config: ScheduleConfig) -> bool:
    current_time = datetime.now(pytz.UTC)

    schedule_tz = pytz.timezone(schedule_config.timezone)
    current_time = current_time.astimezone(schedule_tz)

    cron = croniter(schedule_config.cron_expression, current_time)
    next_run = cron.get_next(datetime)

    cron = croniter(schedule_config.cron_expression, current_time)
    prev_run = cron.get_prev(datetime)

    window_duration = timedelta(minutes=schedule_config.cache_clear_window_minutes)

    next_window_start = next_run - window_duration
    if next_window_start <= current_time <= next_run:
        return True

    prev_window_end = prev_run + window_duration
    return prev_run <= current_time <= prev_window_end


def cache_clear_if_scheduled(prefix: CachePrefix, key_data: str, schedule_config: ScheduleConfig) -> bool:
    if not is_within_scheduled_time_window(schedule_config):
        logger.info(f"Cache clear skipped - outside scheduled window: {prefix.value}:{key_data}")
        return False

    cache_key = _generate_cache_key(prefix, key_data)
    cache.delete(cache_key)
    logger.info(f"Cache cleared within scheduled window: {prefix.value}:{key_data}")
    return True


def generate_rapidapi_cache_key_data(service_name: ServiceName, genre: GenreName) -> str:
    from core.constants import SERVICE_CONFIGS

    config = SERVICE_CONFIGS[service_name.value]

    if service_name == ServiceName.APPLE_MUSIC:
        playlist_id = config["links"][genre.value].split("/")[-1]
        apple_playlist_url = f"https://music.apple.com/us/playlist/playlist/{playlist_id}"
        url = f"{config['base_url']}?url={apple_playlist_url}"
    elif service_name == ServiceName.SOUNDCLOUD:
        playlist_url = config["links"][genre.value]
        url = f"{config['base_url']}?playlist={playlist_url}"
    else:
        raise ValueError(f"Unknown service: {service_name}")

    return f"{service_name.value}:{genre.value}:{url}"


def cache_clear_rapidapi_if_scheduled(
    service_name: ServiceName, genre: GenreName, schedule_config: ScheduleConfig
) -> bool:
    key_data = generate_rapidapi_cache_key_data(service_name, genre)
    return cache_clear_if_scheduled(CachePrefix.RAPIDAPI, key_data, schedule_config)


def generate_spotify_cache_key_data(genre: GenreName) -> str:
    from core.constants import SERVICE_CONFIGS

    config = SERVICE_CONFIGS["spotify"]
    url = config["links"][genre.value]
    return f"spotify:{genre.value}:{url}"


def get_all_rapidapi_cache_keys() -> list[str]:
    from core.constants import SERVICE_CONFIGS

    cache_keys = []
    for service_name in [ServiceName.APPLE_MUSIC, ServiceName.SOUNDCLOUD]:
        service_config = SERVICE_CONFIGS[service_name.value]
        for genre_str in service_config["links"]:
            genre = GenreName(genre_str)
            key_data = generate_rapidapi_cache_key_data(service_name, genre)
            cache_keys.append(key_data)

    return cache_keys


def get_all_spotify_cache_keys() -> list[str]:
    from core.constants import SERVICE_CONFIGS

    cache_keys = []
    service_config = SERVICE_CONFIGS["spotify"]
    for genre_str in service_config["links"]:
        genre = GenreName(genre_str)
        key_data = generate_spotify_cache_key_data(genre)
        cache_keys.append(key_data)

    return cache_keys


def get_all_raw_playlist_cache_keys() -> list[tuple[CachePrefix, str]]:
    """Get all raw playlist cache keys with their prefixes"""
    cache_keys = []

    for key_data in get_all_rapidapi_cache_keys():
        cache_keys.append((CachePrefix.RAPIDAPI, key_data))

    for key_data in get_all_spotify_cache_keys():
        cache_keys.append((CachePrefix.SPOTIFY_PLAYLIST, key_data))

    return cache_keys


def clear_cache_by_prefix(prefix: CachePrefix) -> int:
    """Clear all cache entries with the given prefix."""
    from django.core.cache import cache

    # For Redis/Memcached backends with KEY_PREFIX support
    pattern = f"{prefix.value}:*"

    # Try to use delete_pattern if available (Redis)
    if hasattr(cache, "delete_pattern"):
        deleted = cache.delete_pattern(pattern)
        logger.info(f"Cleared {deleted} cache entries with prefix {prefix.value}")
        return deleted

    # Fallback: clear all cache (less efficient but works with all backends)
    cache.clear()
    logger.info("Cleared all cache (backend doesn't support pattern deletion)")
    return -1  # Unknown count


def cached_resolver(prefix: CachePrefix):
    """Decorator for caching GraphQL resolver results."""

    def decorator(resolver_func: Callable) -> Callable:
        @wraps(resolver_func)
        def wrapper(self, info, *args, **kwargs):
            # Generate cache key from resolver name and arguments
            cache_key_parts = [resolver_func.__name__]

            # Add positional arguments
            for arg in args:
                cache_key_parts.append(str(arg))

            # Add keyword arguments (sorted for consistency)
            for key in sorted(kwargs.keys()):
                cache_key_parts.append(f"{key}={kwargs[key]}")

            key_data = ":".join(cache_key_parts)

            # Try to get from cache
            cached_result = cache_get(prefix, key_data)
            if cached_result is not None:
                return cached_result

            # Execute resolver and cache result
            result = resolver_func(self, info, *args, **kwargs)
            cache_set(prefix, key_data, result)

            return result

        return wrapper

    return decorator
