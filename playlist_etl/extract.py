import html
import os
import re
from typing import TypedDict
from urllib.parse import quote, urlparse

import requests
from bs4 import BeautifulSoup
from unidecode import unidecode

from playlist_etl.helpers import get_logger, set_secrets

__all__ = ["PLAYLIST_GENRES", "SERVICE_CONFIGS", "PlaylistMetadata", "SpotifyFetcher", "run_extraction"]
from playlist_etl.constants import PLAYLIST_GENRES, SERVICE_CONFIGS
from playlist_etl.utils import (
    WebDriverManager,
    clear_collection,
    get_mongo_client,
    insert_or_update_data_to_mongo,
)

DEBUG_MODE = False
NO_RAPID = False


logger = get_logger(__name__)


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
                return text

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


class RapidAPIClient:
    def __init__(self):
        self.api_key = self._get_api_key()
        logger.info(f"apiKey: {self.api_key}")

    @staticmethod
    def _get_api_key():
        api_key = os.getenv("X_RAPIDAPI_KEY")
        if not api_key:
            raise Exception("Failed to set API Key.")
        return api_key


def get_json_response(url, host, api_key):
    if DEBUG_MODE or NO_RAPID:
        logger.info("Debug Mode: not requesting RapidAPI")
        return {}

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": host,
        "Content-Type": "application/json",
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


class Extractor:
    def __init__(self, client, service_name, genre):
        self.client = client
        self.config = SERVICE_CONFIGS[service_name]
        self.base_url = self.config["base_url"]
        self.host = self.config["host"]
        self.api_key = self.client.api_key
        self.genre = genre
        self.playlist_param = self._prepare_param(self.config["links"][genre])
        self.param_key = self.config["param_key"]

    def _prepare_param(self, url):
        if "spotify" in self.base_url:
            return url.split("/")[-1]
        else:
            return quote(url)

    def get_playlist(self):
        raise NotImplementedError("Each service must implement its own `get_playlist` method.")


class AppleMusicFetcher(Extractor):
    def __init__(self, client, service_name, genre):
        super().__init__(client, service_name, genre)
        self.webdriver_manager = WebDriverManager()

    def get_playlist(self):
        url = f"{self.base_url}?{self.param_key}={self.playlist_param}"
        return get_json_response(url, self.host, self.api_key)

    def set_playlist_details(self):
        url = self.config["links"][self.genre]

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

        self.playlist_url = url
        self.playlist_name = f"{subtitle} {title}"
        self.playlist_cover_url = self.get_cover_url(url)
        self.playlist_cover_description_text = playlist_cover_description_text
        self.playlist_stream_url = playlist_stream_url

    def get_cover_url(self, url: str) -> str:
        xpath = "//amp-ambient-video"
        src_attribute = self.webdriver_manager.find_element_by_xpath(url, xpath, attribute="src")

        if src_attribute == "Element not found" or "An error occurred" in src_attribute:
            raise ValueError(f"Could not find amp-ambient-video src attribute for Apple Music {self.genre}")

        if src_attribute.endswith(".m3u8"):
            return src_attribute
        else:
            raise ValueError(f"Found src attribute, but it's not an m3u8 URL: {src_attribute}")


class SoundCloudFetcher(Extractor):
    def __init__(self, client, service_name, genre):
        super().__init__(client, service_name, genre)

    def get_playlist(self):
        url = f"{self.base_url}?{self.param_key}={self.playlist_param}"
        return get_json_response(url, self.host, self.api_key)

    def set_playlist_details(self):
        url = self.config["links"][self.genre]
        parsed_url = urlparse(url)
        clean_url = f"{parsed_url.netloc}{parsed_url.path}"

        response = requests.get(f"https://{clean_url}")
        response.raise_for_status()
        doc = BeautifulSoup(response.text, "html.parser")

        playlist_name_tag = doc.find("meta", {"property": "og:title"})
        self.playlist_name = playlist_name_tag["content"] if playlist_name_tag else "Unknown"

        description_tag = doc.find("meta", {"name": "description"})
        self.playlist_cover_description_text = (
            description_tag["content"] if description_tag else "No description available"
        )

        playlist_cover_url_tag = doc.find("meta", {"property": "og:image"})
        self.playlist_cover_url = playlist_cover_url_tag["content"] if playlist_cover_url_tag else None

        self.playlist_url = url


class SpotifyFetcher(Extractor):
    def __init__(self, client, service_name, genre):
        super().__init__(client, service_name, genre)

    def get_playlist(self, offset=0, limit=100):
        url = f"{self.base_url}?{self.param_key}={self.playlist_param}&offset={offset}&limit={limit}"
        return get_json_response(url, self.host, self.api_key)

    def set_playlist_details(self):
        url = self.config["links"][self.genre]
        response = requests.get(url)
        response.raise_for_status()

        # Extract metadata using the Spotify-specific parser
        metadata = _extract_spotify_metadata_from_html(url, response.text)
        metadata["genre_name"] = self.genre

        # Set attributes from parsed metadata
        self.playlist_name = metadata.get("playlist_name", "Unknown")
        self.playlist_cover_url = metadata.get("playlist_cover_url")
        self.playlist_url = metadata.get("playlist_url", url)
        self.playlist_tagline = metadata.get("playlist_tagline")
        self.playlist_featured_artist = metadata.get("playlist_featured_artist")
        self.playlist_track_count = metadata.get("playlist_track_count")
        self.playlist_saves_count = metadata.get("playlist_saves_count")
        self.playlist_creator = metadata.get("playlist_creator", "spotify")

        # Set description text to tagline or fallback
        self.playlist_cover_description_text = self.playlist_tagline or metadata.get(
            "playlist_cover_description_text", "No description available"
        )

    def get_metadata_as_typed_dict(self) -> PlaylistMetadata:
        """Return metadata as a typed dict for use in transformation pipeline"""
        return {
            "service_name": "Spotify",
            "genre_name": self.genre,
            "playlist_name": getattr(self, "playlist_name", "Unknown"),
            "playlist_url": getattr(self, "playlist_url", ""),
            "playlist_cover_url": getattr(self, "playlist_cover_url", None),
            "playlist_cover_description_text": getattr(self, "playlist_cover_description_text", None),
            "playlist_tagline": getattr(self, "playlist_tagline", None),
            "playlist_featured_artist": getattr(self, "playlist_featured_artist", None),
            "playlist_track_count": getattr(self, "playlist_track_count", None),
            "playlist_saves_count": getattr(self, "playlist_saves_count", None),
            "playlist_creator": getattr(self, "playlist_creator", None),
        }


def run_extraction(mongo_client, client, service_name, genre):
    if service_name == "AppleMusic":
        extractor = AppleMusicFetcher(client, service_name, genre)
    elif service_name == "SoundCloud":
        extractor = SoundCloudFetcher(client, service_name, genre)
    elif service_name == "Spotify":
        extractor = SpotifyFetcher(client, service_name, genre)
    else:
        raise ValueError(f"Unknown service: {service_name}")

    try:
        extractor.set_playlist_details()
        playlist_data = extractor.get_playlist()

        document = {
            "service_name": service_name,
            "genre_name": genre,
            "playlist_url": extractor.playlist_url,
            "data_json": playlist_data,
            "playlist_name": extractor.playlist_name,
            "playlist_cover_url": extractor.playlist_cover_url,
            "playlist_cover_description_text": extractor.playlist_cover_description_text,
            # New enhanced fields
            "playlist_tagline": getattr(extractor, "playlist_tagline", None),
            "playlist_featured_artist": getattr(extractor, "playlist_featured_artist", None),
            "playlist_saves_count": getattr(extractor, "playlist_saves_count", None),
            "playlist_track_count": getattr(extractor, "playlist_track_count", None),
            "playlist_creator": getattr(extractor, "playlist_creator", None),
        }

        if not DEBUG_MODE:
            insert_or_update_data_to_mongo(mongo_client, "raw_playlists", document)
        else:
            logger.info("Debug Mode: not updating mongo")
    finally:
        # Clean up WebDriver for AppleMusic extractor
        if hasattr(extractor, "webdriver_manager"):
            extractor.webdriver_manager.close_driver()


if __name__ == "__main__":
    set_secrets()
    client = RapidAPIClient()
    mongo_client = get_mongo_client()

    if DEBUG_MODE:
        logger.info("Debug Mode: not clearing mongo")
    else:
        clear_collection(mongo_client, "raw_playlists")

    for service_name, config in SERVICE_CONFIGS.items():
        for genre in PLAYLIST_GENRES:
            logger.info(f"Retrieving {genre} from {service_name} with credential {config['links'][genre]}")
            run_extraction(mongo_client, client, service_name, genre)
