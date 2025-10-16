import datetime
import hashlib
import json
import os
import re
import time
from enum import Enum
from typing import Any

import requests
from core import settings
from core.constants import GenreName, ServiceName
from core.settings import DEV
from core.utils.utils import get_logger
from django.core.cache import cache
from django.core.cache.backends.base import BaseCache

logger = get_logger(__name__)

# API caching TTL configuration
SEVEN_DAYS_TTL = 7 * 24 * 60 * 60
TWENTY_FOUR_HOURS_TTL = 24 * 60 * 60
NO_EXPIRATION_TTL = None

CLOUDFLARE_CACHE_TTL_MAP = {
    "rapidapi_apple_music": SEVEN_DAYS_TTL,
    "rapidapi_soundcloud": SEVEN_DAYS_TTL,
    "spotify_playlist": SEVEN_DAYS_TTL,
    "youtube_url": NO_EXPIRATION_TTL,
    "youtube_view_count": TWENTY_FOUR_HOURS_TTL,
    "spotify_isrc": NO_EXPIRATION_TTL,
    "apple_cover": SEVEN_DAYS_TTL,
    "soundcloud_url": NO_EXPIRATION_TTL,
    "album_cover_image": SEVEN_DAYS_TTL,
    "genius_url": NO_EXPIRATION_TTL,
    "genius_lyrics": NO_EXPIRATION_TTL,
    "reccobeats_audio_features": NO_EXPIRATION_TTL,
}


class CachePrefix(str, Enum):
    RAPIDAPI_APPLE_MUSIC = "rapidapi_apple_music"
    RAPIDAPI_SOUNDCLOUD = "rapidapi_soundcloud"
    SPOTIFY_PLAYLIST = "spotify_playlist"
    YOUTUBE_URL = "youtube_url"
    YOUTUBE_VIEW_COUNT = "youtube_view_count"
    SPOTIFY_ISRC = "spotify_isrc"
    APPLE_COVER = "apple_cover"
    SOUNDCLOUD_URL = "soundcloud_url"
    ALBUM_COVER_IMAGE = "album_cover_image"
    GENIUS_URL = "genius_url"
    GENIUS_LYRICS = "genius_lyrics"
    RECCOBEATS_AUDIO_FEATURES = "reccobeats_audio_features"


class CloudflareKVCache(BaseCache):
    BASE_URL_TEMPLATE = "https://api.cloudflare.com/client/v4/accounts/{}/storage/kv/namespaces/{}/values/"
    _session: requests.Session | None = None

    def __init__(self, server, params):
        super().__init__(params)
        logger.debug("Initializing CloudflareKVCache class...")

        self.CF_ACCOUNT_ID = settings.CF_ACCOUNT_ID or ""
        self.CF_NAMESPACE_ID = settings.CF_NAMESPACE_ID or ""
        self.CF_API_TOKEN = settings.CF_API_TOKEN or ""

        if CloudflareKVCache._session is None:
            CloudflareKVCache._session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=0)
            CloudflareKVCache._session.mount("https://", adapter)
            CloudflareKVCache._session.headers.update(
                {"Authorization": f"Bearer {self.CF_API_TOKEN}", "Content-Type": "application/json"}
            )

        # Allow cache to be initialized without credentials in CI/test environments
        secret_key = getattr(settings, "SECRET_KEY", os.getenv("SECRET_KEY", ""))
        is_ci = (
            secret_key == "test-secret-key-for-ci"
            or getattr(settings, "TESTING", False)
            or os.getenv("CI", "").lower() == "true"
        )
        logger.debug(f"Cache init: SECRET_KEY={secret_key}, is_ci={is_ci}")

        if not self.CF_ACCOUNT_ID or not self.CF_NAMESPACE_ID or not self.CF_API_TOKEN:
            if is_ci:
                logger.warning("CloudflareKVCache initialized without Cloudflare KV credentials (CI/test environment)")
                self.BASE_URL = ""
                return
            else:
                missing = []
                if not self.CF_ACCOUNT_ID:
                    missing.append("CF_ACCOUNT_ID")
                if not self.CF_NAMESPACE_ID:
                    missing.append("CF_NAMESPACE_ID")
                if not self.CF_API_TOKEN:
                    missing.append("CF_API_TOKEN")
                raise ValueError(f"Missing required Cloudflare KV credentials: {', '.join(missing)}")

        self.BASE_URL = self.BASE_URL_TEMPLATE.format(self.CF_ACCOUNT_ID, self.CF_NAMESPACE_ID)
        logger.info("CloudflareKVCache initialized with Cloudflare KV + shared connection pool")

    def get(self, key: str, default: Any = None, version: int | None = None) -> Any:
        if settings.ENVIRONMENT == DEV and os.getenv("ENABLE_CACHE_IN_DEV", "").lower() != "true":
            return default

        key = self.make_key(key, version=version)
        sanitized_key = self._validate_key(key)

        if not self.BASE_URL:
            return default

        try:
            url = self.BASE_URL + sanitized_key
            if CloudflareKVCache._session is None:
                return default
            response = CloudflareKVCache._session.get(url)
            value = response.json().get("value")
            return json.loads(value) if value else default
        except Exception as e:
            logger.warning(f"Cache timeout or error for key {key}: {e}")
            return default

    def set(self, key: str, value: Any, timeout: int | None = None, version: int | None = None) -> bool:
        if settings.ENVIRONMENT == DEV and os.getenv("ENABLE_CACHE_IN_DEV", "").lower() != "true":
            return True

        key = self.make_key(key, version=version)
        sanitized_key = self._validate_key(key)

        if not self.BASE_URL:
            return False

        try:
            url = self.BASE_URL + sanitized_key
            serialized_value = json.dumps(value)
            if CloudflareKVCache._session is None:
                return False
            response = CloudflareKVCache._session.put(url, json={"value": serialized_value})
            response.raise_for_status()
            result = response.json()
            return result.get("success", False)
        except Exception as e:
            logger.warning(f"Cache timeout or error setting key {key}: {e}")
            return False

    def put(self, key, value):
        return self.set(key, value)

    def delete(self, key: str, version: int | None = None) -> bool:
        return self.set(key, None, version=version)

    def clear(self) -> bool:
        return True

    def has_key(self, key: str, version: int | None = None) -> bool:
        return self.get(key, version=version) is not None

    def _validate_key(self, key: str) -> str:
        sanitized_key = re.sub(r"[^a-zA-Z0-9\-_]", "_", key)
        return sanitized_key[:512] if len(sanitized_key) > 512 else sanitized_key


def _generate_cache_key(prefix: CachePrefix, key_data: str) -> str:
    full_key = f"{prefix.value}:{key_data}"
    return hashlib.md5(full_key.encode()).hexdigest()


def cloudflare_cache_get(prefix: CachePrefix, key_data: str) -> Any:
    """Get data from Cloudflare KV cache."""
    start_time = time.time()
    cache_key = _generate_cache_key(prefix, key_data)

    try:
        cloudflare_cache = cache  # This is the 'default' cache in settings
        data = cloudflare_cache.get(cache_key)
        elapsed = time.time() - start_time

        if data is not None:
            logger.info(f"Cache HIT (cloudflare): {prefix.value}:{key_data} ({elapsed:.3f}s)")
        else:
            logger.info(f"Cache MISS (cloudflare): {prefix.value}:{key_data} ({elapsed:.3f}s)")
        return data
    except Exception as e:
        logger.warning(f"Cloudflare cache error: {prefix.value}:{key_data}: {e}")
        return None


def cloudflare_cache_set(prefix: CachePrefix, key_data: str, value: Any, ttl: int | None = None) -> None:
    """Set data in Cloudflare KV cache."""
    cache_key = _generate_cache_key(prefix, key_data)

    try:
        cloudflare_cache = cache
        if ttl is None:
            ttl = CLOUDFLARE_CACHE_TTL_MAP.get(prefix.value, SEVEN_DAYS_TTL)
        cloudflare_cache.set(cache_key, value, ttl)
        logger.info(f"Cached (cloudflare): {prefix.value}:{key_data}")
    except Exception as e:
        logger.warning(f"Failed to cache in Cloudflare: {prefix.value}:{key_data}: {e}")


def cloudflare_cache_delete(prefix: CachePrefix, key_data: str) -> bool:
    """Delete a specific key from Cloudflare KV cache."""
    cache_key = _generate_cache_key(prefix, key_data)

    try:
        cloudflare_cache = cache
        cloudflare_cache.delete(cache_key)
        logger.info(f"Deleted (cloudflare): {prefix.value}:{key_data}")
        return True
    except Exception as e:
        logger.warning(f"Failed to delete from Cloudflare cache: {prefix.value}:{key_data}: {e}")
        return False


def clear_rapidapi_cache() -> int:
    """
    Clear RapidAPI and Spotify playlist cache keys.

    Only clears on Saturday scheduled GitHub Actions runs.
    """
    github_event = os.getenv("GITHUB_EVENT_NAME", "unknown")
    current_time = datetime.datetime.utcnow()
    current_weekday = current_time.weekday()
    day_name = current_time.strftime("%A")

    logger.info(f"CACHE AUDIT: Event={github_event}, Day={day_name}, Weekday={current_weekday}")
    logger.info(f"   Time: {current_time.isoformat()}")

    if github_event != "schedule":
        logger.info("CACHE PRESERVED: Not a scheduled run - preserving RapidAPI cache to avoid rate limits")
        logger.info(f"   Event type: {github_event} (expected: 'schedule')")
        return 0

    if current_weekday != 5:  # 5 = Saturday
        logger.info(f"CACHE PRESERVED: Scheduled run on {day_name} - preserving RapidAPI cache (Saturday only)")
        logger.info(f"   Current weekday: {current_weekday} (expected: 5 for Saturday)")
        return 0

    logger.info("CACHE CLEARING TRIGGERED: Saturday scheduled run detected")
    logger.info("   Clearing RapidAPI and Spotify playlist cache for fresh playlist data")
    logger.info(f"   Conditions met: Event={github_event}, Day={day_name}, Weekday={current_weekday}")

    cleared_count = 0

    # Clear Apple Music cache
    for genre in GenreName:
        key_data = f"{ServiceName.APPLE_MUSIC.value}_{genre.value}"
        if cloudflare_cache_get(CachePrefix.RAPIDAPI_APPLE_MUSIC, key_data):
            cloudflare_cache_delete(CachePrefix.RAPIDAPI_APPLE_MUSIC, key_data)
            cleared_count += 1
            logger.info(f"Cleared Apple Music cache: {key_data}")

    # Clear SoundCloud cache
    for genre in GenreName:
        key_data = f"{ServiceName.SOUNDCLOUD.value}_{genre.value}"
        if cloudflare_cache_get(CachePrefix.RAPIDAPI_SOUNDCLOUD, key_data):
            cloudflare_cache_delete(CachePrefix.RAPIDAPI_SOUNDCLOUD, key_data)
            cleared_count += 1
            logger.info(f"Cleared SoundCloud cache: {key_data}")

    # Clear Spotify playlist cache
    for genre in GenreName:
        key_data = generate_spotify_cache_key_data(genre)
        if cloudflare_cache_get(CachePrefix.SPOTIFY_PLAYLIST, key_data):
            cloudflare_cache_delete(CachePrefix.SPOTIFY_PLAYLIST, key_data)
            cleared_count += 1
            logger.info(f"Cleared Spotify playlist cache: {key_data}")

    logger.info(f"Playlist cache clearing completed - {cleared_count} keys cleared")
    return cleared_count


def generate_spotify_cache_key_data(genre: GenreName) -> str:
    """Generate cache key data for Spotify playlists."""
    from core.constants import GENRE_CONFIGS, ServiceName

    url = GENRE_CONFIGS[genre.value]["links"][ServiceName.SPOTIFY.value]
    return f"spotify:{genre.value}:{url}"
