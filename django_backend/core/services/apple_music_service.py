import html
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup
from core.models.playlist_types import PlaylistData, PlaylistMetadata
from core.utils.cache_utils import CachePrefix, cache_get, cache_set
from core.utils.utils import get_logger
from core.utils.webdriver import WebDriverManager
from unidecode import unidecode

logger = get_logger(__name__)


def get_apple_music_album_cover_url(track_url: str) -> str | None:
    album_cover_url = cache_get(CachePrefix.APPLE_COVER, track_url)
    if album_cover_url:
        return str(album_cover_url)

    logger.info(f"Apple Music Album Cover Cache miss for URL: {track_url}")
    try:
        response = requests.get(track_url, timeout=30)
        response.raise_for_status()
        doc = BeautifulSoup(response.text, "html.parser")

        source_tag = doc.find("source", attrs={"type": "image/jpeg"})
        if not source_tag or not source_tag.has_attr("srcset"):
            raise ValueError("Album cover URL not found")

        srcset = source_tag["srcset"]
        album_cover_url = unquote(srcset.split()[0])
        cache_set(CachePrefix.APPLE_COVER, track_url, album_cover_url)
        return album_cover_url
    except Exception as e:
        logger.info(f"Error fetching album cover URL: {e}")
        return None


def _get_apple_music_cover_url(webdriver_manager, url: str, genre: str) -> str | None:
    """Get Apple Music playlist cover URL using WebDriver"""
    xpath = "//amp-ambient-video"
    src_attribute = webdriver_manager.find_element_by_xpath(url, xpath, attribute="src")

    if src_attribute is None or src_attribute == "Element not found" or "An error occurred" in src_attribute:
        raise ValueError(f"Could not find amp-ambient-video src attribute for Apple Music {genre}")

    if src_attribute.endswith(".m3u8"):
        return src_attribute
    else:
        raise ValueError(f"Found src attribute, but it's not an m3u8 URL: {src_attribute}")


def get_apple_music_playlist(genre: str) -> PlaylistData:
    """Get Apple Music playlist data and metadata for a given genre"""
    from playlist_etl.constants import SERVICE_CONFIGS
    from playlist_etl.rapid_api_client import fetch_playlist_data

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
    playlist_cover_url = None
    webdriver_manager = WebDriverManager()
    try:
        playlist_cover_url = _get_apple_music_cover_url(webdriver_manager, url, genre)
        logger.info(f"Successfully extracted Apple Music cover URL for {genre}")
    except Exception as e:
        logger.warning(f"WebDriver extraction failed for Apple Music {genre}: {e}")
        playlist_cover_url = None
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
