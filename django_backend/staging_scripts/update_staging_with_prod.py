#!/usr/bin/env python3
"""
Update staging data files with real production data from the MongoDB API.
This script fetches live production data and updates our staging JSON files
to have realistic album covers and track information.
"""

import json
import requests
import sys
from pathlib import Path

def fetch_production_data(genre, service):
    """Fetch production data from the MongoDB API."""
    service_map = {
        'spotify': 'Spotify',
        'soundcloud': 'SoundCloud', 
        'apple_music': 'AppleMusic'
    }
    
    service_name = service_map[service]
    url = f"https://api.tunemeld.com/service-playlist/{genre}/{service_name}"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data['data'][0]['tracks'][:10]  # Get first 10 tracks
    except Exception as e:
        print(f"Error fetching {service} {genre} data: {e}")
        return None

def update_spotify_json(genre, prod_tracks):
    """Update Spotify JSON file with production data."""
    file_path = Path(f"real_api_data/spotify/{genre}.json")
    
    if not file_path.exists():
        print(f"Spotify file not found: {file_path}")
        return False
        
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Update the first 10 items with production data
        for i, prod_track in enumerate(prod_tracks):
            if i < len(data['items']):
                item = data['items'][i]
                # Update track details
                item['track']['name'] = prod_track['track_name']
                item['track']['artists'][0]['name'] = prod_track['artist_name']
                item['track']['external_urls']['spotify'] = prod_track['track_url']
                item['track']['external_ids']['isrc'] = prod_track['isrc']
                # Update album cover
                item['track']['album']['images'][0]['url'] = prod_track['album_cover_url']
                item['track']['album']['images'][1]['url'] = prod_track['album_cover_url']
                item['track']['album']['images'][2]['url'] = prod_track['album_cover_url']
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Updated Spotify {genre} with {len(prod_tracks)} tracks")
        return True
        
    except Exception as e:
        print(f"Error updating Spotify {genre}: {e}")
        return False

def update_soundcloud_json(genre, prod_tracks):
    """Update SoundCloud JSON file with production data."""
    file_path = Path(f"real_api_data/soundcloud/{genre}.json")
    
    if not file_path.exists():
        print(f"SoundCloud file not found: {file_path}")
        return False
        
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Update the first 10 tracks
        for i, prod_track in enumerate(prod_tracks):
            if i < len(data['tracks']['items']):
                item = data['tracks']['items'][i]
                item['title'] = prod_track['track_name']
                item['publisher']['artist'] = prod_track['artist_name']
                item['permalink'] = prod_track['track_url']
                item['publisher']['isrc'] = prod_track['isrc']
                item['artwork_url'] = prod_track['album_cover_url']
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Updated SoundCloud {genre} with {len(prod_tracks)} tracks")
        return True
        
    except Exception as e:
        print(f"Error updating SoundCloud {genre}: {e}")
        return False

def update_apple_music_json(genre, prod_tracks):
    """Update Apple Music JSON file with production data."""
    file_path = Path(f"real_api_data/apple_music/{genre}.json")
    
    if not file_path.exists():
        print(f"Apple Music file not found: {file_path}")
        return False
        
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Update the first 10 tracks
        for i, prod_track in enumerate(prod_tracks):
            key = str(i)
            if key in data['album_details']:
                item = data['album_details'][key]
                item['name'] = prod_track['track_name']
                item['artist'] = prod_track['artist_name']
                item['link'] = prod_track['track_url']
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Updated Apple Music {genre} with {len(prod_tracks)} tracks")
        return True
        
    except Exception as e:
        print(f"Error updating Apple Music {genre}: {e}")
        return False

def main():
    genres = ['pop', 'country', 'dance', 'rap']
    services = ['spotify', 'soundcloud', 'apple_music']
    
    print("Updating staging data with production data...")
    
    for genre in genres:
        print(f"\nUpdating {genre} genre:")
        
        for service in services:
            print(f"  Fetching {service} data...")
            prod_tracks = fetch_production_data(genre, service)
            
            if prod_tracks:
                if service == 'spotify':
                    update_spotify_json(genre, prod_tracks)
                elif service == 'soundcloud':
                    update_soundcloud_json(genre, prod_tracks)
                elif service == 'apple_music':
                    update_apple_music_json(genre, prod_tracks)
            else:
                print(f"    Failed to fetch {service} {genre} data")
    
    print("\nStaging data update complete!")

if __name__ == "__main__":
    main()