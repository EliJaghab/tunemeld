"""
ONE-TIME DATA FETCH SCRIPT
Makes exactly ONE API call per service/genre combination to get real data.
USAGE: Set X_RAPIDAPI_KEY environment variable, then run: python one_time_data_fetch.py
"""

import json
import os
import sys
import time
from datetime import datetime

# Add parent directory to path to import playlist_etl
sys.path.append("..")

from playlist_etl.constants import PLAYLIST_GENRES, SERVICE_CONFIGS
from playlist_etl.extract import AppleMusicFetcher, RapidAPIClient, SoundCloudFetcher, SpotifyFetcher


def fetch_one_time_data():
    """Fetch real data from RapidAPI - ONE request per service/genre."""

    # Check API key
    api_key = os.getenv("X_RAPIDAPI_KEY")
    if not api_key or api_key == "dummy_key_for_staging":
        print("❌ Please set X_RAPIDAPI_KEY environment variable with your real API key")
        print("   export X_RAPIDAPI_KEY=your_real_key_here")
        return

    print(f"🔑 Using API key: {api_key[:8]}...")

    client = RapidAPIClient()
    real_data = []

    service_names = list(SERVICE_CONFIGS.keys())
    total_calls = len(service_names) * len(PLAYLIST_GENRES)
    current_call = 0

    print(f"🚀 Making {total_calls} API calls...")

    for service_name in service_names:
        for genre in PLAYLIST_GENRES:
            current_call += 1
            print(f"[{current_call}/{total_calls}] Fetching {service_name} - {genre}...")

            try:
                # Create appropriate fetcher
                if service_name == "AppleMusic":
                    fetcher = AppleMusicFetcher(client, service_name, genre)
                elif service_name == "SoundCloud":
                    fetcher = SoundCloudFetcher(client, service_name, genre)
                elif service_name == "Spotify":
                    fetcher = SpotifyFetcher(client, service_name, genre)
                else:
                    print(f"❌ Unknown service: {service_name}")
                    continue

                # Set playlist details and get data
                fetcher.set_playlist_details()
                playlist_data = fetcher.get_playlist()

                # Store the result
                service_id = 1 if service_name == "Spotify" else (2 if service_name == "AppleMusic" else 3)
                genre_id = 1 if genre == "pop" else (2 if genre == "rap" else (3 if genre == "dance" else 4))

                real_data.append(
                    {
                        "model": "core.rawplaylistdata",
                        "pk": len(real_data) + 1,
                        "fields": {
                            "service": service_id,
                            "genre": genre_id,
                            "playlist_url": getattr(fetcher, "playlist_url", f"{service_name.lower()}_{genre}"),
                            "playlist_name": getattr(
                                fetcher, "playlist_name", f"{service_name} {genre.title()} Playlist"
                            ),
                            "created_at": datetime.now().isoformat() + "Z",
                            "data": playlist_data,
                        },
                    }
                )

                track_count = len(playlist_data.get("items", playlist_data.get("tracks", {}).get("items", [])))
                print(f"✅ Success! Got {track_count} tracks")

                # Add delay to avoid rate limiting
                if current_call < total_calls:
                    print("⏸️  Waiting 2 seconds to avoid rate limiting...")
                    time.sleep(2)

            except Exception as e:
                print(f"❌ Failed {service_name}/{genre}: {e}")
                continue

    # Add lookup tables to the beginning
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

    # Save to new fixture file
    output_file = "/Users/eli/github/tunemeld/django_backend/core/fixtures/real_staging_data.json"
    with open(output_file, "w") as f:
        json.dump(complete_data, f, indent=2)

    print(f"💾 Saved real data to: {output_file}")
    print(f"📊 Total API calls made: {current_call}")
    print(f"📦 Total records: {len(complete_data)}")
    print("✅ Done! You can now use this real data for staging.")


if __name__ == "__main__":
    fetch_one_time_data()
