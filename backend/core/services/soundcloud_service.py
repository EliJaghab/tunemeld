from typing import TYPE_CHECKING
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Tag

if TYPE_CHECKING:
    from core.constants import GenreName
from core.models.playlist_types import PlaylistData, PlaylistMetadata
from core.utils.utils import clean_unicode_text, get_logger

logger = get_logger(__name__)


def get_soundcloud_playlist(genre: "GenreName") -> PlaylistData:
    """Get SoundCloud playlist data and metadata for a given genre"""
    from core.constants import SERVICE_CONFIGS, ServiceName
    from core.utils.rapid_api_client import fetch_playlist_data

    config = SERVICE_CONFIGS["soundcloud"]
    url = config["links"][genre.value]

    tracks_data = fetch_playlist_data(ServiceName.SOUNDCLOUD, genre)

    parsed_url = urlparse(url)
    clean_url = f"{parsed_url.netloc}{parsed_url.path}"

    response = requests.get(f"https://{clean_url}")
    response.raise_for_status()
    doc = BeautifulSoup(response.text, "html.parser")

    playlist_name_tag = doc.find("meta", {"property": "og:title"})
    playlist_name = (
        clean_unicode_text(str(playlist_name_tag["content"]))
        if playlist_name_tag and isinstance(playlist_name_tag, Tag) and playlist_name_tag.get("content")
        else "Unknown"
    )

    description_tag = doc.find("meta", {"name": "description"})
    playlist_cover_description_text = (
        clean_unicode_text(str(description_tag["content"]))
        if description_tag and isinstance(description_tag, Tag) and description_tag.get("content")
        else "No description available"
    )

    playlist_cover_url_tag = doc.find("meta", {"property": "og:image"})
    playlist_cover_url = (
        str(playlist_cover_url_tag["content"])
        if playlist_cover_url_tag and isinstance(playlist_cover_url_tag, Tag) and playlist_cover_url_tag.get("content")
        else None
    )

    metadata: PlaylistMetadata = {
        "service_name": "soundcloud",
        "genre_name": genre.value,
        "playlist_name": playlist_name,
        "playlist_url": url,
        "playlist_cover_url": playlist_cover_url,
        "playlist_cover_description_text": playlist_cover_description_text,
    }

    return {
        "metadata": metadata,
        "tracks": tracks_data,
    }
