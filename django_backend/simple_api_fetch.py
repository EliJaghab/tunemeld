"""
SIMPLIFIED ONE-TIME API FETCH
Makes one RapidAPI call per service/genre to get real playlist data.
Only uses direct API calls, no browser automation.
"""

import json
import os
import sys
import time
from datetime import datetime

# Add parent directory to path
sys.path.append("..")

import requests

from playlist_etl.constants import PLAYLIST_GENRES, SERVICE_CONFIGS


def make_api_call(service_name: str, genre: str, api_key: str) -> dict:
    """Make one API call for a specific service/genre combination."""
    config = SERVICE_CONFIGS[service_name]
    playlist_url = config["links"][genre]

    # Prepare the parameter
    if "spotify" in config["base_url"]:
        param_value = playlist_url.split("/")[-1]
    else:
        from urllib.parse import quote

        param_value = quote(playlist_url)

    # Build API URL
    api_url = f"{config['base_url']}?{config['param_key']}={param_value}"

    # Make the request
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": config["host"],
        "Content-Type": "application/json",
    }

    print(f"  📡 API URL: {api_url}")
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()

    return response.json()


def fetch_simple_data():
    """Fetch real data using direct API calls only."""

    # Check API key
    api_key = os.getenv("X_RAPIDAPI_KEY")
    if not api_key or api_key == "dummy_key_for_staging":
        print("❌ Please set X_RAPIDAPI_KEY environment variable")
        return

    print(f"🔑 Using API key: {api_key[:8]}...")

    real_data = []
    service_names = list(SERVICE_CONFIGS.keys())
    total_calls = len(service_names) * len(PLAYLIST_GENRES)
    current_call = 0

    print(f"🚀 Making {total_calls} direct API calls...")

    for service_name in service_names:
        for genre in PLAYLIST_GENRES:
            current_call += 1
            print(f"[{current_call}/{total_calls}] Fetching {service_name} - {genre}...")

            try:
                # Make API call
                playlist_data = make_api_call(service_name, genre, api_key)

                # Get basic playlist info
                config = SERVICE_CONFIGS[service_name]
                playlist_url = config["links"][genre]
                playlist_name = f"{service_name} {genre.title()} Playlist"

                # Map service and genre to IDs
                service_id = {"Spotify": 1, "AppleMusic": 2, "SoundCloud": 3}[service_name]
                genre_id = {"pop": 1, "rap": 2, "dance": 3, "country": 4}[genre]

                # Store the result
                real_data.append(
                    {
                        "model": "core.rawplaylistdata",
                        "pk": len(real_data) + 1,
                        "fields": {
                            "service": service_id,
                            "genre": genre_id,
                            "playlist_url": playlist_url,
                            "playlist_name": playlist_name,
                            "created_at": datetime.now().isoformat() + "Z",
                            "data": playlist_data,
                        },
                    }
                )

                # Count tracks in response
                track_count = 0
                if "items" in playlist_data:
                    track_count = len(playlist_data["items"])
                elif "tracks" in playlist_data and "items" in playlist_data["tracks"]:
                    track_count = len(playlist_data["tracks"]["items"])
                elif "album_details" in playlist_data:
                    track_count = len(playlist_data["album_details"])

                print(f"  ✅ Success! Got {track_count} tracks")

                # Rate limiting delay
                if current_call < total_calls:
                    print("  ⏸️  Waiting 2 seconds...")
                    time.sleep(2)

            except Exception as e:
                print(f"  ❌ Failed: {e}")
                continue

    # Add lookup tables
    lookup_tables = [
        {"model": "core.service", "pk": 1, "fields": {"name": "Spotify", "display_name": "Spotify"}},
        {"model": "core.service", "pk": 2, "fields": {"name": "AppleMusic", "display_name": "Apple Music"}},
        {"model": "core.service", "pk": 3, "fields": {"name": "SoundCloud", "display_name": "SoundCloud"}},
        {"model": "core.genre", "pk": 1, "fields": {"name": "pop", "display_name": "Pop"}},
        {"model": "core.genre", "pk": 2, "fields": {"name": "rap", "display_name": "Hip-Hop/Rap"}},
        {"model": "core.genre", "pk": 3, "fields": {"name": "dance", "display_name": "Dance/Electronic"}},
        {"model": "core.genre", "pk": 4, "fields": {"name": "country", "display_name": "Country"}},
    ]

    complete_data = lookup_tables + real_data

    # Save to fixture file
    output_file = "/Users/eli/github/tunemeld/django_backend/core/fixtures/real_staging_data.json"
    with open(output_file, "w") as f:
        json.dump(complete_data, f, indent=2)

    print(f"💾 Saved real data to: {output_file}")
    print(f"📊 Total API calls made: {current_call}")
    print(f"📦 Total records: {len(complete_data)}")
    print("✅ Done! Real staging data is ready.")


if __name__ == "__main__":
    fetch_simple_data()
