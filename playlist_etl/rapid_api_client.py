import os
from typing import Any, cast

import requests
from core.utils.utils import get_logger

from playlist_etl.cache_utils import CachePrefix, cache_get, cache_set
from playlist_etl.constants import SERVICE_CONFIGS, ServiceName
from playlist_etl.spotdl_client import fetch_spotify_playlist_with_spotdl

logger = get_logger(__name__)

JSON = dict[str, Any] | list[Any]


def fetch_playlist_data(service_name: str, genre: str) -> JSON:
    config = SERVICE_CONFIGS[service_name]

    if service_name == ServiceName.SPOTIFY.value:
        playlist_url = config["links"][genre]
        return fetch_spotify_playlist_with_spotdl(playlist_url)
    elif service_name == ServiceName.APPLE_MUSIC.value:
        playlist_id = config["links"][genre].split("/")[-1]
        apple_playlist_url = f"https://music.apple.com/us/playlist/playlist/{playlist_id}"
        url = f"{config['base_url']}?url={apple_playlist_url}"

        key_data = f"{service_name}:{genre}:{url}"
        cached_data = cache_get(CachePrefix.RAPIDAPI, key_data)
        if cached_data:
            return cached_data

        data = _make_rapidapi_request(url, config["host"])
        cache_set(CachePrefix.RAPIDAPI, key_data, data)
        return data
    elif service_name == ServiceName.SOUNDCLOUD.value:
        playlist_url = config["links"][genre]
        url = f"{config['base_url']}?playlist={playlist_url}"

        key_data = f"{service_name}:{genre}:{url}"
        cached_data = cache_get(CachePrefix.RAPIDAPI, key_data)
        if cached_data:
            return cached_data

        data = _make_rapidapi_request(url, config["host"])
        cache_set(CachePrefix.RAPIDAPI, key_data, data)
        return data
    else:
        raise ValueError(f"Unknown service: {service_name}")


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
    response = requests.get(url, headers=headers, timeout=30)

    if response.status_code == 429:
        logger.error(f"RapidAPI rate limit exceeded for {host}. Skipping this request.")
        raise requests.exceptions.HTTPError(f"429 Rate limit exceeded for {host}")

    response.raise_for_status()
    logger.info(f"RapidAPI request successful - Status: {response.status_code}")
    return cast("JSON", response.json())
