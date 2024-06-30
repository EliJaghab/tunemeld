import os
import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote
import concurrent.futures
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from extract import EXTRACT_BASE_PATH, get_local_secrets, write_json_to_file
import threading

BASE_TRANSFORM_PATH = "docs/files/transform"
ISRC_CACHE_FILE = "isrc_cache.json"
YOUTUBE_CACHE_FILE = "youtube_cache.json"
SOURCES = ["apple_music", "spotify", "soundcloud"]
GENRES = ["dance"]

isrc_cache = {}
youtube_cache = {}
youtube_count = 0
youtube_cache_lock = threading.Lock()

def convert_apple_music_raw_export_to_track_type(data):
    tracks = []
    raw_track_data = data["album_details"].items()
    for key, track_data in raw_track_data:
        if key.isdigit():
            rank = int(key) + 1
            track_name = track_data["name"]
            artist_name = track_data["artist"]
            track_url = track_data["link"]
            track = Track(
                source_name="apple_music",
                rank=rank,
                track_name=track_name,
                artist_name=artist_name,
                track_url=track_url
            )
            tracks.append(track)
    return tracks

def convert_soundcloud_raw_export_to_track_type(data):
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
            isrc=isrc,
            track_name=track_name,
            artist_name=artist_name,
            track_url=track_url,
            rank=rank,
            album_cover_url=album_cover_url,
            source_name="soundcloud"
        )
        tracks.append(track)
    return tracks

def convert_spotify_raw_export_to_track_type(data):
    tracks = []
    for rank, item in enumerate(data["items"]):
        track_info = item["track"]
        isrc = track_info["external_ids"]["isrc"]
        track_name = track_info["name"]
        track_url = track_info["external_urls"]["spotify"]
        artist_name = ", ".join(artist["name"] for artist in track_info["artists"])
        album_cover_url = track_info["album"]["images"][0]["url"]

        track = Track(
            isrc=isrc,
            track_name=track_name,
            artist_name=artist_name,
            track_url=track_url,
            rank=rank + 1,
            album_cover_url=album_cover_url,
            source_name="spotify"
        )
        tracks.append(track)
    return tracks

class Track:
    def __init__(self, track_name, artist_name, track_url, rank, source_name, album_cover_url=None, isrc=None):
        self.isrc = isrc
        self.track_name = track_name
        self.artist_name = artist_name
        self.track_url = track_url
        self.album_cover_url = album_cover_url
        self.rank = rank
        self.source_name = source_name
        self.youtube_url = None

    def to_dict(self):
        return self.__dict__

    @staticmethod
    def from_dict(data):
        return Track(**data)

    def set_isrc(self):
        self.isrc = get_isrc_from_spotify_api(self.track_name, self.artist_name)

    def set_youtube_url(self):
        if not self.youtube_url:
            self.youtube_url = get_youtube_url_by_track_and_artist_name(self.track_name, self.artist_name)

    def set_apple_music_album_cover_url(self):
        if not self.album_cover_url:
            self.album_cover_url = get_apple_music_album_cover(self.track_url)

def save_tracks_to_json(tracks, filename):
    with open(filename, 'w') as file:
        json.dump([track.to_dict() for track in tracks], file, indent=4)

def load_tracks_from_json(filename):
    with open(filename, 'r') as file:
        track_dicts = json.load(file)
        return [Track.from_dict(track_dict) for track_dict in track_dicts]

def get_isrc_from_spotify_api(track_name, artist_name):
    client_id = os.getenv("spotify_client_id")
    client_secret = os.getenv("spotify_client_secret")
    client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    def search_spotify(query):
        results = spotify.search(q=query, type="track", limit=1)
        tracks = results["tracks"]["items"]
        if tracks:
            return tracks[0]["external_ids"]["isrc"]
        return None

    track_name_no_parens = re.sub(r"\([^()]*\)", "", track_name.lower())
    queries = [
        f"track:{track_name_no_parens} artist:{artist_name}",
        f"{track_name_no_parens} {artist_name}",
        f"track:{track_name.lower()} artist:{artist_name}"
    ]

    for query in queries:
        isrc = search_spotify(query)
        if isrc:
            return isrc

    print(f"No track found on Spotify using queries: {queries} for {track_name} {artist_name}")
    return None

def get_youtube_url_by_track_and_artist_name(track_name, artist_name):
    global youtube_count, youtube_cache
    cache_key = f"{track_name}|{artist_name}"

    with youtube_cache_lock: 
        if youtube_cache and cache_key in youtube_cache:
            return youtube_cache[cache_key]

    youtube_count += 1
    query = f"{track_name} {artist_name}"
    print(f"{youtube_count} getting youtube url for {query}")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("API key not found. Make sure to set the GOOGLE_API_KEY environment variable.")

    youtube_search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&key={api_key}&quotaUser={youtube_count}"

    response = requests.get(youtube_search_url)
    if response.status_code == 200:
        data = response.json()
        if "items" in data and len(data["items"]) > 0:
            video_id = data["items"][0]["id"]["videoId"]
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"
            youtube_cache[cache_key] = youtube_url
            write_json_to_file(youtube_cache, YOUTUBE_CACHE_FILE)
            return youtube_url

        with youtube_cache_lock: 
            youtube_cache[cache_key] = "No video found"
            write_json_to_file(youtube_cache, YOUTUBE_CACHE_FILE)
        return "No video found"
    
    error_msg = f"Error: {response.status_code}, {response.text}"
    print(error_msg)
    return error_msg

def get_apple_music_album_cover(url_link):
    response = client.get(url_link, timeout=30)
    response.raise_for_status()
    doc = BeautifulSoup(response.text, "html.parser")

    source_tag = doc.find("source", attrs={"type": "image/jpeg"})
    if not source_tag or not source_tag.has_attr("srcset"):
        raise ValueError("Album cover URL not found")

    srcset = source_tag["srcset"]
    url = unquote(srcset.split()[0])
    return url

def read_json_from_file(file_path):
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r") as file:
        return json.load(file)

def process_tracks(tracks, filename):
    filtered_tracks = [track for track in tracks if track.source_name in filename]
    sorted_tracks = sorted(filtered_tracks, key=lambda x: x.rank)
    output_path = f"{BASE_TRANSFORM_PATH}/{filename}_transformed.json"
    save_tracks_to_json(sorted_tracks, output_path)

if __name__ == "__main__":
    print("\nStarting transform")
    client = requests.Session()

    if not os.getenv("GITHUB_ACTIONS"):
        get_local_secrets()
    
    isrc_cache = read_json_from_file(ISRC_CACHE_FILE)
    youtube_cache = read_json_from_file(YOUTUBE_CACHE_FILE)

    all_tracks = []
    for filename in os.listdir(EXTRACT_BASE_PATH):
        input_path = f"{EXTRACT_BASE_PATH}/{filename}"
        data = read_json_from_file(input_path)

        if "applemusic" in filename:
            all_tracks.extend(convert_apple_music_raw_export_to_track_type(data))
        elif "spotify" in filename:
            all_tracks.extend(convert_spotify_raw_export_to_track_type(data))
        elif "soundcloud" in filename:
            all_tracks.extend(convert_soundcloud_raw_export_to_track_type(data))
        else:
            raise ValueError("unknown file name")
        
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(track.set_isrc) for track in all_tracks]
        concurrent.futures.wait(futures)
        for future in futures:
            future.result()

        futures = [executor.submit(track.set_youtube_url) for track in all_tracks]
        concurrent.futures.wait(futures)
        for future in futures:
            future.result()

        futures = [executor.submit(track.set_apple_music_album_cover_url) for track in all_tracks if track.source_name == "apple_music"]
        concurrent.futures.wait(futures)
        for future in futures:
            future.result()
        
    for source in SOURCES:
        for genre in GENRES:
            process_tracks(all_tracks, f"{source}_{genre}")

    print("Transform completed")
