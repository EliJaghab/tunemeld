import re
from typing import Optional
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials

from playlist_etl.mongo_db_client import MongoDBClient
from playlist_etl.utils import get_logger
from playlist_etl.config import (
    ISRC_CACHE_COLLECTION,
    YOUTUBE_CACHE_COLLECTION,
    APPLE_MUSIC_ALBUM_COVER_CACHE_COLLECTION,
)

logger = get_logger(__name__)


class CacheService:
    def __init__(self, mongo_client: MongoDBClient):
        self.mongo_client = mongo_client

    def get(self, collection_name: str, key: str):
        cache = self.mongo_client.read_cache(collection_name)
        return cache.get(key)

    def set(self, collection_name: str, key: str, value):
        logger.info(f"Updating cache in collection: {collection_name} for key: {key}")
        self.mongo_client.update_cache(collection_name, key, value)


class SpotifyService:
    def __init__(self, client_id: str, client_secret: str, cache_service: CacheService):
        if not client_id or not client_secret:
            raise ValueError("Spotify client ID or client secret not provided.")
        self.spotify_client = Spotify(
            client_credentials_manager=SpotifyClientCredentials(
                client_id=client_id, client_secret=client_secret
            )
        )
        self.cache_service = cache_service

    def get_isrc(self, track_name: str, artist_name: str) -> Optional[str]:
        cache_key = f"{track_name}|{artist_name}"
        isrc = self.cache_service.get(ISRC_CACHE_COLLECTION, cache_key)
        if isrc:
            logger.info(f"Cache hit for ISRC: {cache_key}")
            return isrc

        logger.info(f"ISRC Spotify Lookup Cache miss for {track_name} by {artist_name}")

        def search_spotify(query):
            try:
                results = self.spotify_client.search(q=query, type="track", limit=1)
                tracks = results["tracks"]["items"]
                if tracks:
                    return tracks[0]["external_ids"].get("isrc")
                return None
            except Exception as e:
                logger.info(f"Error searching Spotify with query '{query}': {e}")
                return None

        track_name_no_parens = re.sub(r"\([^()]*\)", "", track_name.lower())
        queries = [
            f"track:{track_name_no_parens} artist:{artist_name}",
            f"{track_name_no_parens} {artist_name}",
            f"track:{track_name.lower()} artist:{artist_name}",
        ]

        for query in queries:
            isrc = search_spotify(query)
            if isrc:
                logger.info(f"Found ISRC for {track_name} by {artist_name}: {isrc}")
                self.cache_service.set(ISRC_CACHE_COLLECTION, cache_key, isrc)
                return isrc

        logger.info(
            f"No track found on Spotify using queries: {queries} for {track_name} by {artist_name}"
        )
        return None


class YouTubeService:
    def __init__(self, api_key: str, cache_service: CacheService):
        if not api_key:
            raise ValueError("YouTube API key not provided.")
        self.api_key = api_key
        self.cache_service = cache_service

    def get_youtube_url(self, track_name: str, artist_name: str) -> Optional[str]:
        cache_key = f"{track_name}|{artist_name}"
        youtube_url = self.cache_service.get(YOUTUBE_CACHE_COLLECTION, cache_key)
        if youtube_url:
            logger.info(f"Cache hit for YouTube URL: {cache_key}")
            return youtube_url

        query = f"{track_name} {artist_name}"
        youtube_search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&key={self.api_key}"
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
                    self.cache_service.set(YOUTUBE_CACHE_COLLECTION, cache_key, youtube_url)
                    return youtube_url
            logger.info(f"No video found for {track_name} by {artist_name}")
            return None
        else:
            logger.info(f"Error fetching YouTube URL: {response.status_code}, {response.text}")
            if response.status_code == 403 and "quotaExceeded" in response.text:
                raise ValueError(f"Could not get YouTube URL for {track_name} {artist_name}")
            return None


class AppleMusicService:
    def __init__(self, cache_service: CacheService):
        self.cache_service = cache_service

    def get_album_cover_url(self, track_url: str) -> Optional[str]:
        cache_key = track_url
        album_cover_url = self.cache_service.get(APPLE_MUSIC_ALBUM_COVER_CACHE_COLLECTION, cache_key)
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
            self.cache_service.set(APPLE_MUSIC_ALBUM_COVER_CACHE_COLLECTION, cache_key, album_cover_url)
            return album_cover_url
        except Exception as e:
            logger.info(f"Error fetching album cover URL: {e}")
            return None
