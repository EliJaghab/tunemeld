import os
import re
import time
from functools import lru_cache
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from core.constants import GenreName
import builtins
import contextlib

from bs4 import BeautifulSoup, Tag
from core.models.playlist import PlaylistData, PlaylistMetadata
from core.utils.cache_utils import CachePrefix, cache_get, cache_set
from core.utils.utils import clean_unicode_text, get_logger
from core.utils.webdriver import get_cached_webdriver
from selenium.webdriver.common.by import By
from spotipy import Spotify
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials
from tenacity import retry, stop_after_attempt, wait_exponential

logger = get_logger(__name__)

SPOTIFY_VIEW_COUNT_SELECTOR = '[data-testid="playcount"]'


@lru_cache(maxsize=4)
def get_cached_spotify_client(client_id: str, client_secret: str) -> Spotify:
    if not client_id or not client_secret:
        raise ValueError("Spotify client ID or client secret not provided.")

    return Spotify(
        client_credentials_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    )


def get_spotify_isrc(
    track_name: str, artist_name: str, client_id: str | None = None, client_secret: str | None = None
) -> str | None:
    client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET")

    key_data = f"{track_name}|{artist_name}"
    isrc = cache_get(CachePrefix.SPOTIFY_ISRC, key_data)
    if isrc:
        return str(isrc)

    logger.info(f"ISRC Spotify Lookup Cache miss for {track_name} by {artist_name}")

    spotify_client = get_cached_spotify_client(client_id, client_secret)
    track_name_no_parens = _clean_track_name(track_name)

    queries = [
        f"track:{track_name_no_parens} artist:{artist_name}",
        f"{track_name_no_parens} {artist_name}",
        f"track:{track_name.lower()} artist:{artist_name}",
    ]

    for query in queries:
        isrc = _search_spotify_for_isrc(spotify_client, query)
        if isrc:
            logger.info(f"Found ISRC for {track_name} by {artist_name}: {isrc}")
            cache_set(CachePrefix.SPOTIFY_ISRC, key_data, isrc)
            return isrc

    logger.info(f"No track found on Spotify for {track_name} by {artist_name}")
    return None


def get_spotify_track_url_by_isrc(isrc: str, client_id: str | None = None, client_secret: str | None = None) -> str:
    client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET")

    spotify_client = get_cached_spotify_client(client_id, client_secret)
    return _get_track_url_by_isrc_with_retry(spotify_client, isrc)


def _clean_track_name(track_name: str) -> str:
    return re.sub(r"\([^()]*\)", "", track_name.lower())


def _search_spotify_for_isrc(spotify_client: Spotify, query: str) -> str | None:
    try:
        results = spotify_client.search(q=query, type="track", limit=1)
        tracks = results["tracks"]["items"]
        if tracks:
            isrc_value = tracks[0]["external_ids"].get("isrc")
            return str(isrc_value) if isrc_value is not None else None
        return None
    except Exception as e:
        logger.info(f"Error searching Spotify with query '{query}': {e}")
        return None


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(5),
    reraise=True,
)
def _get_track_url_by_isrc_with_retry(spotify_client: Spotify, isrc: str) -> str:
    try:
        results = spotify_client.search(q=f"isrc:{isrc}", type="track", limit=1)
        if results["tracks"]["items"]:
            spotify_url = results["tracks"]["items"][0]["external_urls"]["spotify"]
            return str(spotify_url)
        else:
            return ""
    except SpotifyException as e:
        logger.error(f"SpotifyException: {e}")
        raise


def _get_meta_content(doc: BeautifulSoup, property_name: str) -> str | None:
    """Extract content from meta tag"""
    meta_tag = doc.find("meta", {"property": property_name})
    if meta_tag and isinstance(meta_tag, Tag) and meta_tag.get("content"):
        return str(meta_tag["content"])
    return None


def _extract_spotify_full_description(doc: BeautifulSoup) -> str | None:
    """Extract full description text from Spotify page (including Cover: part)"""
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

    if "Cover:" in full_text:
        tagline_part = full_text.split("Cover:")[0].strip()
        return tagline_part if tagline_part else None
    else:
        return full_text


def _extract_featured_artist_from_text(text: str) -> str | None:
    """Extract featured artist from text containing 'Cover: Artist Name'"""
    if not text or "Cover:" not in text:
        return None

    cover_match = re.search(r"Cover:\s*([^,\d]+?)(?:\s*\d|$)", text)
    if cover_match:
        artist = cover_match.group(1).strip()
        artist = re.sub(r"\s*\d+[,\d]*\s*(saves?|likes?|followers?).*$", "", artist)
        return artist.strip() if artist else None

    return None


def _extract_saves_and_track_count(doc: BeautifulSoup) -> tuple[str | None, int | None]:
    """Extract saves count and track count from Spotify page"""
    saves_count = None
    track_count = None

    saves_elements = doc.find_all("span", string=re.compile(r"\d+[,\d]*\s*saves?"))
    if saves_elements:
        saves_text = saves_elements[0].get_text(strip=True)
        saves_match = re.search(r"(\d+[,\d]*)\s*saves?", saves_text)
        if saves_match:
            raw_saves = saves_match.group(1)
            saves_count = _format_saves_count(raw_saves)

    og_desc = _get_meta_content(doc, "og:description")
    if og_desc:
        track_match = re.search(r"(\d+)\s*(?:items?|songs?|tracks?)", og_desc, re.IGNORECASE)
        if track_match:
            track_count = int(track_match.group(1))

        saves_match = re.search(r"(\d+\.?\d*[KMB])\s*saves?", og_desc, re.IGNORECASE)
        if saves_match and not saves_count:
            saves_count = saves_match.group(1)

    return saves_count, track_count


def _format_saves_count(raw_saves: str) -> str:
    """Format raw saves count to human-readable format"""
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
        return raw_saves


def _extract_spotify_metadata_from_html(url: str, html_content: str) -> PlaylistMetadata:
    """Extract Spotify playlist metadata from HTML content"""
    doc = BeautifulSoup(html_content, "html.parser")

    metadata: PlaylistMetadata = {
        "service_name": "Spotify",
        "playlist_url": url,
        "playlist_name": clean_unicode_text(_get_meta_content(doc, "og:title") or "Unknown"),
        "playlist_cover_url": _get_meta_content(doc, "og:image"),
        "playlist_creator": "spotify",
    }

    full_description_text = _extract_spotify_full_description(doc)

    if full_description_text:
        featured_artist = _extract_featured_artist_from_text(full_description_text)
        if featured_artist:
            metadata["playlist_featured_artist"] = clean_unicode_text(featured_artist)

        tagline = _extract_tagline_from_full_text(full_description_text)
        if tagline:
            metadata["playlist_tagline"] = clean_unicode_text(tagline)
            metadata["playlist_cover_description_text"] = clean_unicode_text(tagline)

    saves_count, track_count = _extract_saves_and_track_count(doc)
    if saves_count:
        metadata["playlist_saves_count"] = saves_count
    if track_count:
        metadata["playlist_track_count"] = track_count

    if not metadata.get("playlist_cover_description_text"):
        og_desc = _get_meta_content(doc, "og:description")
        if og_desc:
            metadata["playlist_cover_description_text"] = og_desc

    return metadata


def get_spotify_playlist(genre: "GenreName") -> PlaylistData:
    """Get Spotify playlist data and metadata for a given genre"""
    from core.constants import SERVICE_CONFIGS
    from core.utils.cache_utils import generate_spotify_cache_key_data
    from core.utils.spotdl_client import fetch_spotify_playlist_with_spotdl

    key_data = generate_spotify_cache_key_data(genre)
    cached_data = cache_get(CachePrefix.SPOTIFY_PLAYLIST, key_data)
    if cached_data:
        return cached_data

    config = SERVICE_CONFIGS["spotify"]
    url = config["links"][genre.value]

    tracks_data = fetch_spotify_playlist_with_spotdl(url)

    response = requests.get(url)
    response.raise_for_status()

    metadata = _extract_spotify_metadata_from_html(url, response.text)
    metadata["genre_name"] = genre

    playlist_data: PlaylistData = {
        "metadata": metadata,
        "tracks": tracks_data,
    }

    cache_set(CachePrefix.SPOTIFY_PLAYLIST, key_data, playlist_data)
    return playlist_data


@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), reraise=False)
def get_spotify_track_view_count(track_url: str) -> int | None:
    webdriver = get_cached_webdriver()

    try:
        driver = webdriver.get_driver()
        logger.info(f"Accessing Spotify URL: {track_url}")
        driver.get(track_url)

        # Wait for dynamic content to load
        time.sleep(5)

        # Try multiple selectors as backup
        selectors = [
            '[data-testid="playcount"]',
            'span[data-testid="playcount"]',
            '[data-testid="playcount"] span',
        ]

        view_count_element = None
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    view_count_element = elements[0]
                    logger.info(f"Found element with selector: {selector}")
                    break
            except Exception:
                continue

        if not view_count_element:
            logger.error(f"View count element not found with any selector for {track_url}")
            return None

        view_count_text = view_count_element.text.strip()
        logger.info(f"Found Spotify view count text: '{view_count_text}' for {track_url}")

        if not view_count_text:
            logger.warning(f"Empty text in view count element for {track_url}")
            return None

        # Remove commas and convert to int
        clean_text = view_count_text.replace(",", "")
        if not clean_text.isdigit():
            logger.warning(f"Non-numeric view count text: '{view_count_text}' for {track_url}")
            return None

        view_count = int(clean_text)
        logger.info(f"Successfully retrieved Spotify view count: {view_count}")
        return view_count

    except Exception as e:
        logger.error(f"WebDriver error getting Spotify view count: {e} for {track_url}")
        # Try to restart driver on critical failures
        with contextlib.suppress(builtins.BaseException):
            webdriver.close_driver()
        return None
