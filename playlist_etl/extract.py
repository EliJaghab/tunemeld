import html
import re
from typing import Any, TypedDict
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from unidecode import unidecode

from playlist_etl.constants import PLAYLIST_GENRES, SERVICE_CONFIGS
from playlist_etl.helpers import get_logger
from playlist_etl.rapid_api_client import fetch_playlist_data
from playlist_etl.utils import WebDriverManager

__all__ = [
    "PLAYLIST_GENRES",
    "SERVICE_CONFIGS",
    "PlaylistData",
    "PlaylistMetadata",
    "get_apple_music_playlist",
    "get_soundcloud_playlist",
    "get_spotify_playlist",
]

DEBUG_MODE = False

logger = get_logger(__name__)

JSON = dict[str, Any] | list[Any]


class PlaylistMetadata(TypedDict, total=False):
    """Type definition for playlist metadata extracted from web scraping"""

    service_name: str
    genre_name: str
    playlist_name: str
    playlist_url: str
    playlist_cover_url: str | None
    playlist_cover_description_text: str | None
    playlist_tagline: str | None
    playlist_featured_artist: str | None
    playlist_track_count: int | None
    playlist_saves_count: str | None
    playlist_creator: str | None
    playlist_stream_url: str | None  # Apple Music specific


class PlaylistData(TypedDict):
    """Complete playlist data including metadata and tracks"""

    metadata: PlaylistMetadata
    tracks: Any  # JSON data from RapidAPI


def _extract_spotify_metadata_from_html(url: str, html_content: str) -> PlaylistMetadata:
    """Extract Spotify playlist metadata from HTML content"""
    doc = BeautifulSoup(html_content, "html.parser")

    # Basic metadata from meta tags
    metadata: PlaylistMetadata = {
        "service_name": "Spotify",
        "playlist_url": url,
        "playlist_name": _get_meta_content(doc, "og:title") or "Unknown",
        "playlist_cover_url": _get_meta_content(doc, "og:image"),
        "playlist_creator": "spotify",  # Default for Spotify playlists
    }

    # Extract full description text first
    full_description_text = _extract_spotify_full_description(doc)

    # Extract featured artist from full text before splitting
    if full_description_text:
        featured_artist = _extract_featured_artist_from_text(full_description_text)
        if featured_artist:
            metadata["playlist_featured_artist"] = featured_artist

        # Extract clean tagline (without "Cover: Artist" part)
        tagline = _extract_tagline_from_full_text(full_description_text)
        if tagline:
            metadata["playlist_tagline"] = tagline
            metadata["playlist_cover_description_text"] = tagline

    # Extract saves count and track count from various sources
    saves_count, track_count = _extract_saves_and_track_count(doc)
    if saves_count:
        metadata["playlist_saves_count"] = saves_count
    if track_count:
        metadata["playlist_track_count"] = track_count

    # Fallback description from og:description if no tagline
    if not metadata.get("playlist_cover_description_text"):
        og_desc = _get_meta_content(doc, "og:description")
        if og_desc:
            metadata["playlist_cover_description_text"] = og_desc

    return metadata


def _get_meta_content(doc: BeautifulSoup, property_name: str) -> str | None:
    """Extract content from meta tag"""
    meta_tag = doc.find("meta", {"property": property_name})
    return meta_tag.get("content") if meta_tag else None


def _extract_spotify_full_description(doc: BeautifulSoup) -> str | None:
    """Extract full description text from Spotify page (including Cover: part)"""
    # Try multiple selectors for Spotify's description text
    selectors = [
        'span[data-encore-id="text"][variant="bodySmall"]',
        "span.encore-text-body-small.encore-internal-color-text-subdued",
        'span[class*="encore-text-body-small"]',
    ]

    for selector in selectors:
        elements = doc.select(selector)
        for element in elements:
            text = element.get_text(strip=True)
            if text and not text.isdigit() and "saves" not in text.lower():
                return str(text)

    return None


def _extract_tagline_from_full_text(full_text: str) -> str | None:
    """Extract clean tagline from full description text"""
    if not full_text:
        return None

    # Remove "Cover: Artist" part for tagline
    if "Cover:" in full_text:
        tagline_part = full_text.split("Cover:")[0].strip()
        return tagline_part if tagline_part else None
    else:
        return full_text


def _extract_featured_artist_from_text(text: str) -> str | None:
    """Extract featured artist from text containing 'Cover: Artist Name'"""
    if not text or "Cover:" not in text:
        return None

    # Extract artist name after "Cover:"
    cover_match = re.search(r"Cover:\s*([^,\d]+?)(?:\s*\d|$)", text)
    if cover_match:
        artist = cover_match.group(1).strip()
        # Clean up any trailing artifacts
        artist = re.sub(r"\s*\d+[,\d]*\s*(saves?|likes?|followers?).*$", "", artist)
        return artist.strip() if artist else None

    return None


def _extract_saves_and_track_count(doc: BeautifulSoup) -> tuple[str | None, int | None]:
    """Extract saves count and track count from Spotify page"""
    saves_count = None
    track_count = None

    # Look for saves count in span elements
    saves_elements = doc.find_all("span", string=re.compile(r"\d+[,\d]*\s*saves?"))
    if saves_elements:
        saves_text = saves_elements[0].get_text(strip=True)
        saves_match = re.search(r"(\d+[,\d]*)\s*saves?", saves_text)
        if saves_match:
            raw_saves = saves_match.group(1)
            saves_count = _format_saves_count(raw_saves)

    # Extract track count and saves count from og:description
    og_desc = _get_meta_content(doc, "og:description")
    if og_desc:
        # Look for patterns like "50 items" or "25 songs"
        track_match = re.search(r"(\d+)\s*(?:items?|songs?|tracks?)", og_desc, re.IGNORECASE)
        if track_match:
            track_count = int(track_match.group(1))

        # Also check for formatted saves in og:description
        saves_match = re.search(r"(\d+\.?\d*[KMB])\s*saves?", og_desc, re.IGNORECASE)
        if saves_match and not saves_count:
            saves_count = saves_match.group(1)

    return saves_count, track_count


def _format_saves_count(raw_saves: str) -> str:
    """Format raw saves count to human-readable format"""
    # Remove commas and convert to number
    try:
        num = int(raw_saves.replace(",", ""))
        if num >= 1_000_000_000:
            return f"{num / 1_000_000_000:.1f}B".rstrip("0").rstrip(".")
        elif num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M".rstrip("0").rstrip(".")
        elif num >= 1_000:
            return f"{num / 1_000:.1f}K".rstrip("0").rstrip(".")
        else:
            return str(num)
    except ValueError:
        return raw_saves  # Return original if conversion fails


def get_apple_music_playlist(genre: str) -> PlaylistData:
    """Get Apple Music playlist data and metadata for a given genre"""
    config = SERVICE_CONFIGS["apple_music"]
    url = config["links"][genre]

    # Get playlist tracks data
    tracks_data = fetch_playlist_data("apple_music", genre)

    # Scrape metadata from playlist page
    response = requests.get(url)
    response.raise_for_status()
    doc = BeautifulSoup(response.text, "html.parser")

    title_tag = doc.select_one("a.click-action")
    title = title_tag.get_text(strip=True) if title_tag else "Unknown"

    subtitle_tag = doc.select_one("h1")
    subtitle = subtitle_tag.get_text(strip=True) if subtitle_tag else "Unknown"

    stream_tag = doc.find("amp-ambient-video", {"class": "editorial-video"})
    playlist_stream_url = stream_tag["src"] if stream_tag and stream_tag.get("src") else None

    playlist_cover_description_tag = doc.find("p", {"data-testid": "truncate-text"})
    playlist_cover_description_text = (
        unidecode(html.unescape(playlist_cover_description_tag.get_text(strip=True)))
        if playlist_cover_description_tag
        else None
    )

    # Get cover URL using WebDriver
    webdriver_manager = WebDriverManager()
    try:
        playlist_cover_url = _get_apple_music_cover_url(webdriver_manager, url, genre)
    finally:
        webdriver_manager.close_driver()

    metadata: PlaylistMetadata = {
        "service_name": "apple_music",
        "genre_name": genre,
        "playlist_name": f"{subtitle} {title}",
        "playlist_url": url,
        "playlist_cover_url": playlist_cover_url,
        "playlist_cover_description_text": playlist_cover_description_text,
        "playlist_stream_url": playlist_stream_url,
    }

    return {
        "metadata": metadata,
        "tracks": tracks_data,
    }


def _get_apple_music_cover_url(webdriver_manager: WebDriverManager, url: str, genre: str) -> str | None:
    """Get Apple Music playlist cover URL using WebDriver"""
    xpath = "//amp-ambient-video"
    src_attribute = webdriver_manager.find_element_by_xpath(url, xpath, attribute="src")

    if src_attribute is None or src_attribute == "Element not found" or "An error occurred" in src_attribute:
        raise ValueError(f"Could not find amp-ambient-video src attribute for Apple Music {genre}")

    if src_attribute.endswith(".m3u8"):
        return src_attribute
    else:
        raise ValueError(f"Found src attribute, but it's not an m3u8 URL: {src_attribute}")


def get_soundcloud_playlist(genre: str) -> PlaylistData:
    """Get SoundCloud playlist data and metadata for a given genre"""
    config = SERVICE_CONFIGS["soundcloud"]
    url = config["links"][genre]

    # Get playlist tracks data
    tracks_data = fetch_playlist_data("soundcloud", genre)

    # Scrape metadata from playlist page
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


def get_spotify_playlist(genre: str) -> PlaylistData:
    """Get Spotify playlist data and metadata for a given genre"""
    config = SERVICE_CONFIGS["spotify"]
    url = config["links"][genre]

    # Get playlist tracks data
    tracks_data = fetch_playlist_data("spotify", genre)

    # Scrape metadata from playlist page
    response = requests.get(url)
    response.raise_for_status()

    # Extract metadata using the Spotify-specific parser
    metadata = _extract_spotify_metadata_from_html(url, response.text)
    metadata["genre_name"] = genre

    return {
        "metadata": metadata,
        "tracks": tracks_data,
    }
