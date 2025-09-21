from typing import TYPE_CHECKING
from urllib.parse import unquote

import requests

if TYPE_CHECKING:
    from core.constants import GenreName
import time

from bs4 import BeautifulSoup, Tag
from core.models.playlist import PlaylistData, PlaylistMetadata
from core.utils.cloudflare_cache import CachePrefix, cloudflare_cache_get, cloudflare_cache_set
from core.utils.utils import clean_unicode_text, get_logger

logger = get_logger(__name__)

APPLE_MUSIC_REQUEST_DELAY = 0.5


def get_apple_music_album_cover_url(track_url: str) -> str | None:
    album_cover_url = cloudflare_cache_get(CachePrefix.APPLE_COVER, track_url)
    if album_cover_url:
        return str(album_cover_url)

    logger.info(f"Apple Music Album Cover Cache miss for URL: {track_url}")
    try:
        response = requests.get(track_url, timeout=5)
        response.raise_for_status()
        doc = BeautifulSoup(response.text, "html.parser")

        source_tag = doc.find("source", attrs={"type": "image/jpeg"})
        if not source_tag or not isinstance(source_tag, Tag) or not source_tag.has_attr("srcset"):
            raise ValueError("Album cover URL not found")

        srcset = str(source_tag["srcset"])
        album_cover_url = unquote(srcset.split()[0])
        cloudflare_cache_set(CachePrefix.APPLE_COVER, track_url, album_cover_url)
        return album_cover_url
    except Exception as e:
        logger.info(f"Error fetching album cover URL: {e}")
        return None


def _get_apple_music_cover_url_static(url: str, genre: "GenreName") -> str | None:
    """Get Apple Music playlist cover URL using static HTML extraction"""
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    doc = BeautifulSoup(response.text, "html.parser")

    stream_tag = doc.find("amp-ambient-video", {"class": "editorial-video"})
    if not stream_tag or not isinstance(stream_tag, Tag) or not stream_tag.get("src"):
        raise ValueError(f"Could not find amp-ambient-video src attribute for Apple Music {genre.value}")

    src_attribute = str(stream_tag["src"])
    if src_attribute.endswith(".m3u8"):
        return src_attribute
    else:
        raise ValueError(f"Found src attribute, but it's not an m3u8 URL: {src_attribute}")


def get_apple_music_playlist(genre: "GenreName") -> PlaylistData:
    """Get Apple Music playlist data and metadata for a given genre"""
    from core.constants import GENRE_CONFIGS, SERVICE_CONFIGS, ServiceName
    from core.utils.rapid_api_client import fetch_playlist_data

    SERVICE_CONFIGS["apple_music"]
    url = GENRE_CONFIGS[genre.value]["links"][ServiceName.APPLE_MUSIC.value]

    tracks_data = fetch_playlist_data(ServiceName.APPLE_MUSIC, genre)

    response = requests.get(url, timeout=5)
    response.raise_for_status()
    doc = BeautifulSoup(response.text, "html.parser")

    title_tag = doc.select_one("a.click-action")
    clean_unicode_text(title_tag.get_text(strip=True)) if title_tag else "Unknown"

    subtitle_tag = doc.select_one("h1")
    subtitle = clean_unicode_text(subtitle_tag.get_text(strip=True)) if subtitle_tag else "Unknown"

    stream_tag = doc.find("amp-ambient-video", {"class": "editorial-video"})
    playlist_stream_url = (
        str(stream_tag["src"]) if stream_tag and isinstance(stream_tag, Tag) and stream_tag.get("src") else None
    )

    playlist_cover_description_tag = doc.find("p", {"data-testid": "truncate-text"})
    playlist_cover_description_text = (
        clean_unicode_text(playlist_cover_description_tag.get_text(strip=True))
        if playlist_cover_description_tag
        else None
    )

    playlist_cover_url = _get_apple_music_cover_url_static(url, genre)
    logger.info(f"Successfully extracted Apple Music cover URL for {genre}")
    time.sleep(APPLE_MUSIC_REQUEST_DELAY)

    metadata: PlaylistMetadata = {
        "service_name": "apple_music",
        "genre_name": genre,
        "playlist_name": subtitle,
        "playlist_url": url,
        "playlist_cover_url": playlist_cover_url,
        "playlist_cover_description_text": playlist_cover_description_text,
        "playlist_stream_url": playlist_stream_url,
    }

    return {
        "metadata": metadata,
        "tracks": tracks_data,
    }
