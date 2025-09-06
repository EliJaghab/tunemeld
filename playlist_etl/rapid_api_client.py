import os
import time
from typing import Any, cast

import requests
from core.utils.utils import get_logger

from playlist_etl.cache_utils import CachePrefix, cache_get, cache_set, generate_rapidapi_cache_key_data
from playlist_etl.constants import SERVICE_CONFIGS, GenreName, ServiceName

logger = get_logger(__name__)

JSON = dict[str, Any] | list[Any]


def fetch_playlist_data(service_name: ServiceName, genre: GenreName) -> JSON:
    key_data = generate_rapidapi_cache_key_data(service_name, genre)

    cached_data = cache_get(CachePrefix.RAPIDAPI, key_data)
    if cached_data:
        return cast("JSON", cached_data)

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

    data = _make_rapidapi_request(url, config["host"])
    cache_set(CachePrefix.RAPIDAPI, key_data, data)
    return data


def _make_rapidapi_request(url: str, host: str) -> JSON:
    """Make a RapidAPI request with proper error handling"""
    api_key = os.getenv("X_RAPIDAPI_KEY")
    if not api_key:
        raise ValueError("X_RAPIDAPI_KEY not found in environment")

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": host,
        "Content-Type": "application/json",
    }

    logger.info(f"Making RapidAPI request to {host}")
    time.sleep(10.0)
    response = requests.get(url, headers=headers, timeout=30)

    if response.status_code == 429:
        logger.error(f"RapidAPI rate limit exceeded for {host}. Skipping this request.")
        raise requests.exceptions.HTTPError(f"429 Rate limit exceeded for {host}")

    response.raise_for_status()
    logger.info(f"RapidAPI request successful - Status: {response.status_code}")
    return cast("JSON", response.json())
