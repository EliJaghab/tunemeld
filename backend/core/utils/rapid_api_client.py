import os
from typing import Any, cast

import requests
from core.constants import GENRE_CONFIGS, SERVICE_CONFIGS, GenreName, ServiceName
from core.utils.cloudflare_cache import CachePrefix, cloudflare_cache_get, cloudflare_cache_set
from core.utils.utils import get_logger

logger = get_logger(__name__)

JSON = dict[str, Any] | list[Any]


def fetch_playlist_data(service_name: ServiceName, genre: GenreName, force_refresh: bool = False) -> JSON:
    key_data = f"{service_name.value}_{genre.value}"

    # Determine cache prefix based on service
    if service_name == ServiceName.APPLE_MUSIC:
        cache_prefix = CachePrefix.RAPIDAPI_APPLE_MUSIC
    elif service_name == ServiceName.SOUNDCLOUD:
        cache_prefix = CachePrefix.RAPIDAPI_SOUNDCLOUD
    else:
        raise ValueError(f"Unknown service: {service_name}")

    if not force_refresh:
        cached_data = cloudflare_cache_get(cache_prefix, key_data)
        if cached_data:
            return cast("JSON", cached_data)

    config = SERVICE_CONFIGS[service_name.value]

    if service_name == ServiceName.APPLE_MUSIC:
        playlist_id = GENRE_CONFIGS[genre.value]["links"][service_name.value].split("/")[-1]
        apple_playlist_url = f"https://music.apple.com/us/playlist/playlist/{playlist_id}"
        url = f"{config['base_url']}?url={apple_playlist_url}"
    elif service_name == ServiceName.SOUNDCLOUD:
        playlist_url = GENRE_CONFIGS[genre.value]["links"][service_name.value]
        url = f"{config['base_url']}?playlist={playlist_url}"

    data = _make_rapidapi_request(url, config["host"])
    cloudflare_cache_set(cache_prefix, key_data, data)
    return data


def _make_rapidapi_request(url: str, host: str) -> JSON:
    """Make a RapidAPI request with automatic key rotation on rate limits"""
    api_keys = [
        os.getenv("X_RAPIDAPI_KEY_A"),
        os.getenv("X_RAPIDAPI_KEY_B"),
    ]

    for api_key in api_keys:
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": host,
            "Content-Type": "application/json",
        }

        logger.info(f"Making RapidAPI request to {host}")

        response = requests.get(url, headers=headers, timeout=60)

        if response.status_code == 429:
            logger.warning(f"RapidAPI rate limit exceeded for {host}. Trying next key...")
            continue

        response.raise_for_status()
        logger.info(f"RapidAPI request successful - Status: {response.status_code}")
        return cast("JSON", response.json())

    logger.error(f"All RapidAPI keys exhausted for {host}")
    raise requests.exceptions.HTTPError(f"All RapidAPI keys failed for {host}")
