from flask import Flask, render_template
from datetime import datetime
import json
import os
import logging
from extractor import Extractor, SpotifyExtractor, SOUNDCLOUD_URL, APPLE_MUSIC_URL, SPOTIFY_PLAYLIST_API_URL

from aggregator import aggregate_playlists



app = Flask(__name__)
extractor = Extractor()
spotify_extractor = SpotifyExtractor()

CACHED_SOUNDCLOUD_TRACKS_FILENAME = "cache_soundcloud.json"
CACHED_APPLE_MUSIC_TRACKS_FILENAME = "cache_apple_music.json"
CACHED_SPOTIFY_TRACKS_FILENAME = "cache_spotify.json"

def get_cached_data(filename):
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
                return data['result']
        else:
            logging.warning(f"The cache file {filename} does not exist.")
    except Exception as e:
        logging.exception("An error occurred while getting cached data.")
    return None

def cache_data(data, filename):
    with open(filename, 'w') as f:
        json.dump({'result': data, 'timestamp': datetime.now().isoformat()}, f)

def fetch_data(url, extract_method, cache_filename, extractor_instance=None):
    data = get_cached_data(cache_filename)
    if data is None:
        if extractor_instance:
            data = getattr(extractor_instance, extract_method)()
        else:
            soup = extractor.soupify(url, True)
            data = getattr(extractor, extract_method)(soup)
        cache_data(data, cache_filename)
    return data

@app.route('/')
def home():
    # Fetch and cache data for SoundCloud, Apple Music, and Spotify
    soundcloud_data = fetch_data(SOUNDCLOUD_URL, 'retrieve_soundcloud_items', CACHED_SOUNDCLOUD_TRACKS_FILENAME)
    apple_music_data = fetch_data(APPLE_MUSIC_URL, 'retrieve_apple_music_song_details', CACHED_APPLE_MUSIC_TRACKS_FILENAME)
    spotify_data = fetch_data(SPOTIFY_PLAYLIST_API_URL, 'retrieve_spotify_song_details', CACHED_SPOTIFY_TRACKS_FILENAME, extractor_instance=spotify_extractor)

    # Get the aggregated playlist
    aggregated_data = aggregate_playlists(soundcloud_data, apple_music_data, spotify_data)

    return render_template('index.html', soundcloud_data=soundcloud_data, apple_music_data=apple_music_data, spotify_data=spotify_data, aggregated_data=aggregated_data)

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

if __name__ == '__main__':
    app.run(debug=True)
