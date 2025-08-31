import os
from typing import Any, cast

import requests

from playlist_etl.cache_utils import get_cached_response, set_cached_response
from playlist_etl.constants import SERVICE_CONFIGS
from playlist_etl.helpers import get_logger
from playlist_etl.spotdl_client import fetch_spotify_playlist_with_spotdl

logger = get_logger(__name__)

JSON = dict[str, Any] | list[Any]


def fetch_playlist_data(service_name: str, genre: str) -> JSON:
    config = SERVICE_CONFIGS[service_name]

    if service_name == "Spotify":
        playlist_url = config["links"][genre]
        return fetch_spotify_playlist_with_spotdl(playlist_url)
    elif service_name == "AppleMusic":
        playlist_id = config["links"][genre].split("/")[-1]
        apple_playlist_url = f"https://music.apple.com/us/playlist/playlist/{playlist_id}"
        url = f"{config['base_url']}?url={apple_playlist_url}"

        cached_data = get_cached_response(service_name, genre, url)
        if cached_data:
            return cached_data

        data = _make_rapidapi_request(url, config["host"])
        set_cached_response(service_name, genre, url, data)
        return data
    elif service_name == "SoundCloud":
        playlist_url = config["links"][genre]
        url = f"{config['base_url']}?playlist={playlist_url}"

        cached_data = get_cached_response(service_name, genre, url)
        if cached_data:
            return cached_data

        data = _make_rapidapi_request(url, config["host"])
        set_cached_response(service_name, genre, url, data)
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
    response.raise_for_status()
    logger.info(f"RapidAPI request successful - Status: {response.status_code}")
    return cast("JSON", response.json())
