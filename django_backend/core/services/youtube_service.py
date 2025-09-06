import os

import requests
from core.utils.cache_utils import CachePrefix, cache_get, cache_set
from core.utils.utils import get_logger
from tenacity import retry, stop_after_attempt, wait_exponential

logger = get_logger(__name__)


def get_youtube_url(track_name: str, artist_name: str, api_key: str | None = None) -> str | None:
    api_key = api_key or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("YouTube API key not provided.")

    key_data = f"{track_name}|{artist_name}"
    youtube_url = cache_get(CachePrefix.YOUTUBE_URL, key_data)
    if youtube_url:
        return str(youtube_url)

    query = f"{track_name} {artist_name}"
    youtube_search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&key={api_key}"

    response = requests.get(youtube_search_url)
    if response.status_code == 200:
        data = response.json()
        if data.get("items"):
            video_id = data["items"][0]["id"].get("videoId")
            if video_id:
                youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                logger.info(f"Found YouTube URL for {track_name} by {artist_name}: {youtube_url}")
                cache_set(CachePrefix.YOUTUBE_URL, key_data, youtube_url)
                return youtube_url
        logger.info(f"No video found for {track_name} by {artist_name}")
        return None
    else:
        logger.info(f"Error fetching YouTube URL: {response.status_code}, {response.text}")
        if response.status_code == 403 and "quotaExceeded" in response.text:
            logger.warning(
                f"YouTube quota exceeded for {track_name} by {artist_name} - returning placeholder (not cached)"
            )
            return "https://youtube.com"  # Temporary placeholder - NOT cached so tomorrow's run will retry
        return None


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(3),
    reraise=True,
)
def get_youtube_track_view_count(youtube_url: str, api_key: str | None = None) -> int:
    api_key = api_key or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("YouTube API key not provided.")

    video_id = youtube_url.split("v=")[-1]
    youtube_api_url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={video_id}&key={api_key}"

    try:
        response = requests.get(youtube_api_url)
        response.raise_for_status()

        data = response.json()
        if data["items"]:
            view_count = data["items"][0]["statistics"]["viewCount"]
            logger.info(f"Video ID {video_id} has {view_count} views.")
            return int(view_count)
        else:
            logger.error(f"No video found for ID {video_id}")
            return 0

    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        raise ValueError(f"Unexpected error occurred for {youtube_url}: {e}") from e
