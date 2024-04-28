import json
import os
import re

import requests
import base64
from bs4 import BeautifulSoup
from urllib.parse import unquote

import musicbrainzngs

from extractors import RapidAPIClient, get_json_response, load_env_variables_from_script, write_json_to_file

def read_json_from_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        return data

def transform_applemusic_data(data):
    if not data:
        raise ValueError("Data is empty")

    album_details = data.get("album_details")
    if not album_details:
        raise ValueError("Album details not found in data")

    tracks = []
    for key, track_data in album_details.items():
        if key.isdigit():  # Check if the key is a rank number
            try:
                rank = int(key) + 1  # Convert to 1-based index
            except ValueError:
                print(f"Warning: Skipping rank {key} due to conversion error")
                continue
            
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
    response.raise_for_status()  # Raises an HTTPError for bad responses

    doc = BeautifulSoup(response.text, 'html.parser')

    # Query the document to find the specific tag and attribute
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

def get_isrc(track_name, artist_name, expected_duration_ms, link):
    isrc = None
    
    isrc = get_isrc_from_music_brainz(track_name, artist_name, expected_duration_ms, link)
    if not isrc:
        
        print(f"retrieving isrc from spotify for {track_name} {artist_name}")
        isrc = get_isrc_from_spotify_api(track_name, artist_name)
        
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
            if best_match['score'] > 95 and abs(best_match['duration_diff']) <= 3000:
                return best_match['isrc']
            else:
                print(f"found more than one isrc for {track_name} {artist_name} {link}")
                print(f"Best ISRC: {best_match['isrc']} with score: {best_match['score']} and duration diff: {best_match['duration_diff']}ms")
        return None
    

def get_isrc_from_spotify_api(track_name, artist_name):
    client_id = os.getenv('spotify_client_id')
    client_secret = os.getenv('spotify_client_secret')
    if not client_id or not client_secret:
        raise ValueError("Spotify client ID or secret not set in environment variables")

    auth_url = "https://accounts.spotify.com/api/token"
    auth_headers = {
        'Authorization': 'Basic ' + base64.b64encode(f"{client_id}:{client_secret}".encode()).decode(),
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    auth_body = {'grant_type': 'client_credentials'}
    auth_response = requests.post(auth_url, headers=auth_headers, data=auth_body)
    auth_response.raise_for_status()
    token = auth_response.json()['access_token']

    search_url = f"https://api.spotify.com/v1/search"
    search_headers = {'Authorization': f'Bearer {token}'}
    track_name_no_parens = re.sub(r'\([^()]*\)', '', track_name.lower())
    query = f"track:{track_name_no_parens} artist:{artist_name}"
    search_params = {
        'q': query,
        'type': 'track',
        'limit': 1
    }
    search_response = requests.get(search_url, headers=search_headers, params=search_params)
    search_response.raise_for_status()
    tracks = search_response.json()['tracks']['items']

    if tracks:
        print("found on spotify")
        print(tracks[0]["name"], tracks[0]['external_ids']['isrc'])
        return tracks[0]['external_ids']['isrc']
    else:
        print(f"No track found on spotify using query: {query} for {track_name} {artist_name}")
        return f"No track found using query: {query} for {track_name} {artist_name}"


def get_isrc_from_rapid_api_apple_music_api(track_url):
    client = RapidAPIClient()
    api_key = client.api_key
    url = "https://musicapi13.p.rapidapi.com/public/inspect/url"
    host = "musicapi13.p.rapidapi.com"
    payload = {"url": track_url}
    data = get_json_response(url, host, api_key, method='POST', payload=payload)
    return data['data']['isrc']



def transform_soundcloud_data(data):
    items = data['tracks']['items']

    tracks = []
    for i, item in enumerate(items):
        try:
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

        except KeyError as e:
            print(f"Missing key {e} in item index {i}, skipping this item.")
            continue

    sorted_tracks = sorted(tracks, key=lambda x: x['rank'])
    return sorted_tracks

def transform_spotify_data(data):
    items = data['items']

    tracks = []
    for rank, item in enumerate(items):
        track_info = item.get('track', {})
        if not track_info:
            print(f"Missing 'track' key in item at index {rank}")
            continue
        isrc = track_info["external_ids"]["isrc"]
        name = track_info.get('name', '')
        external_urls = track_info.get('external_urls', {}).get('spotify', '')
        artists = [artist.get('name', '') for artist in track_info.get('artists', []) if artist.get('name')]
        artist_names = ", ".join(artists)
        album_info = track_info.get('album', {})
        images = album_info.get('images', [])

        album_url = images[0].get('url', '') if images else None

        if not album_url:
            print(f"No album cover available for track at index {rank}")

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
    base_path = "migration/data/transform"
    full_path = f"{base_path}/{base_name}"
    os.makedirs(base_path, exist_ok=True) 
    return full_path

if __name__ == "__main__":
    # Directory listing and file processing
    client = requests.Session()
    load_env_variables_from_script()
    
    for filename in os.listdir('.'):
        if 'extract' in filename:
            service_name = filename.split('_')[0]  # Extracts the service name from filename
            transform_function_name = f"transform_{service_name}_data"
            
            # Dynamically get the transform function from globals
            transform_function = globals().get(transform_function_name)
            if not transform_function:
                print(f"No transform function found for {service_name}")
                continue
            
            # Read, transform, and write the data
            input_path = filename
            output_path = format_transformed_filename(filename)
            
            data = read_json_from_file(input_path)
            transformed_data = transform_function(data)
            write_json_to_file(transformed_data, output_path)
            print(f"Processed {input_path} -> {output_path}")