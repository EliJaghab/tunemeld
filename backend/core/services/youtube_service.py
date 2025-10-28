import os
from enum import Enum
from urllib.parse import quote_plus

import requests
from core.utils.cloudflare_cache import CachePrefix, cloudflare_cache_get, cloudflare_cache_set
from core.utils.utils import get_logger
from tenacity import retry, stop_after_attempt, wait_exponential

logger = get_logger(__name__)


class YouTubeUrlResult(Enum):
    CACHE_HIT = "cache_hit"
    API_SUCCESS = "api_success"
    API_FAILURE_QUOTA = "api_failure_quota"
    API_FAILURE_NOT_FOUND = "api_failure_not_found"
    API_FAILURE_ERROR = "api_failure_error"


def get_youtube_url(
    track_name: str, artist_name: str, api_key: str | None = None
) -> tuple[str | None, YouTubeUrlResult]:
    api_key = api_key or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("YouTube API key not provided.")

    key_data = f"{track_name}|{artist_name}"
    youtube_url = cloudflare_cache_get(CachePrefix.YOUTUBE_URL, key_data)
    if youtube_url:
        return str(youtube_url), YouTubeUrlResult.CACHE_HIT

    query = f'"{track_name}" "{artist_name}"'
    youtube_search_url = (
        f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={quote_plus(query)}&type=video&key={api_key}"
    )

    response = requests.get(youtube_search_url)
    if response.status_code == 200:
        data = response.json()
        if data.get("items"):
            item = data["items"][0]
            video_id = item["id"].get("videoId")
            snippet_title = item.get("snippet", {}).get("title", "")

            if video_id and snippet_title:
                youtube_url = f"https://www.youtube.com/watch?v={video_id}"

                snippet_lower = snippet_title.lower()
                track_lower = track_name.lower()

                # Check if track name is in snippet
                track_match = track_lower in snippet_lower

                # For artist, split by comma and check if any artist name appears in snippet
                artist_names = [name.strip().lower() for name in artist_name.split(",")]
                artist_match = any(artist in snippet_lower for artist in artist_names if artist)

                if track_match or artist_match:
                    logger.info(f"Found YouTube URL for {track_name} by {artist_name}: {youtube_url}")
                    cloudflare_cache_set(CachePrefix.YOUTUBE_URL, key_data, youtube_url)
                    return youtube_url, YouTubeUrlResult.API_SUCCESS
                else:
                    logger.info(
                        f"YouTube result failed validation for {track_name} by {artist_name} "
                        f"(snippet: {snippet_title}), skipping"
                    )

        logger.info(f"No video found for {track_name} by {artist_name}")
        return None, YouTubeUrlResult.API_FAILURE_NOT_FOUND
    else:
        logger.info(f"Error fetching YouTube URL: {response.status_code}, {response.text}")
        if response.status_code == 403 and "quotaExceeded" in response.text:
            logger.warning(f"YouTube quota exceeded for {track_name} by {artist_name} - will retry later")
            return None, YouTubeUrlResult.API_FAILURE_QUOTA
        return None, YouTubeUrlResult.API_FAILURE_ERROR


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(3),
    reraise=True,
)
def get_youtube_track_view_count(youtube_url: str, api_key: str | None = None) -> int:
    """Get YouTube track view count. Returns 0 if API key missing or extraction fails."""
    api_key = api_key or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning(f"YouTube API key not provided for: {youtube_url}")
        return 0

    video_id = youtube_url.split("v=")[-1]

    cached_count = cloudflare_cache_get(CachePrefix.YOUTUBE_VIEW_COUNT, video_id)
    if cached_count:
        logger.info(f"Video ID {video_id} play count from cache: {cached_count}")
        return int(cached_count)

    youtube_api_url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={video_id}&key={api_key}"

    response = requests.get(youtube_api_url)
    response.raise_for_status()

    data = response.json()
    if data["items"]:
        view_count = data["items"][0]["statistics"]["viewCount"]
        logger.info(f"Video ID {video_id} has {view_count} views.")

        cloudflare_cache_set(CachePrefix.YOUTUBE_VIEW_COUNT, video_id, view_count)

        return int(view_count)
    else:
        raise ValueError("No video data found in YouTube API response")
