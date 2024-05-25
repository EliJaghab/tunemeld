import json
import os
import re

import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


import musicbrainzngs


from extract import EXTRACT_BASE_PATH, load_env_variables_from_script, write_json_to_file

BASE_TRANSFORM_PATH = "migration/data/transform"

def transform_applemusic_data(data):
    tracks = []
    for key, track_data in data["album_details"].items():
        if key.isdigit():
            rank = int(key) + 1  # Convert to 1-based index
            track_name = track_data.get("name")
            artist_name = track_data.get("artist")
            url = track_data.get("link")
            album_url = get_apple_music_album_cover(url)
            
            milliseconds = duration_to_milliseconds(track_data["duration"])
            isrc = get_isrc(track_name, artist_name, milliseconds, url)
            
            track_info = {
                "isrc": isrc,
                "name": track_name,
                "artist": artist_name,
                "link": url,
                "rank": rank,
                "album_url": album_url, 
                "source": "apple_music"
            }
            tracks.append(track_info)

    sorted_tracks = sorted(tracks, key=lambda x: x['rank'])
    return sorted_tracks

def get_apple_music_album_cover(url_link):
    """Manually scrapes the URL for the Album cover for Apple Music Links."""
    response = client.get(url_link, timeout=30)
    response.raise_for_status()
    doc = BeautifulSoup(response.text, 'html.parser')

    source_tag = doc.find("source", attrs={"type": "image/jpeg"})
    if not source_tag or not source_tag.has_attr('srcset'):
        raise ValueError("Album cover URL not found")

    # Extracts the first URL from the srcset attribute value and decodes URL-encoded characters
    srcset = source_tag['srcset']
    url = unquote(srcset.split()[0])
    return url

def duration_to_milliseconds(duration):
    parts = duration.split()
    if len(parts) == 2:
        minutes = int(parts[0].strip('m'))
        seconds = int(parts[1].strip('s'))
        total_seconds = minutes * 60 + seconds
        return total_seconds * 1000
    return 0

cache_file = "migration/isrc_cache.json"
cache = {}

def load_cache():
    global cache
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as file:
            cache = json.load(file)

def save_cache(cache):
    with open(cache_file, 'w') as file:
        json.dump(cache, file)

def get_isrc(track_name, artist_name, expected_duration_ms, link):
    global cache
    # Initialize cache if empty
    if not cache:
        load_cache()
    # Using tuple of track name and artist name as the key
    cache_key = track_name + "|" + artist_name
    if cache_key in cache:
        print(f"Cache hit for {track_name} {artist_name}")
        return cache[cache_key]

    isrc = get_isrc_from_music_brainz(track_name, artist_name, expected_duration_ms, link)
    if not isrc:
        print(f"retrieving isrc from spotify for {track_name} {artist_name}")
        isrc = get_isrc_from_spotify_api(track_name, artist_name)

    # Update the cache with the new ISRC
    cache[cache_key] = isrc
    save_cache(cache)
    return isrc

def get_isrc_from_music_brainz(track_name, artist_name, expected_duration_ms, link):
    musicbrainzngs.set_useragent("TuneMeld", "0.1", "http://www.tunemeld.com")
    result = musicbrainzngs.search_recordings(query=track_name, artist=artist_name, limit=5)
    
    isrc_list = []
    for recording in result['recording-list']:
        if 'isrc-list' not in recording:
            continue
        
        is_disqualified = any(x in recording.get('disambiguation', '').lower() for x in ['mix', 'live', 'extended', 'dolby atmos'])
        if is_disqualified:
            continue
        
        recording_duration_ms = int(recording.get('length', 0))
        duration_diff = abs(recording_duration_ms - expected_duration_ms)
        
        for isrc in recording['isrc-list']:
            isrc_list.append({
                'isrc': isrc,
                'score': int(recording.get('ext:score', 0)),
                'duration_diff': duration_diff
            })
        
        isrc_list.sort(key=lambda x: (-x['score'], x['duration_diff']))

        if isrc_list:
            best_match = isrc_list[0]
            if best_match['score'] > 96 and abs(best_match['duration_diff']) <= 3000:
                return best_match['isrc']
            else:
                print(f"found more than one isrc for {track_name} {artist_name} {link}")
                print(f"Best ISRC: {best_match['isrc']} with score: {best_match['score']} and duration diff: {best_match['duration_diff']}ms")
        return None

def get_isrc_from_spotify_api(track_name, artist_name):
    client_id = os.getenv('spotify_client_id')
    client_secret = os.getenv('spotify_client_secret')
    client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    # Remove parentheses and contents within
    track_name_no_parens = re.sub(r'\([^()]*\)', '', track_name.lower())
    query = f"track:{track_name_no_parens} artist:{artist_name}"
    results = spotify.search(q=query, type='track', limit=1)
    
    tracks = results['tracks']['items']
    if tracks:
        isrc = tracks[0]['external_ids']['isrc']
        print("Found on Spotify:", tracks[0]["name"], isrc)
        return isrc
    else:
        error_message = f"No track found on Spotify using query: {query} for {track_name} {artist_name}"
        print(error_message)
        return None

def transform_soundcloud_data(data):
    items = data['tracks']['items']

    tracks = []
    for i, item in enumerate(items):
        isrc = item['publisher']['isrc']
        title = item['title']
        permalink = item['permalink']
        user = item['user']
        artist_name = user['name']
        artwork_url = item.get('artworkUrl', '')

        # Handle titles with hyphens
        if ' - ' in title:
            parts = title.split(' - ', 1)
            artist_name = parts[0]
            track_name = parts[1]
        else:
            track_name = title

        track = {
            "isrc": isrc,
            'name': track_name,
            'artist': artist_name,
            'link': permalink,
            'rank': i + 1,
            'album_url': artwork_url,
            'source': 'soundcloud'
        }
        tracks.append(track)

    sorted_tracks = sorted(tracks, key=lambda x: x['rank'])
    return sorted_tracks

def transform_spotify_data(data):
    tracks = []
    for rank, item in enumerate(data['items']):
        track_info = item.get('track', {})
        isrc = track_info["external_ids"]["isrc"]
        name = track_info.get('name', '')
        external_urls = track_info.get('external_urls', {}).get('spotify', '')
        artists = [artist.get('name', '') for artist in track_info.get('artists', []) if artist.get('name')]
        artist_names = ", ".join(artists)
        album_info = track_info.get('album', {})
        images = album_info.get('images', [])
        album_url = images[0].get('url', '') if images else None

        track = {
            "isrc": isrc,
            'name': name,
            'artist': artist_names,
            'link': external_urls,
            'rank': rank + 1,
            'album_url': album_url,
            'source': 'spotify'
        }
        tracks.append(track)

    sorted_tracks = sorted(tracks, key=lambda x: x['rank'])
    return sorted_tracks

def format_transformed_filename(original_filename):
    """Generate a clean file name for the JSON transformed output based on the original filename."""
    base_name = original_filename.replace('extract', 'transformed')
    full_path = f"{BASE_TRANSFORM_PATH}/{base_name}"
    os.makedirs(BASE_TRANSFORM_PATH, exist_ok=True) 
    return full_path

def read_json_from_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        return data



if __name__ == "__main__":
    print()
    print("starting transform")
    client = requests.Session()
    load_env_variables_from_script()
    
    for filename in os.listdir(EXTRACT_BASE_PATH):
        if 'extract' in filename:
            service_name = filename.split('_')[0] 
            transform_function_name = f"transform_{service_name}_data"
            
            transform_function = globals().get(transform_function_name)
            
            input_path = f"{EXTRACT_BASE_PATH}/{filename}"
            output_path = format_transformed_filename(filename)
            data = read_json_from_file(input_path)
            transformed_data = transform_function(data)
            write_json_to_file(transformed_data, output_path)
            print(f"Processed {input_path} -> {output_path}")
    
    print("transform completed")