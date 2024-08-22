import lyricsgenius
import logging
import re
from concurrent.futures import ThreadPoolExecutor
import os

from utils import (
    set_secrets,
    get_mongo_client,
    get_mongo_collection,
    insert_or_update_data_to_mongo,
    read_data_from_mongo,
    get_spotify_client,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s",
)

# Constants
MAX_WORKERS = 4

# Genius API Client
class GeniusAPIClient:
    def __init__(self):
        set_secrets()
        print(os.getenv("GENIUS_API_KEY"))
        self.genius = lyricsgenius.Genius(os.getenv("GENIUS_API_KEY"))

    def search_song(self, track_name: str, artist_name: str) -> dict:
        search_results = self.genius.search_songs(track_name)
        for hit in search_results['hits']:
            if hit['result']['primary_artist']['name'].lower() == artist_name.lower():
                return hit['result']
        return None

    def get_lyrics(self, song_id: int) -> str:
        lyrics = self.genius.lyrics(song_id=song_id)
        return self.clean_lyrics(lyrics)

    def get_artist_info(self, artist_id: int) -> dict:
        artist_response = self.genius.artist(artist_id)
        artist = artist_response['artist']
        return {
            'bio': artist['description']['plain'],
        }

    @staticmethod
    def clean_lyrics(lyrics: str) -> str:
        cleaned_lyrics = re.sub(r"(?i)(You might also like|Embed|Translations.*|Contributors.*)", "", lyrics).strip()
        cleaned_lyrics = re.sub(r'\n\s*\n', '\n', cleaned_lyrics)
        return cleaned_lyrics

# Processing and data enrichment
def fetch_and_store_genius_data(track: dict, genius_client: GeniusAPIClient, mongo_client) -> None:
    song = genius_client.search_song(track['track_name'], track['artist_name'])
    if song:
        lyrics = genius_client.get_lyrics(song_id=song['id'])
        artist_info = genius_client.get_artist_info(song['primary_artist']['id'])

        # Update MongoDB with the enriched data
        data_to_store = {
            'isrc': track['isrc'],
            'track_name': track['track_name'],
            'artist_name': track['artist_name'],
            'lyrics': lyrics,
            'artist_bio': artist_info.get('bio', ''),
        }
        insert_or_update_data_to_mongo(mongo_client, data_to_store)

def fetch_and_store_spotify_data(track: dict, spotify_client, mongo_client) -> None:
    spotify_data = spotify_client.get_spotify_data(track['isrc'])

    # Update MongoDB with the enriched data
    if spotify_data:
        data_to_store = {
            'isrc': track['isrc'],
            'track_name': track['track_name'],
            'artist_name': track['artist_name'],
            'spotify_data': spotify_data,
        }
        insert_or_update_data_to_mongo(mongo_client, data_to_store)

# Main process
def process_tracks(tracks: list, genius_client: GeniusAPIClient, spotify_client, mongo_client) -> None:
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for track in tracks:
            futures.append(executor.submit(fetch_and_store_genius_data, track, genius_client, mongo_client))
            futures.append(executor.submit(fetch_and_store_spotify_data, track, spotify_client, mongo_client))

        for future in futures:
            try:
                future.result()
            except Exception as e:
                logging.error(f"Error processing track: {e}")

if __name__ == "__main__":
    set_secrets()
    mongo_client = get_mongo_client()
    collection_name = "track_data"
    mongo_collection = get_mongo_collection(mongo_client, collection_name)

    genius_client = GeniusAPIClient()
    spotify_client = get_spotify_client()

    tracks = read_data_from_mongo(mongo_client, collection_name)

    process_tracks(tracks, genius_client, spotify_client, mongo_client)

    logging.info("Data enrichment and processing complete.")
