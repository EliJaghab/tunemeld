import os
from typing import Any, cast

import requests

from playlist_etl.constants import SERVICE_CONFIGS
from playlist_etl.helpers import get_logger

logger = get_logger(__name__)

JSON = dict[str, Any] | list[Any]


def fetch_playlist_data(service_name: str, genre: str) -> JSON:
    config = SERVICE_CONFIGS[service_name]
    host = config["host"]

    if service_name == "Spotify":
        playlist_id = config["links"][genre].split("/")[-1]
        url = f"{config['base_url']}?id={playlist_id}&offset=0&limit=100"
    elif service_name == "AppleMusic":
        playlist_id = config["links"][genre].split("/")[-1]
        apple_playlist_url = f"https://music.apple.com/us/playlist/playlist/{playlist_id}"
        url = f"{config['base_url']}?url={apple_playlist_url}"
    elif service_name == "SoundCloud":
        playlist_url = config["links"][genre]
        url = f"{config['base_url']}?playlist={playlist_url}"
    else:
        raise ValueError(f"Unknown service: {service_name}")

    api_key = os.getenv("X_RAPIDAPI_KEY")
    if not api_key:
        raise ValueError("X_RAPIDAPI_KEY not found in environment")

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": host,
        "Content-Type": "application/json",
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return cast("JSON", response.json())
