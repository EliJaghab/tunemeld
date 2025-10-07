import html
import re
import string
from enum import Enum
from typing import TYPE_CHECKING
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup, Tag

# ETL-only imports - conditionally imported to avoid Vercel serverless bloat
from django.conf import settings

if settings.ETL_DEPENDENCIES_AVAILABLE:
    from unidecode import unidecode
else:
    unidecode = None  # type: ignore

from tenacity import retry, stop_after_attempt, wait_exponential

if TYPE_CHECKING:
    from core.constants import GenreName
from core.constants import GENRE_CONFIGS, SERVICE_CONFIGS, ServiceName
from core.models.playlist import PlaylistData, PlaylistMetadata
from core.utils.cloudflare_cache import CachePrefix, cloudflare_cache_get, cloudflare_cache_set
from core.utils.rapid_api_client import fetch_playlist_data
from core.utils.utils import clean_unicode_text, get_logger

logger = get_logger(__name__)


class SoundCloudUrlResult(Enum):
    CACHE_HIT = "cache_hit"
    SCRAPE_SUCCESS = "scrape_success"
    SCRAPE_FAILURE_NOT_FOUND = "scrape_failure_not_found"
    SCRAPE_FAILURE_ERROR = "scrape_failure_error"


def get_soundcloud_playlist(genre: "GenreName", force_refresh: bool = False) -> PlaylistData:
    """Get SoundCloud playlist data and metadata for a given genre"""
    SERVICE_CONFIGS[ServiceName.SOUNDCLOUD.value]
    url = GENRE_CONFIGS[genre.value]["links"][ServiceName.SOUNDCLOUD.value]

    tracks_data = fetch_playlist_data(ServiceName.SOUNDCLOUD, genre, force_refresh)

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
        "service_name": ServiceName.SOUNDCLOUD.value,
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


@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), reraise=True)
def get_soundcloud_track_view_count(track_url: str) -> int:
    """Get SoundCloud track view count from meta tag."""
    logger.info(f"Accessing SoundCloud URL: {track_url}")
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )

    response = requests.get(
        track_url,
        headers={"User-Agent": user_agent},
        timeout=10,
    )
    response.raise_for_status()

    html_content = response.text

    # Look for meta tag - this is the most reliable method
    # <meta property="soundcloud:play_count" content="44561">
    meta_match = re.search(r'<meta\s+property="soundcloud:play_count"\s+content="(\d+)"', html_content)
    if meta_match:
        view_count = int(meta_match.group(1))
        logger.info(f"Found SoundCloud play count: {view_count:,}")
        return view_count

    # Fallback: Look for playback_count in JSON data if meta tag fails
    playback_match = re.search(r'"playback_count":\s*(\d+)', html_content)
    if playback_match:
        view_count = int(playback_match.group(1))
        logger.info(f"Found SoundCloud play count via JSON: {view_count:,}")
        return view_count

    raise ValueError(f"Could not extract play count from SoundCloud URL: {track_url}")


def _verify_soundcloud_track_page(url: str, expected_track_name: str, expected_artist_name: str) -> bool:
    """Visit the SoundCloud track page to verify it matches our expected track/artist."""
    try:
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )

        response = requests.get(url, headers={"User-Agent": user_agent}, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Get track title from og:title or page title
        og_title = soup.find("meta", {"property": "og:title"})
        page_title = soup.find("title")

        track_title = None
        if og_title and isinstance(og_title, Tag) and og_title.get("content"):
            track_title = str(og_title["content"]).strip()
        elif page_title and isinstance(page_title, Tag):
            track_title = page_title.get_text(strip=True)

        if not track_title:
            return False

        # Normalize for comparison
        actual_text = _normalize_text(track_title)
        actual_words = set(actual_text.split())

        # Must have good track name overlap AND some artist overlap
        track_words = set(_normalize_text(expected_track_name).split())

        # Get first artist (try comma first, then ampersand)
        first_artist = expected_artist_name
        if "," in expected_artist_name:
            first_artist = expected_artist_name.split(",")[0].strip()
        elif "&" in expected_artist_name:
            first_artist = expected_artist_name.split("&")[0].strip()

        artist_words = set(_normalize_text(first_artist).split())

        track_overlap = len(track_words.intersection(actual_words))
        artist_overlap = len(artist_words.intersection(actual_words))

        track_match = (track_overlap / len(track_words) * 100) if len(track_words) > 0 else 0
        artist_match = (artist_overlap / len(artist_words) * 100) if len(artist_words) > 0 else 0

        # Need 80% track match OR (60% track match AND 40% artist match)
        is_match = track_match >= 80.0 or (track_match >= 60.0 and artist_match >= 40.0)

        if is_match:
            logger.info(f"Verified track page: {track_title} (track: {track_match:.1f}%, artist: {artist_match:.1f}%)")
        else:
            logger.info(
                f"Page verification failed: {track_title} (track: {track_match:.1f}%, artist: {artist_match:.1f}%)"
            )

        return is_match

    except Exception as e:
        logger.warning(f"Failed to verify SoundCloud track page {url}: {e}")
        return False


def _normalize_text(text: str) -> str:
    """Normalize text for better matching by removing special chars and extra spaces."""
    # First fix common HTML encoding issues
    text = text.replace("Ã³", "o").replace("Ã¡", "a").replace("Ã©", "e").replace("Ã­", "i").replace("Ã±", "n")

    # Then decode HTML entities
    text = html.unescape(text)

    # Then convert Unicode to ASCII (ETL only)
    if unidecode is not None:
        text = unidecode(text)

    # Remove punctuation and normalize spaces
    normalized = "".join(c if c not in string.punctuation else " " for c in text.lower())
    # Replace multiple spaces with single space and strip
    return " ".join(normalized.split())


def get_soundcloud_url(track_name: str, artist_name: str) -> tuple[str | None, SoundCloudUrlResult]:
    """Find SoundCloud URL for a track by searching SoundCloud."""
    key_data = f"{track_name}|{artist_name}"
    cached_url = cloudflare_cache_get(CachePrefix.SOUNDCLOUD_URL, key_data)
    if cached_url:
        return str(cached_url), SoundCloudUrlResult.CACHE_HIT

    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )

    # Generate artist variations: full, first artist only
    artist_variations = [artist_name]

    # Try splitting on comma first
    if "," in artist_name:
        first_artist = artist_name.split(",")[0].strip()
        if first_artist not in artist_variations:
            artist_variations.append(first_artist)

    # Also try splitting on ampersand
    if "&" in artist_name:
        first_artist_ampersand = artist_name.split("&")[0].strip()
        if first_artist_ampersand not in artist_variations:
            artist_variations.append(first_artist_ampersand)

    # Try each artist variation
    for artist_variant in artist_variations:
        query = f"{artist_variant} {track_name}"
        search_url = f"https://soundcloud.com/search/sounds?q={quote_plus(query)}"

        try:
            logger.info(f"Searching SoundCloud: {query}")
            response = requests.get(search_url, headers={"User-Agent": user_agent}, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            track_links = soup.find_all("a", href=re.compile(r"^/[^/]+/[^/]+$"))

            # Check each result - take first few candidates and verify by visiting the page
            for link in track_links[:8]:  # Check first 8 results (skip navigation links)
                if not isinstance(link, Tag):
                    continue

                href = link.get("href")
                if href and isinstance(href, str) and not href.startswith(("http", "//")):
                    full_url = f"https://soundcloud.com{href}"

                    # Get the title for basic filtering
                    title_element = link.find("span") or link
                    if isinstance(title_element, Tag):
                        title_text = title_element.get_text(strip=True)

                        # Basic filtering: track name should have some overlap
                        track_words = set(_normalize_text(track_name).split())
                        title_words = set(_normalize_text(title_text).split())

                        if len(track_words) == 0:
                            continue

                        track_overlap = len(track_words.intersection(title_words))
                        track_match_percentage = (track_overlap / len(track_words)) * 100

                        # Basic 50% track name filter to avoid completely wrong tracks
                        if track_match_percentage >= 50.0 and _verify_soundcloud_track_page(
                            full_url, track_name, artist_name
                        ):
                            logger.info(f"Found SoundCloud URL for {track_name} by {artist_name}: {full_url}")
                            cloudflare_cache_set(CachePrefix.SOUNDCLOUD_URL, key_data, full_url)
                            return full_url, SoundCloudUrlResult.SCRAPE_SUCCESS

        except Exception as e:
            logger.warning(f"SoundCloud search failed for {track_name} by {artist_variant}: {e}")

    logger.info(f"No SoundCloud track found for {track_name} by {artist_name}")
    return None, SoundCloudUrlResult.SCRAPE_FAILURE_NOT_FOUND
