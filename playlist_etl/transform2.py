import concurrent.futures
import os
import re
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel

from playlist_etl.mongo_db_client import MongoDBClient
from playlist_etl.utils import get_logger, get_spotify_client, set_secrets

RAW_PLAYLISTS_COLLECTION = "raw_playlists"
TRACK_COLLECTION = "track"
TRACK_PLAYLIST_COLLECTION = "track_playlist"
YOUTUBE_CACHE_COLLECTION = "youtube_cache"
ISRC_CACHE_COLLECTION = "isrc_cache"
APPLE_MUSIC_ALBUM_COVER_CACHE_COLLECTION = "apple_music_album_cover_cache"

MAX_THREADS = 100

logger = get_logger(__name__)


class Track(BaseModel):
    isrc: str
    spotify_track_name: str | None = None
    spotify_artist_name: str | None = None
    spotify_track_url: str | None = None
    soundcloud_track_name: str | None = None
    soundcloud_artist_name: str | None = None
    soundcloud_track_url: str | None = None
    apple_music_track_name: str | None = None
    apple_music_artist_name: str | None = None
    apple_music_track_url: str | None = None
    album_cover_url: str | None = None

    def set_youtube_url(self, mongo_client):
        if not self.youtube_url:
            self.youtube_url = get_youtube_url_by_track_and_artist_name(
                self.track_name, self.artist_name, mongo_client
            )

    def set_apple_music_album_cover_url(self, mongo_client):
        if not self.album_cover_url:
            self.album_cover_url = get_apple_music_album_cover(self.track_url, mongo_client)

    def to_dict(self) -> dict:
        return self.dict()


class PlaylistRank(BaseModel):
    isrc: str
    rank: int


def get_isrc_from_spotify_api(track_name, artist_name, spotify_client, mongo_client):
    cache_key = f"{track_name}|{artist_name}"
    isrc_cache = mongo_client.read_cache(ISRC_CACHE_COLLECTION)

    if cache_key in isrc_cache:
        logger.info(f"Cache hit for ISRC: {cache_key}")
        return isrc_cache[cache_key]

    logger.info(f"ISRC Spotify Lookup Cache miss for {track_name} by {artist_name}")

    def search_spotify(query):
        try:
            results = spotify_client.search(q=query, type="track", limit=1)
            tracks = results["tracks"]["items"]
            if tracks:
                return tracks[0]["external_ids"]["isrc"]
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
            mongo_client.update_cache(ISRC_CACHE_COLLECTION, cache_key, isrc)
            return isrc

    logger.info(
        f"No track found on Spotify using queries: {queries} for {track_name} by {artist_name}"
    )
    return None


def get_youtube_url_by_track_and_artist_name(track_name, artist_name, mongo_client):
    cache_key = f"{track_name}|{artist_name}"
    youtube_cache = mongo_client.read_cache(YOUTUBE_CACHE_COLLECTION)

    if cache_key in youtube_cache:
        logger.info(f"Cache hit for ISRC: {cache_key}")
        return youtube_cache[cache_key]

    query = f"{track_name} {artist_name}"
    api_key = os.getenv("GOOGLE_API_KEY")

    youtube_search_url = (
        f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&key={api_key}"
    )
    response = requests.get(youtube_search_url)

    if response.status_code == 200:
        data = response.json()
        if data["items"]:
            video_id = data["items"][0]["id"].get("videoId")
            if video_id:
                youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                logger.info(
                    f"Updating YouTube cache for {track_name} by {artist_name} with URL {youtube_url}"
                )
                mongo_client.update_cache(YOUTUBE_CACHE_COLLECTION, cache_key, youtube_url)
                return youtube_url
        logger.info(f"No video found for {track_name} by {artist_name}")
        return None
    else:
        logger.info(f"Error: {response.status_code}, {response.text}")
        if response.status_code == 403 and "quotaExceeded" in response.text:
            raise ValueError(f"Could not get Youtube URL for {track_name} {artist_name}")
        return None


def get_apple_music_album_cover(url_link, mongo_client):
    cache_key = url_link
    album_cover_cache = mongo_client.read_cache(APPLE_MUSIC_ALBUM_COVER_CACHE_COLLECTION)

    if cache_key in album_cover_cache:
        return album_cover_cache[cache_key]

    logger.info(f"Apple Music Album Cover Cache miss for URL: {url_link}")
    response = requests.get(url_link, timeout=30)
    response.raise_for_status()
    doc = BeautifulSoup(response.text, "html.parser")

    source_tag = doc.find("source", attrs={"type": "image/jpeg"})
    if not source_tag or not source_tag.has_attr("srcset"):
        raise ValueError("Album cover URL not found")

    srcset = source_tag["srcset"]
    album_cover_url = unquote(srcset.split()[0])
    mongo_client.update_cache(
        APPLE_MUSIC_ALBUM_COVER_CACHE_COLLECTION,
        cache_key,
        album_cover_url,
    )
    return album_cover_url


class Transform:
    def __init__(self):
        set_secrets()
        self.mongo_client = MongoDBClient()
        self.spotify_client = get_spotify_client()
        self.tracks = {}
        self.playlist_ranks = {}

    def transform(self):
        self.build_track_objects()
        self.overwrite_data_to_mongo()

    def build_track_objects(self):
        logger.info("Reading raw playlists from MongoDB")
        raw_playlists = self.mongo_client.read_data(RAW_PLAYLISTS_COLLECTION)
        logger.info(f"Found playlists from MongoDB: {len(raw_playlists)} documents found")

        for playlist_data in raw_playlists:
            genre_name = playlist_data["genre_name"]
            if genre_name != "dance":
                continue
            service_name = playlist_data["service_name"]
            logger.info(f"Processing playlist for genre {genre_name} from {service_name}")
            self.convert_to_track_objects(playlist_data["data_json"], service_name, genre_name)
            self.set_youtube_url_for_all_tracks()
            self.set_apple_music_album_cover_url_for_all_tracks()

    def exclude_tracks_without_isrc(self):
        self.tracks = {isrc: track for isrc, track in self.tracks.items() if track.isrc is not None}
        for playlist in self.playlist_ranks:
            self.playlist_ranks[playlist] = {
                isrc: rank
                for isrc, rank in self.playlist_ranks[playlist].items()
                if isrc in self.tracks
            }

    def format_tracks(self):
        formatted_tracks = {
            isrc: track.to_dict() for isrc, track in self.tracks.items() if track.isrc is not None
        }
        return formatted_tracks

    def format_playlist_ranks(self):
        formatted_ranks = {
            playlist: [PlaylistRank(isrc=isrc, rank=rank).dict() for isrc, rank in ranks.items()]
            for playlist, ranks in self.playlist_ranks.items()
        }
        return formatted_ranks

    def overwrite_data_to_mongo(self):
        formatted_tracks = self.format_tracks()
        self.mongo_client.overwrite_kv_collection(TRACK_COLLECTION, formatted_tracks)
        print(self.playlist_ranks)
        formatted_ranks = self.format_playlist_ranks()
        self.mongo_client.overwrite_kv_collection(TRACK_PLAYLIST_COLLECTION, formatted_ranks)

    def get_isrc_from_spotify_api(self, track_name: str, artist_name: str) -> str | None:
        cache_key = f"{track_name}|{artist_name}"
        isrc_cache = self.mongo_client.read_cache(ISRC_CACHE_COLLECTION)

        if cache_key in isrc_cache:
            logger.info(f"Spotify cache hit for ISRC: {cache_key}")
            return isrc_cache[cache_key]

        logger.info(f"ISRC Spotify Lookup Cache miss for {track_name} by {artist_name}")

        def search_spotify(query: str) -> str | None:
            try:
                results = self.spotify_client.search(q=query, type="track", limit=1)
                tracks = results["tracks"]["items"]
                return tracks[0]["external_ids"]["isrc"] if tracks else None
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
                self.mongo_client.update_cache(ISRC_CACHE_COLLECTION, cache_key, isrc)
                return isrc

        logger.info(
            f"No track found on Spotify using queries: {queries} for {track_name} by {artist_name}"
        )
        return None

    def get_youtube_url_by_track_and_artist_name(
        self, track_name: str, artist_name: str
    ) -> str | None:
        cache_key = f"{track_name}|{artist_name}"
        youtube_cache = self.mongo_client.read_cache(YOUTUBE_CACHE_COLLECTION)

        if cache_key in youtube_cache:
            logger.info(f"Youtube cache hit for ISRC: {cache_key}")
            return youtube_cache[cache_key]

        query = f"{track_name} {artist_name}"
        api_key = os.getenv("GOOGLE_API_KEY")

        youtube_search_url = (
            f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&key={api_key}"
        )
        response = requests.get(youtube_search_url)

        if response.status_code == 200:
            data = response.json()
            if data["items"]:
                video_id = data["items"][0]["id"].get("videoId")
                if video_id:
                    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                    logger.info(
                        f"Updating YouTube cache for {track_name} by {artist_name} with URL {youtube_url}"
                    )
                    self.mongo_client.update_cache(YOUTUBE_CACHE_COLLECTION, cache_key, youtube_url)
                    return youtube_url
            logger.info(f"No video found for {track_name} by {artist_name}")
            return None
        else:
            logger.info(f"Error: {response.status_code}, {response.text}")
            if response.status_code == 403 and "quotaExceeded" in response.text:
                raise ValueError(f"Could not get Youtube URL for {track_name} {artist_name}")
            return None

    def get_apple_music_album_cover(self, url_link: str) -> str:
        cache_key = url_link
        album_cover_cache = self.mongo_client.read_cache(APPLE_MUSIC_ALBUM_COVER_CACHE_COLLECTION)

        if cache_key in album_cover_cache:
            return album_cover_cache[cache_key]

        logger.info(f"Apple Music Album Cover Cache miss for URL: {url_link}")
        response = requests.get(url_link, timeout=30)
        response.raise_for_status()
        doc = BeautifulSoup(response.text, "html.parser")

        source_tag = doc.find("source", attrs={"type": "image/jpeg"})
        if not source_tag or not source_tag.has_attr("srcset"):
            raise ValueError("Album cover URL not found")

        srcset = source_tag["srcset"]
        album_cover_url = unquote(srcset.split()[0])
        self.mongo_client.update_cache(
            APPLE_MUSIC_ALBUM_COVER_CACHE_COLLECTION,
            cache_key,
            album_cover_url,
        )
        return album_cover_url

    def convert_to_track_objects(self, data: dict, service_name: str, genre_name: str) -> None:
        logger.info(f"Converting data to track objects for {service_name} and genre {genre_name}")
        match service_name:
            case "AppleMusic":
                self.convert_apple_music_raw_export_to_track_type(data, genre_name)
            case "Spotify":
                self.convert_spotify_raw_export_to_track_type(data, genre_name)
            case "SoundCloud":
                self.convert_soundcloud_raw_export_to_track_type(data, genre_name)
            case _:
                raise ValueError("Unknown service name")

    def convert_apple_music_raw_export_to_track_type(
        self, data: dict, genre_name: str
    ) -> list[Track]:
        logger.info(f"Converting Apple Music data for genre {genre_name}")
        isrc_rank_map = {}

        for key, track_data in data["album_details"].items():
            if key.isdigit():
                track_name = track_data["name"]
                artist_name = track_data["artist"]
                isrc = get_isrc_from_spotify_api(
                    track_name, artist_name, self.spotify_client, self.mongo_client
                )

                if isrc is None:
                    continue

                track_url = track_data["link"]

                if isrc in self.tracks:
                    track.apple_music_track_name = track_name
                    track.apple_music_artist_name = artist_name
                    track.apple_music_track_url = track_url
                else:
                    track = Track(
                        isrc=isrc,
                        apple_music_track_name=track_name,
                        apple_music_artist_name=artist_name,
                        apple_music_track_url=track_url,
                    )
                    self.tracks[isrc] = track

                isrc_rank_map[isrc] = int(key) + 1

        self.playlist_ranks[f"AppleMusic_{genre_name}"] = isrc_rank_map

    def convert_soundcloud_raw_export_to_track_type(
        self, data: dict, genre_name: str
    ) -> list[Track]:
        logger.info(f"Converting SoundCloud data for genre {genre_name}")
        isrc_rank_map = {}

        for i, item in enumerate(data["tracks"]["items"]):
            isrc = item["publisher"]["isrc"]
            if isrc is None:
                continue
            track_name = item["title"]
            artist_name = item["user"]["name"]
            track_url = item["permalink"]
            album_cover_url = item["artworkUrl"]

            if " - " in track_name:
                artist_name, track_name = track_name.split(" - ", 1)

            if isrc in self.tracks:
                track = self.tracks[isrc]
                track.soundcloud_track_name = track_name
                track.soundcloud_artist_name = artist_name
                track.soundcloud_track_url = track_url
                track.album_cover_url = album_cover_url

            else:
                track = Track(
                    isrc=isrc,
                    soundcloud_track_name=track_name,
                    soundcloud_artist_name=artist_name,
                    soundcloud_track_url=track_url,
                    album_cover_url=album_cover_url,
                )
                self.tracks[isrc] = track

            isrc_rank_map[isrc] = i + 1

        self.playlist_ranks[f"SoundCloud_{genre_name}"] = isrc_rank_map

    def convert_spotify_raw_export_to_track_type(self, data: dict, genre_name: str) -> list[Track]:
        logger.info(f"Converting Spotify data for genre {genre_name}")
        isrc_rank_map = {}
        for i, item in enumerate(data["items"]):
            track_info = item["track"]

            if not track_info:
                continue

            track_name = track_info["name"]
            artist_name = ", ".join(artist["name"] for artist in track_info["artists"])
            track_url = track_info["external_urls"]["spotify"]
            album_cover_url = track_info["album"]["images"][0]["url"]
            isrc = track_info["external_ids"]["isrc"]

            if isrc is None:
                continue

            if isrc in self.tracks:
                track = self.tracks[isrc]
                track.spotify_track_name = track_name
                track.spotify_artist_name = artist_name
                track.spotify_track_url = track_url
                track.album_cover_url = album_cover_url
            else:
                track = Track(
                    isrc=isrc,
                    spotify_track_name=track_name,
                    spotify_artist_name=artist_name,
                    spotify_track_url=track_url,
                    album_cover_url=album_cover_url,
                )
                self.tracks[isrc] = track

            isrc_rank_map[isrc] = i + 1

        self.playlist_ranks[f"Spotify_{genre_name}"] = isrc_rank_map

    def set_youtube_url_for_all_tracks(self) -> None:
        logger.info("Setting YouTube URLs for all tracks")
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            futures = [
                executor.submit(track.set_youtube_url, self.mongo_client)
                for track in self.tracks.values()
            ]
            concurrent.futures.wait(futures)

    def set_apple_music_album_cover_url_for_all_tracks(self):
        logger.info("Setting Apple Music album cover URLs for all tracks")
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [
                executor.submit(track.set_apple_music_album_cover_url, self.mongo_client)
                for track in self.tracks.values()
                if not track.album_cover_url == "AppleMusic"
            ]
            concurrent.futures.wait(futures)


if __name__ == "__main__":
    transform = Transform()
    transform.transform()
