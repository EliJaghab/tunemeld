import re
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup
from spotipy import Spotify
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials
from tenacity import retry, stop_after_attempt, wait_exponential

from playlist_etl.cache_utils import CachePrefix, cache_get, cache_set
from playlist_etl.config import CURRENT_TIMESTAMP
from playlist_etl.helpers import get_logger
from playlist_etl.models import HistoricalView, Track
from playlist_etl.utils import WebDriverManager, get_delta_view_count

SPOTIFY_ERROR_THRESHOLD = 5

logger = get_logger(__name__)


class SpotifyService:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        webdriver_manager: WebDriverManager,
    ):
        if not client_id or not client_secret:
            raise ValueError("Spotify client ID or client secret not provided.")
        self.spotify_client = Spotify(
            client_credentials_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        )
        self.webdriver_manager = webdriver_manager
        self.error_count = 0

    def get_isrc(self, track_name: str, artist_name: str) -> str | None:
        key_data = f"{track_name}|{artist_name}"
        isrc = cache_get(CachePrefix.SPOTIFY_ISRC, key_data)
        if isrc:
            return str(isrc)

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
                cache_set(CachePrefix.SPOTIFY_ISRC, key_data, isrc)
                return isrc

        logger.info(f"No track found on Spotify using queries: {queries} for {track_name} by {artist_name}")
        return None

    def _get_track_name_with_no_parens(self, track_name: str) -> str:
        return re.sub(r"\([^()]*\)", "", track_name.lower())

    def _get_isrc(self, query: str) -> str | None:
        try:
            results = self.spotify_client.search(q=query, type="track", limit=1)
            tracks = results["tracks"]["items"]
            if tracks:
                isrc_value = tracks[0]["external_ids"].get("isrc")
                return str(isrc_value) if isrc_value is not None else None
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
        wait=wait_exponential(multiplier=1, min=4, max=10),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def _get_track_url_by_isrc(self, isrc: str) -> str:
        try:
            results = self.spotify_client.search(q=f"isrc:{isrc}", type="track", limit=1)
            if results["tracks"]["items"]:
                spotify_url = results["tracks"]["items"][0]["external_urls"]["spotify"]
                return str(spotify_url)
            else:
                return ""
        except SpotifyException as e:
            logger.error(f"SpotifyException: {e}")
            raise

    def set_track_url(self, track: Track) -> bool:
        if not track.spotify_track_data.track_url:
            track_url = self.get_track_url_by_isrc(track.isrc)
            if track_url is None:
                return False
            track.spotify_track_data.track_url = track_url
        return True

    def update_view_count(self, track: Track) -> bool:
        def _update_view_count(track: Track) -> bool:
            start_view_count_update = _set_start_view_count(track)
            current_view_count_update = _set_current_view_count(track)
            if start_view_count_update or current_view_count_update:
                _set_historical_view_count(track)
                return True
            return False

        def _set_start_view_count(track: Track) -> bool:
            if track.spotify_view.start_view.timestamp is not None:
                return False

            view_count = _get_track_view_count(track)
            if view_count is None:
                return False

            track.spotify_view.start_view.view_count = view_count
            track.spotify_view.start_view.timestamp = CURRENT_TIMESTAMP
            return True

        def _get_track_view_count(track: Track) -> int | None:
            track_url = track.spotify_track_data.track_url
            if track_url is None:
                logger.error(f"No Spotify track URL for {track.isrc}")
                return None
            try:
                return self.webdriver_manager.get_spotify_track_view_count(track_url)
            except Exception as e:
                logger.error(f"Error getting Spotify view count for {track.isrc} {track_url}: {e}")
                return None

        def _set_current_view_count(track: Track) -> bool:
            view_count = _get_track_view_count(track)
            if view_count is None:
                return False

            track.spotify_view.current_view.view_count = view_count
            track.spotify_view.current_view.timestamp = CURRENT_TIMESTAMP
            return True

        def _set_historical_view_count(track: Track) -> bool:
            historical_view = HistoricalView()
            current_view_count = track.spotify_view.current_view.view_count
            if current_view_count is None:
                return False
            historical_view.total_view_count = current_view_count
            delta_view_count = get_delta_view_count(
                track.spotify_view.historical_view,
                current_view_count,
            )
            historical_view.delta_view_count = delta_view_count
            historical_view.timestamp = CURRENT_TIMESTAMP
            track.spotify_view.historical_view.append(historical_view)
            return True

        return _update_view_count(track)


class YouTubeService:
    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("YouTube API key not provided.")
        self.api_key = api_key

    def set_track_url(self, track: Track) -> bool:
        if not track.youtube_url:
            track_name = (
                track.spotify_track_data.track_name
                or track.soundcloud_track_data.track_name
                or track.apple_music_track_data.track_name
            )
            artist_name = (
                track.spotify_track_data.artist_name
                or track.soundcloud_track_data.artist_name
                or track.apple_music_track_data.artist_name
            )
            if not track_name or not artist_name:
                return False

            track_url = self.get_youtube_url(track_name, artist_name)
            if track_url is None:
                return False

            track.youtube_url = track_url

        return True

    def get_youtube_url(self, track_name: str, artist_name: str) -> str | None:
        key_data = f"{track_name}|{artist_name}"
        youtube_url = cache_get(CachePrefix.YOUTUBE_URL, key_data)
        if youtube_url:
            return str(youtube_url)

        query = f"{track_name} {artist_name}"
        youtube_search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&key={self.api_key}"
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
                raise ValueError(f"Could not get YouTube URL for {track_name} {artist_name} because Quota Exceeded")
            return None

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def get_youtube_track_view_count(self, youtube_url: str) -> int:
        video_id = youtube_url.split("v=")[-1]

        youtube_api_url = (
            f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={video_id}&key={self.api_key}"
        )

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

    def update_view_count(self, track: Track) -> bool:
        def _update_view_count(track: Track) -> bool:
            start_view_count_update = _set_start_view_count(track)
            current_view_count_update = _set_current_view_count(track)
            if start_view_count_update or current_view_count_update:
                _set_historical_view_count(track)
                return True
            return False

        def _set_start_view_count(track: Track) -> bool:
            if track.youtube_view.start_view.timestamp is not None:
                return False

            view_count = _get_track_view_count(track)
            if view_count is None:
                return False

            track.youtube_view.start_view.view_count = view_count
            track.youtube_view.start_view.timestamp = CURRENT_TIMESTAMP
            return True

        def _get_track_view_count(track: Track) -> int | None:
            track_url = track.youtube_url
            if track_url is None:
                logger.error(f"No YouTube URL for {track.isrc}")
                return None
            try:
                return self.get_youtube_track_view_count(track_url)
            except Exception as e:
                logger.error(f"Error getting Youtube view count for {track.isrc} {track_url}: {e}")
                return None

        def _set_current_view_count(track: Track) -> bool:
            view_count = _get_track_view_count(track)
            if view_count is None:
                return False

            track.youtube_view.current_view.view_count = view_count
            track.youtube_view.current_view.timestamp = CURRENT_TIMESTAMP
            return True

        def _set_historical_view_count(track: Track) -> bool:
            historical_view = HistoricalView()
            current_view_count = track.youtube_view.current_view.view_count
            if current_view_count is None:
                return False
            historical_view.total_view_count = current_view_count
            delta_view_count = get_delta_view_count(
                track.youtube_view.historical_view,
                current_view_count,
            )
            historical_view.delta_view_count = delta_view_count
            historical_view.timestamp = CURRENT_TIMESTAMP
            track.youtube_view.historical_view.append(historical_view)
            return True

        return _update_view_count(track)


class AppleMusicService:
    def __init__(self):
        pass

    def get_album_cover_url(self, track_url: str) -> str | None:
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
