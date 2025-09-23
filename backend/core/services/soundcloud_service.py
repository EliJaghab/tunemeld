import re
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Tag

if TYPE_CHECKING:
    from core.constants import GenreName
from core.models.playlist import PlaylistData, PlaylistMetadata
from core.utils.utils import clean_unicode_text, get_logger

logger = get_logger(__name__)


def get_soundcloud_playlist(genre: "GenreName") -> PlaylistData:
    """Get SoundCloud playlist data and metadata for a given genre"""
    from core.constants import GENRE_CONFIGS, SERVICE_CONFIGS, ServiceName
    from core.utils.rapid_api_client import fetch_playlist_data

    SERVICE_CONFIGS["soundcloud"]
    url = GENRE_CONFIGS[genre.value]["links"][ServiceName.SOUNDCLOUD.value]

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

    meta_description_tag = doc.find("meta", {"name": "description"})
    meta_description = (
        clean_unicode_text(str(meta_description_tag["content"]))
        if meta_description_tag and isinstance(meta_description_tag, Tag) and meta_description_tag.get("content")
        else None
    )

    og_description_tag = doc.find("meta", {"property": "og:description"})
    og_description_raw = (
        str(og_description_tag["content"])
        if og_description_tag and isinstance(og_description_tag, Tag) and og_description_tag.get("content")
        else None
    )

    og_description = None
    if og_description_raw:
        url_match = re.search(r"https?://[^\s]+", og_description_raw)
        if url_match:
            og_description = clean_unicode_text(og_description_raw.replace(url_match.group(), "").strip())
        else:
            og_description = clean_unicode_text(og_description_raw)

    if meta_description and og_description and meta_description != og_description:
        playlist_cover_description_text = f"{meta_description} | {og_description}"
    elif og_description:
        playlist_cover_description_text = og_description
    elif meta_description:
        playlist_cover_description_text = meta_description
    else:
        playlist_cover_description_text = "No description available"

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
