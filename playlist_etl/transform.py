import concurrent.futures
import os
import re
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup
from extract import PLAYLIST_GENRES, SERVICE_CONFIGS
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from utils import (
    clear_collection,
    get_mongo_client,
    insert_data_to_mongo,
    read_cache_from_mongo,
    read_data_from_mongo,
    set_secrets,
    update_cache_in_mongo,
)

RAW_PLAYLISTS_COLLECTION = "raw_playlists"
TRANSFORMED_DATA_COLLECTION = "transformed_playlists"
YOUTUBE_CACHE_COLLECTION = "youtube_cache"
ISRC_CACHE_COLLECTION = "isrc_cache"
APPLE_MUSIC_ALBUM_COVER_CACHE_COLLECTION = "apple_music_album_cover_cache"

MAX_THREADS = 50


class Track:
    def __init__(
        self,
        track_name,
        artist_name,
        track_url,
        rank,
        source_name,
        genre_name,
        album_cover_url=None,
        isrc=None,
    ):
        self.isrc = isrc
        self.track_name = track_name
        self.artist_name = artist_name
        self.track_url = track_url
        self.album_cover_url = album_cover_url
        self.rank = rank
        self.source_name = source_name
        self.genre_name = genre_name
        self.youtube_url = None

    def to_dict(self):
        return self.__dict__

    @staticmethod
    def from_dict(data):
        return Track(**data)

    def set_isrc(self, mongo_client):
        if not self.isrc:
            self.isrc = get_isrc_from_spotify_api(self.track_name, self.artist_name, mongo_client)

    def set_youtube_url(self, mongo_client):
        if not self.youtube_url:
            self.youtube_url = get_youtube_url_by_track_and_artist_name(
                self.track_name, self.artist_name, mongo_client
            )

    def set_apple_music_album_cover_url(self, mongo_client):
        if not self.album_cover_url:
            self.album_cover_url = get_apple_music_album_cover(self.track_url, mongo_client)


def convert_to_track_objects(data, service_name, genre_name):
    print(f"Converting data to track objects for {service_name} and genre {genre_name}")
    match service_name:
        case "AppleMusic":
            return convert_apple_music_raw_export_to_track_type(data, genre_name)
        case "Spotify":
            return convert_spotify_raw_export_to_track_type(data, genre_name)
        case "SoundCloud":
            return convert_soundcloud_raw_export_to_track_type(data, genre_name)
        case _:
            raise ValueError("Unknown service name")


def convert_apple_music_raw_export_to_track_type(data, genre_name):
    print(f"Converting Apple Music data for genre {genre_name}")
    tracks = []
    for key, track_data in data["album_details"].items():
        if key.isdigit():
            rank = int(key) + 1
            track_name = track_data["name"]
            artist_name = track_data["artist"]
            track_url = track_data["link"]
            track = Track(track_name, artist_name, track_url, rank, "AppleMusic", genre_name)
            tracks.append(track)
    return tracks


def convert_soundcloud_raw_export_to_track_type(data, genre_name):
    print(f"Converting SoundCloud data for genre {genre_name}")
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


def convert_spotify_raw_export_to_track_type(data, genre_name):
    print(f"Converting Spotify data for genre {genre_name}")
    tracks = []
    for rank, item in enumerate(data["items"]):
        track_info = item["track"]
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


def get_isrc_from_spotify_api(track_name, artist_name, mongo_client):
    cache_key = f"{track_name}|{artist_name}"
    isrc_cache = read_cache_from_mongo(mongo_client, ISRC_CACHE_COLLECTION)

    if cache_key in isrc_cache:
        print(f"Cache hit for ISRC: {cache_key}")
        return isrc_cache[cache_key]

    print(f"ISRC Spotify Lookup Cache miss for {track_name} by {artist_name}")
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError("Spotify client ID or client secret not found.")

    spotify = Spotify(
        client_credentials_manager=SpotifyClientCredentials(
            client_id=client_id, client_secret=client_secret
        )
    )

    def search_spotify(query):
        try:
            results = spotify.search(q=query, type="track", limit=1)
            tracks = results["tracks"]["items"]
            if tracks:
                return tracks[0]["external_ids"]["isrc"]
            return None
        except Exception as e:
            print(f"Error searching Spotify with query '{query}': {e}")
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
            print(f"Found ISRC for {track_name} by {artist_name}: {isrc}")
            update_cache_in_mongo(mongo_client, ISRC_CACHE_COLLECTION, cache_key, isrc)
            return isrc

    print(f"No track found on Spotify using queries: {queries} for {track_name} by {artist_name}")
    return None


def get_youtube_url_by_track_and_artist_name(track_name, artist_name, mongo_client):
    cache_key = f"{track_name}|{artist_name}"
    youtube_cache = read_cache_from_mongo(mongo_client, YOUTUBE_CACHE_COLLECTION)

    if cache_key in youtube_cache:
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
                print(
                    f"Updating YouTube cache for {track_name} by {artist_name} with URL {youtube_url}"
                )
                update_cache_in_mongo(mongo_client, YOUTUBE_CACHE_COLLECTION, cache_key, youtube_url)
                return youtube_url
        print(f"No video found for {track_name} by {artist_name}")
        return None
    else:
        print(f"Error: {response.status_code}, {response.text}")
        if response.status_code == 403 and "quotaExceeded" in response.text:
            return None
        return None

def get_apple_music_album_cover(url_link, mongo_client):
    cache_key = url_link
    album_cover_cache = read_cache_from_mongo(
        mongo_client, APPLE_MUSIC_ALBUM_COVER_CACHE_COLLECTION
    )

    if cache_key in album_cover_cache:
        return album_cover_cache[cache_key]

    print(f"Apple Music Album Cover Cache miss for URL: {url_link}")
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


def transform_playlists(mongo_client):
    print("Reading raw playlists from MongoDB")
    raw_playlists = read_data_from_mongo(mongo_client, RAW_PLAYLISTS_COLLECTION)
    print(f"Raw playlists from MongoDB: {len(raw_playlists)} documents found")

    for genre in PLAYLIST_GENRES:
        print(f"Processing genre: {genre}")
        all_tracks = []
        genre_playlists = [doc for doc in raw_playlists if doc["genre_name"] == genre]
        print(f"Found {len(genre_playlists)} playlists for genre {genre}")

        for document in genre_playlists:
            service_name = document["service_name"]
            data = document["data_json"]
            print(f"Processing {service_name} playlist for genre {genre}")
            tracks = convert_to_track_objects(data, service_name, genre)
            print(f"Converted {len(tracks)} tracks for {service_name} in genre {genre}")
            all_tracks.extend(tracks)

        if not all_tracks:
            print(f"No tracks found for genre {genre}")
            continue

        print("Setting ISRCs for all tracks")
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [executor.submit(track.set_isrc, mongo_client) for track in all_tracks]
            concurrent.futures.wait(futures)

        print("Setting YouTube URLs for all tracks")
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            futures = [executor.submit(track.set_youtube_url, mongo_client) for track in all_tracks]
            concurrent.futures.wait(futures)

        print("Setting Apple Music album cover URLs for applicable tracks")
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [
                executor.submit(track.set_apple_music_album_cover_url, mongo_client)
                for track in all_tracks
                if track.source_name == "AppleMusic"
            ]
            concurrent.futures.wait(futures)

        print(f"Processing tracks by source and genre for {genre}")
        for source in SERVICE_CONFIGS.keys():
            process_tracks(all_tracks, source, genre, mongo_client)


def process_tracks(tracks, source_name, genre, mongo_client):
    print(f"Processing {source_name} tracks for genre {genre}")
    filtered_tracks = [
        track
        for track in tracks
        if track.source_name.lower() == source_name.lower() and track.genre_name == genre
    ]
    if not filtered_tracks:
        print(f"No tracks found for {source_name} in genre {genre}")
        return

    sorted_tracks = sorted(filtered_tracks, key=lambda x: x.rank)
    print(f"Filtered and sorted {len(filtered_tracks)} tracks for {source_name} in genre {genre}")
    playlist_url = SERVICE_CONFIGS[source_name]["links"][genre]
    document = {
        "service_name": source_name,
        "genre_name": genre,
        "playlist_url": playlist_url,
        "tracks": [track.to_dict() for track in sorted_tracks],
    }
    insert_data_to_mongo(mongo_client, TRANSFORMED_DATA_COLLECTION, document)
    print(f"Inserted {len(filtered_tracks)} tracks for {source_name} in genre {genre}")


if __name__ == "__main__":
    print("Starting transform")
    set_secrets()
    mongo_client = get_mongo_client()
    print("Clearing transformed playlists collection")
    clear_collection(mongo_client, TRANSFORMED_DATA_COLLECTION)
    transform_playlists(mongo_client)
    print("Transform completed")
