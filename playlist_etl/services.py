import re
from typing import Optional
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup
from spotipy import Spotify
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials
from tenacity import retry, stop_after_attempt, wait_exponential

from playlist_etl.helpers import get_logger
from playlist_etl.utils import CacheManager

SPOTIFY_ERROR_THRESHOLD = 5

logger = get_logger(__name__)


class SpotifyService:
    def __init__(self, client_id: str, client_secret: str, isrc_cache_manager: CacheManager):
        if not client_id or not client_secret:
            raise ValueError("Spotify client ID or client secret not provided.")
        self.spotify_client = Spotify(
            client_credentials_manager=SpotifyClientCredentials(
                client_id=client_id, client_secret=client_secret
            )
        )
        self.isrc_cache_manager = isrc_cache_manager
        self.error_count = 0

    def get_isrc(self, track_name: str, artist_name: str) -> Optional[str]:
        cache_key = f"{track_name}|{artist_name}"
        isrc = self.isrc_cache_manager.get(cache_key)
        if isrc:
            logger.info(f"Cache hit for ISRC: {cache_key}")
            return isrc

        logger.info(f"ISRC Spotify Lookup Cache miss for {track_name} by {artist_name}")

        track_name_no_parens = self._get_track_name_with_no_parens(track_name)
        queries = [
            f"track:{track_name_no_parens} artist:{artist_name}",
            f"{track_name_no_parens} {artist_name}",
            f"track:{track_name.lower()} artist:{artist_name}",
        ]

        for query in queries:
            isrc = self._get_isrc(query)
            if isrc:
                logger.info(f"Found ISRC for {track_name} by {artist_name}: {isrc}")
                self.isrc_cache_manager.set(cache_key, isrc)
                return isrc

        logger.info(
            f"No track found on Spotify using queries: {queries} for {track_name} by {artist_name}"
        )
        return None

    def _get_track_name_with_no_parens(self, track_name: str) -> str:
        return re.sub(r"\([^()]*\)", "", track_name.lower())

    def _get_isrc(self, query: str) -> str | None:
        try:
            results = self.spotify_client.search(q=query, type="track", limit=1)
            tracks = results["tracks"]["items"]
            if tracks:
                return tracks[0]["external_ids"].get("isrc")
            return None
        except Exception as e:
            logger.info(f"Error searching Spotify with query '{query}': {e}")
            return None

    def get_track_url_by_isrc(self, isrc: str) -> str:
        track_url = self._get_track_url_by_isrc(isrc)
        if not track_url:
            logger.error(f"Failed to find track URL for ISRC: {isrc} after multiple attempts")
        return track_url

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(5), reraise=True
    )
    def _get_track_url_by_isrc(self, isrc: str) -> str:
        try:
            results = self.spotify_client.search(q=f"isrc:{isrc}", type="track", limit=1)
            if results["tracks"]["items"]:
                return results["tracks"]["items"][0]["external_urls"]["spotify"]
            else:
                return ""
        except SpotifyException as e:
            logger.error(f"SpotifyException: {e}")
            raise


class YouTubeService:
    def __init__(self, api_key: str, cache_manager: CacheManager):
        if not api_key:
            raise ValueError("YouTube API key not provided.")
        self.api_key = api_key
        self.cache_service = cache_manager

    def get_youtube_url(self, track_name: str, artist_name: str) -> Optional[str]:
        cache_key = f"{track_name}|{artist_name}"
        youtube_url = self.cache_service.get(cache_key)
        if youtube_url:
            logger.info(f"Cache hit for YouTube URL: {cache_key}")
            return youtube_url

        youtube_search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={cache_key}&key={self.api_key}"
        response = requests.get(youtube_search_url)

        if response.status_code == 200:
            data = response.json()
            if data.get("items"):
                video_id = data["items"][0]["id"].get("videoId")
                if video_id:
                    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                    logger.info(
                        f"Found YouTube URL for {track_name} by {artist_name}: {youtube_url}"
                    )
                    self.cache_service.set(cache_key, youtube_url)
                    return youtube_url
            logger.info(f"No video found for {track_name} by {artist_name}")
            return None
        else:
            logger.info(f"Error fetching YouTube URL: {response.status_code}, {response.text}")
            if response.status_code == 403 and "quotaExceeded" in response.text:
                raise ValueError(
                    f"Could not get YouTube URL for {track_name} {artist_name} because Quota Exceeded"
                )
            return None

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3), reraise=True
    )
    def get_youtube_track_view_count(self, youtube_url: str) -> int:
        video_id = youtube_url.split("v=")[-1]

        youtube_api_url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={video_id}&key={self.api_key}"

        try:
            response = requests.get(youtube_api_url)
            response.raise_for_status()

            data = response.json()
            if data["items"]:
                view_count = data["items"][0]["statistics"]["viewCount"]
                logger.info(f"Video ID {video_id} has {view_count} views.")
                return int(view_count)

        except Exception as e:
            logger.exception(f"An unexpected error occurred: {e}")
            raise ValueError(f"Unexpected error occurred for {youtube_url}: {e}")


class AppleMusicService:
    def __init__(self, cache_service: CacheManager):
        self.cache_service = cache_service

    def get_album_cover_url(self, track_url: str) -> Optional[str]:
        cache_key = track_url
        album_cover_url = self.cache_service.get(cache_key)
        if album_cover_url:
            logger.info(f"Cache hit for Apple Music Album Cover URL: {cache_key}")
            return album_cover_url

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
            self.cache_service.set(cache_key, album_cover_url)
            return album_cover_url
        except Exception as e:
            logger.info(f"Error fetching album cover URL: {e}")
            return None
