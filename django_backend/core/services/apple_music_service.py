from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup
from core.utils.cache_utils import CachePrefix, cache_get, cache_set
from core.utils.helpers import get_logger

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
