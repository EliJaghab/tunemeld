import concurrent.futures
import os
import re
from urllib.parse import unquote
from collections import defaultdict

import requests
from bs4 import BeautifulSoup

from playlist_etl.extract import PLAYLIST_GENRES, SERVICE_CONFIGS
from playlist_etl.utils import (
    get_logger,
    get_mongo_client,
    get_spotify_client,
    overwrite_kv_collection,
    read_cache_from_mongo,
    read_data_from_mongo,
    set_secrets,
    update_cache_in_mongo,
)

RAW_PLAYLISTS_COLLECTION = "raw_playlists"
TRACK_COLLECTION = "track"
TRACK_PLAYLIST_COLLECTION = "track_playlist"
YOUTUBE_CACHE_COLLECTION = "youtube_cache"
ISRC_CACHE_COLLECTION = "isrc_cache"
APPLE_MUSIC_ALBUM_COVER_CACHE_COLLECTION = "apple_music_album_cover_cache"

MAX_THREADS = 50

logger = get_logger(__name__)

class Track:
    def __init__(
        self,
        track_name: str,
        artist_name: str,
        track_url: str,
        rank: int,
        service_name: str,
        genre_name: str,
        album_cover_url: str | None = None,
        isrc: str | None = None,
    ):
        self.isrc = isrc
        self.track_name = track_name
        self.artist_name = artist_name
        self.track_url = track_url
        self.album_cover_url = album_cover_url
        self.rank = rank
        self.service_name = service_name
        self.genre_name = genre_name
        self.youtube_url: str | None = None

    def to_dict(self) -> dict:
        return self.__dict__

    @staticmethod
    def from_dict(data: dict) -> "Track":
        return Track(**data)

    def set_isrc(self, spotify_client, mongo_client):
        if not self.isrc:
            self.isrc = get_isrc_from_spotify_api(
                self.track_name, self.artist_name, spotify_client, mongo_client
            )

    def set_youtube_url(self, mongo_client):
        if not self.youtube_url:
            self.youtube_url = get_youtube_url_by_track_and_artist_name(
                self.track_name, self.artist_name, mongo_client
            )

    def set_apple_music_album_cover_url(self, mongo_client):
        if not self.album_cover_url:
            self.album_cover_url = get_apple_music_album_cover(self.track_url, mongo_client)

def get_isrc_from_spotify_api(track_name, artist_name, spotify_client, mongo_client):
    cache_key = f"{track_name}|{artist_name}"
    isrc_cache = read_cache_from_mongo(mongo_client, ISRC_CACHE_COLLECTION)

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
            update_cache_in_mongo(mongo_client, ISRC_CACHE_COLLECTION, cache_key, isrc)
            return isrc

    logger.info(
        f"No track found on Spotify using queries: {queries} for {track_name} by {artist_name}"
    )
    return None


def get_youtube_url_by_track_and_artist_name(track_name, artist_name, mongo_client):
    cache_key = f"{track_name}|{artist_name}"
    youtube_cache = read_cache_from_mongo(mongo_client, YOUTUBE_CACHE_COLLECTION)

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
                update_cache_in_mongo(
                    mongo_client, YOUTUBE_CACHE_COLLECTION, cache_key, youtube_url
                )
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
    album_cover_cache = read_cache_from_mongo(
        mongo_client, APPLE_MUSIC_ALBUM_COVER_CACHE_COLLECTION
    )

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
    update_cache_in_mongo(
        mongo_client,
        APPLE_MUSIC_ALBUM_COVER_CACHE_COLLECTION,
        cache_key,
        album_cover_url,
    )
    return album_cover_url
    
    

class Transform:
    def __init__(self):
        set_secrets()
        self.mongo_client = get_mongo_client()
        self.spotify_client = get_spotify_client()

    def get_isrc_from_spotify_api(self, track_name: str, artist_name: str) -> str | None:
        cache_key = f"{track_name}|{artist_name}"
        isrc_cache = read_cache_from_mongo(self.mongo_client, ISRC_CACHE_COLLECTION)

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
                update_cache_in_mongo(self.mongo_client, ISRC_CACHE_COLLECTION, cache_key, isrc)
                return isrc

        logger.info(
            f"No track found on Spotify using queries: {queries} for {track_name} by {artist_name}"
        )
        return None

    def get_youtube_url_by_track_and_artist_name(self, track_name: str, artist_name: str) -> str | None:
        cache_key = f"{track_name}|{artist_name}"
        youtube_cache = read_cache_from_mongo(self.mongo_client, YOUTUBE_CACHE_COLLECTION)

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
                    update_cache_in_mongo(
                        self.mongo_client, YOUTUBE_CACHE_COLLECTION, cache_key, youtube_url
                    )
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
        album_cover_cache = read_cache_from_mongo(
            self.mongo_client, APPLE_MUSIC_ALBUM_COVER_CACHE_COLLECTION
        )

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
        update_cache_in_mongo(
            self.mongo_client,
            APPLE_MUSIC_ALBUM_COVER_CACHE_COLLECTION,
            cache_key,
            album_cover_url,
        )
        return album_cover_url

    def convert_to_track_objects(self, data: dict, service_name: str, genre_name: str) -> list[Track]:
        logger.info(f"Converting data to track objects for {service_name} and genre {genre_name}")
        match service_name:
            case "AppleMusic":
                return self.convert_apple_music_raw_export_to_track_type(data, genre_name)
            case "Spotify":
                return self.convert_spotify_raw_export_to_track_type(data, genre_name)
            case "SoundCloud":
                return self.convert_soundcloud_raw_export_to_track_type(data, genre_name)
            case _:
                raise ValueError("Unknown service name")

    def convert_apple_music_raw_export_to_track_type(self, data: dict, genre_name: str) -> list[Track]:
        logger.info(f"Converting Apple Music data for genre {genre_name}")
        tracks = []
        print(data.keys())
        for key, track_data in data["album_details"].items():
            if key.isdigit():
                rank = int(key) + 1
                track_name = track_data["name"]
                artist_name = track_data["artist"]
                track_url = track_data["link"]
                track = Track(track_name, artist_name, track_url, rank, "AppleMusic", genre_name)
                tracks.append(track)
        return tracks

    def convert_soundcloud_raw_export_to_track_type(self, data: dict, genre_name: str) -> list[Track]:
        logger.info(f"Converting SoundCloud data for genre {genre_name}")
        tracks = []
        for i, item in enumerate(data["tracks"]["items"]):
            track_name = item["title"]
            track_url = item["permalink"]
            rank = i + 1
            artist_name = item["user"]["name"]
            album_cover_url = item["artworkUrl"]
            isrc = item["publisher"]["isrc"]

            if " - " in track_name:
                artist_name, track_name = track_name.split(" - ", 1)
            track = Track(
                track_name,
                artist_name,
                track_url,
                rank,
                "SoundCloud",
                genre_name,
                album_cover_url,
                isrc,
            )
            tracks.append(track)
        return tracks

    def convert_spotify_raw_export_to_track_type(self, data: dict, genre_name: str) -> list[Track]:
        logger.info(f"Converting Spotify data for genre {genre_name}")
        tracks = []
        for rank, item in enumerate(data["items"]):
            track_info = item["track"]

            if not track_info:
                continue

            isrc = track_info["external_ids"]["isrc"]
            track_name = track_info["name"]
            track_url = track_info["external_urls"]["spotify"]
            artist_name = ", ".join(artist["name"] for artist in track_info["artists"])
            album_cover_url = track_info["album"]["images"][0]["url"]
            track = Track(
                track_name,
                artist_name,
                track_url,
                rank + 1,
                "Spotify",
                genre_name,
                album_cover_url,
                isrc,
            )
            tracks.append(track)
        return tracks

    def get_all_track_objects(self) -> list[Track]:
        logger.info("Reading raw playlists from MongoDB")
        raw_playlists = read_data_from_mongo(self.mongo_client, RAW_PLAYLISTS_COLLECTION)
        logger.info(f"Found playlists from MongoDB: {len(raw_playlists)} documents found")

        all_tracks = []
        for playlist_data in raw_playlists:
            genre_name = playlist_data["genre_name"]
            service_name = playlist_data["service_name"]
            logger.info(f"Processing playlist for genre {genre_name} from {service_name}")
            tracks = self.convert_to_track_objects(playlist_data["data_json"], service_name, genre_name)
            logger.info(f"Converted {len(tracks)} tracks for {service_name} in genre {genre_name}")
            all_tracks.extend(tracks)

        return all_tracks

    def set_isrc_from_spotify_for_all_tracks(self, all_tracks: list[Track]):
        logger.info("Setting ISRCs for all tracks")
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [
                executor.submit(track.set_isrc, self.spotify_client, self.mongo_client)
                for track in all_tracks
            ]
            concurrent.futures.wait(futures)

    def set_youtube_url_for_all_tracks(self, all_tracks: list[Track]):
        logger.info("Setting YouTube URLs for all tracks")
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            futures = [executor.submit(track.set_youtube_url, self.mongo_client) for track in all_tracks]
            concurrent.futures.wait(futures)

    def set_apple_music_album_cover_url_for_all_tracks(self, all_tracks: list[Track]):
        logger.info("Setting Apple Music album cover URLs for all tracks")
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [
                executor.submit(track.set_apple_music_album_cover_url, self.mongo_client)
                for track in all_tracks
                if track.service_name == "AppleMusic"
            ]
            concurrent.futures.wait(futures)

    def get_track_ranking_from_playlist(self, all_tracks: list[Track]) -> dict[tuple[str, str], list[str]]:
        playlist_to_isrc = defaultdict(list)
        for track in sorted(all_tracks, key=lambda t: (t["service_name"], t["genre_name"], t["rank"])):
            key = f"{track['service_name']}_{track['genre_name']}"
            playlist_to_isrc[key].append(track["isrc"])
        return playlist_to_isrc

    def build_track_collection(self) -> list[dict]:
        all_tracks = self.get_all_track_objects()
        self.set_isrc_from_spotify_for_all_tracks(all_tracks)
        self.set_youtube_url_for_all_tracks(all_tracks)
        self.set_apple_music_album_cover_url_for_all_tracks(all_tracks)
        return [track.to_dict() for track in all_tracks]

if __name__ == "__main__":
    transform = Transform()
    #tracks = transform.build_track_collection()
    #overwrite_collection(transform.mongo_client, TRACK_COLLECTION, tracks)
    tracks_collection = read_data_from_mongo(transform.mongo_client, TRACK_COLLECTION)
    playlist_to_track = transform.get_track_ranking_from_playlist(tracks_collection)
    overwrite_kv_collection(transform.mongo_client, TRACK_PLAYLIST_COLLECTION, playlist_to_track)
