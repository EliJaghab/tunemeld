import concurrent.futures
import os
import re
from urllib.parse import unquote
from collections import defaultdict, Counter

import requests
from bs4 import BeautifulSoup

from playlist_etl.extract import PLAYLIST_GENRES, SERVICE_CONFIGS
from playlist_etl.utils import (
    get_logger,
    get_mongo_client,
    get_spotify_client,
    overwrite_collection,
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
        isrc: str,
        spotify_track_name: str | None = None,
        spotify_artist_name: str | None = None,
        spotify_track_url: str | None = None,
        soundcloud_track_name: str | None = None,
        soundcloud_artist_name: str | None = None,
        soundcloud_track_url: str | None = None,
        apple_music_track_name: str | None = None,
        apple_music_artist_name: str | None = None,
        apple_music_track_url: str | None = None,
        album_cover_url: str | None = None,
    ):
        self.spotify_track_name = spotify_track_name
        self.spotify_artist_name = spotify_artist_name
        self.spotify_track_url = spotify_track_url
        self.soundcloud_track_name = soundcloud_track_name
        self.soundcloud_artist_name = soundcloud_artist_name
        self.soundcloud_track_url = soundcloud_track_url
        self.apple_music_track_name = apple_music_track_name
        self.apple_music_artist_name = apple_music_artist_name
        self.apple_music_track_url = apple_music_track_url
        self.album_cover_url = album_cover_url
        self.isrc = isrc

    @staticmethod
    def from_dict(data: dict) -> "Track":
        return Track(**data)

    def set_youtube_url(self, mongo_client):
        if not self.youtube_url:
            self.youtube_url = get_youtube_url_by_track_and_artist_name(
                self.track_name, self.artist_name, mongo_client
            )

    def set_apple_music_album_cover_url(self, mongo_client):
        if not self.album_cover_url:
            self.album_cover_url = get_apple_music_album_cover(self.track_url, mongo_client)
    
    def to_dict(self) -> dict:
        return self.__dict__

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
        self.tracks = {}
        self.playlist_ranks = {}

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

    def convert_to_track_objects(self, data: dict, service_name: str, genre_name: str):
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

    def convert_apple_music_raw_export_to_track_type(self, data: dict, genre_name: str) -> list[Track]:
        logger.info(f"Converting Apple Music data for genre {genre_name}")
        isrc_rank_map = {}
        
        for key, track_data in data["album_details"].items():
            if key.isdigit():
                track_name = track_data["name"]
                artist_name = track_data["artist"]
                isrc = get_isrc_from_spotify_api(track_name, artist_name, self.spotify_client, self.mongo_client)
                
                track_url = track_data["link"]
                
                if isrc in self.tracks:
                    track.apple_music_track_name = track_name
                    track.apple_music_artist_name = artist_name
                    track.apple_music_track_url = track_url
                else:
                    track = Track(
                        isrc = isrc,
                        apple_music_track_name=track_name,
                        apple_music_artist_name=artist_name,
                        apple_music_track_url=track_url,
                    )                
                    self.tracks[isrc] = track
 
                isrc_rank_map[isrc] = int(key) + 1
            
        self.playlist_ranks[f"AppleMusic_{genre_name}"] = isrc_rank_map

    def convert_soundcloud_raw_export_to_track_type(self, data: dict, genre_name: str) -> list[Track]:
        logger.info(f"Converting SoundCloud data for genre {genre_name}")
        isrc_rank_map = {}
        
        for i, item in enumerate(data["tracks"]["items"]):
            isrc = item["publish"]
            track_name = item["title"]
            artist_name = item["user"]["name"]
            track_url = item["permalink"]
            album_cover_url = item["artworkUrl"]
            
            if " - " in track_name:
                artist_name, track_name = track_name.split(" - ", 1)
                
            if isrc in self.tracks:
                track.soundcloud_track_name = track_name
                track.soundcloud_artist_name = artist_name
                track.soundcloud_track_url = track_url
                track.album_cover_url = album_cover_url
                
            else:
                track = Track(
                    isrc = isrc,
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
            
            if isrc in self.tracks:
                track.spotify_track_name = track_name
                track.spotify_artist_name = artist_name
                track.spotify_track_url = track_url
                track.album_cover_url = album_cover_url
            else:
                track = Track(
                    isrc = isrc,
                    spotify_track_name=track_name,
                    spotify_artist_name=artist_name,
                    spotify_track_url=track_url,
                    album_cover_url=album_cover_url,
                )
                self.tracks[isrc] = track
                
            isrc_rank_map[isrc] = i + 1
        
        self.playlist_ranks[f"Spotify_{genre_name}"] = isrc_rank_map

    def build_track_objects(self):
        logger.info("Reading raw playlists from MongoDB")
        raw_playlists = read_data_from_mongo(self.mongo_client, RAW_PLAYLISTS_COLLECTION)
        logger.info(f"Found playlists from MongoDB: {len(raw_playlists)} documents found")
        
        for playlist_data in raw_playlists:
            genre_name = playlist_data["genre_name"]
            service_name = playlist_data["service_name"]
            logger.info(f"Processing playlist for genre {genre_name} from {service_name}")
            self.convert_to_track_objects(playlist_data["data_json"], service_name, genre_name)

    def set_youtube_url_for_all_tracks(self):
        logger.info("Setting YouTube URLs for all tracks")
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            futures = [executor.submit(track.set_youtube_url, self.mongo_client) for track in self.tracks.values()]
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

    def build_track_collection(self) -> list[dict]:
        self.get_all_track_objects()

        self.set_youtube_url_for_all_tracks(all_tracks)
        self.set_apple_music_album_cover_url_for_all_tracks(all_tracks)
        return {track.isrc: track.to_dict() for track in all_tracks}
class Aggregate:
    def __init__(self):
        set_secrets()
        self.mongo_client = get_mongo_client()
        self.playlist_to_track = read_data_from_mongo(self.mongo_client, TRACK_PLAYLIST_COLLECTION)
        self.track = read_data_from_mongo(self.mongo_client, TRACK_COLLECTION)
    
    def _get_genres(self) -> list[str]:
        genre_names = set()
        for playlist_name in self.playlist_to_track:
            genre_names.add(playlist_name.split("_")[1])
        return list(genre_names)

    def _aggregate_by_playlist_by_genre(self, genre_name: str) -> dict[str, list[str]]:
        genre_to_playlists = defaultdict(dict)
        genre_names = self._get_genres()
        for genre_name in genre_names:
            for playlist_name, playlist_tracks in self.playlist_to_track.items():
                if genre_name in playlist_name:
                    genre_to_playlists[genre_name][playlist_name] = playlist_tracks
        return genre_to_playlists

    def _get_matches_within_genre(self, playlists: dict[str, list[str]]) -> dict[str, list[str]]:
        candidates = defaultdict(list)
        for playlist_name, playlist_tracks in playlists.items():
            for isrc in playlist_tracks:
                candidates[isrc].append((playlist_name, )
        
        matches = 
            
        
        

        
        
    
    def _get_candidates(self) -> list[str]:
        counter = Counter()
        source_mapping = defaultdict(list)
        for playlist_name, isrc in self.playlist_to_track.items():
            counter[isrc] += 1
            source_mapping[isrc].append(playlist_name)
        
        candidates = [isrc for isrc, count in counter.items() if count > 1]
        isrc_to_service_names = {isrc: sources for isrc, sources in source_mapping.items() if isrc in candidates}
        return isrc_to_service_names

    def _get_track_rank(self, isrc: str, service_names: str) -> int:
        rank = None
        rank_priority = ["AppleMusic", "SoundCloud", "Spotify"]
        for service_name in rank_priority:
            if service_name in self.track:
                return self.track[isrc]["rank"]
        
        raise ValueError(f"Rank not found for {isrc} in {service_names}")

    def _get_source(self, isrc: str, service_names: str) -> str:
        source = None
        source_priority = ["SoundCloud", "AppleMusic", "Spotify"]
        for service_name in source_priority:
            if service_name in self.track:
                return service_name
        
        raise ValueError(f"Source not found for {isrc} in {service_names}")

    def build_aggregated_playlist(self, matched_tracks: dict[str, list[str]]) -> list[dict]:
        consolidated_tracks = []
        
        for isrc, service_names in matched_tracks.items():
            rank = self._get_track_rank(isrc, service_names)
            source = self.get_source(isrc, service_names)


if __name__ == "__main__":
    transform = Transform()
    tracks = transform.build_track_collection()
    overwrite_kv_collection(transform.mongo_client, TRACK_COLLECTION, tracks)
    tracks_collection = read_data_from_mongo(transform.mongo_client, TRACK_COLLECTION)
    playlist_to_track = transform.get_track_ranking_from_playlist(tracks_collection)
    overwrite_kv_collection(transform.mongo_client, TRACK_PLAYLIST_COLLECTION, playlist_to_track)
