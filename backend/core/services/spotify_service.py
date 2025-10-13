import builtins
import contextlib
import os
import re
import time
from functools import lru_cache
from typing import TYPE_CHECKING

import requests
from bs4 import BeautifulSoup, Tag
from core.services.reccobeats_service import fetch_reccobeats_audio_features
from django.conf import settings
from spotipy import Spotify
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials

if settings.ETL_DEPENDENCIES_AVAILABLE:
    from selenium.webdriver.common.by import By
else:
    By = None  # type: ignore

from tenacity import retry, stop_after_attempt, wait_exponential

if TYPE_CHECKING:
    from core.constants import GenreName
from core.constants import GENRE_CONFIGS, SERVICE_CONFIGS, ServiceName
from core.models.playlist import PlaylistData, PlaylistMetadata
from core.utils.cloudflare_cache import (
    CachePrefix,
    cloudflare_cache_get,
    cloudflare_cache_set,
    generate_spotify_cache_key_data,
)
from core.utils.utils import clean_unicode_text, get_logger

# ETL utilities - import conditionally
if settings.ETL_DEPENDENCIES_AVAILABLE:
    from core.utils.spotdl_client import fetch_spotify_playlist_with_spotdl
    from core.utils.webdriver import get_cached_webdriver
else:
    fetch_spotify_playlist_with_spotdl = None  # type: ignore
    get_cached_webdriver = None  # type: ignore

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
    isrc = cloudflare_cache_get(CachePrefix.SPOTIFY_ISRC, key_data)
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
            cloudflare_cache_set(CachePrefix.SPOTIFY_ISRC, key_data, isrc)
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


def _extract_track_count(doc: BeautifulSoup) -> int | None:
    """Extract track count from Spotify page"""
    og_desc = _get_meta_content(doc, "og:description")
    if og_desc:
        track_match = re.search(r"(\d+)\s*(?:items?|songs?|tracks?)", og_desc, re.IGNORECASE)
        if track_match:
            return int(track_match.group(1))
    return None


def _extract_spotify_metadata_from_html(url: str, html_content: str) -> PlaylistMetadata:
    """Extract Spotify playlist metadata from HTML content"""
    doc = BeautifulSoup(html_content, "html.parser")

    metadata: PlaylistMetadata = {
        "service_name": "Spotify",
        "playlist_url": url,
        "playlist_name": clean_unicode_text(_get_meta_content(doc, "og:title") or "Unknown"),
        "playlist_cover_url": _get_meta_content(doc, "og:image"),
        "playlist_creator": ServiceName.SPOTIFY.value,
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

    track_count = _extract_track_count(doc)
    if track_count:
        metadata["playlist_track_count"] = track_count

    if not metadata.get("playlist_cover_description_text"):
        og_desc = _get_meta_content(doc, "og:description")
        if og_desc:
            metadata["playlist_cover_description_text"] = og_desc

    return metadata


def get_spotify_playlist(genre: "GenreName", force_refresh: bool = False) -> PlaylistData:
    """Get Spotify playlist data and metadata for a given genre"""
    key_data = generate_spotify_cache_key_data(genre)
    if not force_refresh:
        cached_data = cloudflare_cache_get(CachePrefix.SPOTIFY_PLAYLIST, key_data)
        if cached_data:
            return cached_data

    SERVICE_CONFIGS[ServiceName.SPOTIFY.value]
    url = GENRE_CONFIGS[genre.value]["links"][ServiceName.SPOTIFY.value]

    tracks_data = fetch_spotify_playlist_with_spotdl(url)

    response = requests.get(url)
    response.raise_for_status()

    metadata = _extract_spotify_metadata_from_html(url, response.text)
    metadata["genre_name"] = genre

    playlist_data: PlaylistData = {
        "metadata": metadata,
        "tracks": tracks_data,
    }

    cloudflare_cache_set(CachePrefix.SPOTIFY_PLAYLIST, key_data, playlist_data)
    return playlist_data


@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), reraise=True)
def get_spotify_track_view_count(track_url: str) -> int:
    """Get Spotify track view count using webdriver if available, otherwise return 0."""
    if settings.ETL_DEPENDENCIES_AVAILABLE and get_cached_webdriver is not None:
        try:
            return get_spotify_track_view_count_with_webdriver(track_url)
        except Exception as e:
            logger.warning(f"Webdriver extraction failed for {track_url}: {e}")
            return 0
    else:
        # In serverless environment or webdriver not available
        logger.info(f"Webdriver not available for Spotify extraction: {track_url}")
        return 0


def get_spotify_track_view_count_with_webdriver(track_url: str) -> int:
    """Get Spotify track view count using webdriver. Raises exception if failed."""
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
            raise ValueError("No playcount element found on Spotify page")

        view_count_text = view_count_element.text.strip()
        logger.info(f"Found Spotify play count text: '{view_count_text}' for {track_url}")

        if not view_count_text:
            raise ValueError("Empty playcount text on Spotify page")

        # Remove commas and convert to int
        clean_text = view_count_text.replace(",", "")
        if not clean_text.isdigit():
            raise ValueError(f"Invalid playcount format: {view_count_text}")

        view_count = int(clean_text)
        logger.info(f"Successfully retrieved Spotify play count: {view_count}")
        return view_count

    except Exception as e:
        # Try to restart driver on critical failures
        with contextlib.suppress(builtins.BaseException):
            webdriver.close_driver()
        raise e


def extract_spotify_track_id_from_url(spotify_url: str) -> str:
    """
    Extract track ID from Spotify URL.

    Args:
        spotify_url: Spotify track URL (e.g., https://open.spotify.com/track/7xGfFoTpQ2E7fRF5lN10tr)

    Returns:
        Spotify track ID (e.g., 7xGfFoTpQ2E7fRF5lN10tr)
    """
    return spotify_url.split("/track/")[1].split("?")[0]


def get_spotify_audio_features(
    spotify_track_id: str, client_id: str | None = None, client_secret: str | None = None
) -> dict | None:
    """
    Fetch audio features for a Spotify track using ReccoBeats API.

    Args:
        spotify_track_id: Spotify track ID
        client_id: Ignored (kept for compatibility)
        client_secret: Ignored (kept for compatibility)

    Returns:
        Dictionary with audio features or None if track not found:
        {
            "danceability": float (0-1),
            "energy": float (0-1),
            "valence": float (0-1),
            "acousticness": float (0-1),
            "instrumentalness": float (0-1),
            "speechiness": float (0-1),
            "liveness": float (0-1),
            "tempo": float (BPM),
            "loudness": float (dB)
        }
    """
    return fetch_reccobeats_audio_features(spotify_track_id)
