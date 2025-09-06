from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from core.models.playlist_types import PlaylistData, PlaylistMetadata
from core.utils.utils import get_logger

logger = get_logger(__name__)


def get_soundcloud_playlist(genre: str) -> PlaylistData:
    """Get SoundCloud playlist data and metadata for a given genre"""
    from playlist_etl.constants import SERVICE_CONFIGS
    from playlist_etl.rapid_api_client import fetch_playlist_data

    config = SERVICE_CONFIGS["soundcloud"]
    url = config["links"][genre]

    tracks_data = fetch_playlist_data("soundcloud", genre)

    parsed_url = urlparse(url)
    clean_url = f"{parsed_url.netloc}{parsed_url.path}"

    response = requests.get(f"https://{clean_url}")
    response.raise_for_status()
    doc = BeautifulSoup(response.text, "html.parser")

    playlist_name_tag = doc.find("meta", {"property": "og:title"})
    playlist_name = playlist_name_tag["content"] if playlist_name_tag else "Unknown"

    description_tag = doc.find("meta", {"name": "description"})
    playlist_cover_description_text = description_tag["content"] if description_tag else "No description available"

    playlist_cover_url_tag = doc.find("meta", {"property": "og:image"})
    playlist_cover_url = playlist_cover_url_tag["content"] if playlist_cover_url_tag else None

    metadata: PlaylistMetadata = {
        "service_name": "soundcloud",
        "genre_name": genre,
        "playlist_name": playlist_name,
        "playlist_url": url,
        "playlist_cover_url": playlist_cover_url,
        "playlist_cover_description_text": playlist_cover_description_text,
    }

    return {
        "metadata": metadata,
        "tracks": tracks_data,
    }
