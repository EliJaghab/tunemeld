"""
Fetch REAL data from RapidAPI - ONE call per service/genre combination.
Store exact raw responses in separate files. This is to create the staging environment
so we don't have to call RapidAPI during development because we don't have unlimited calls.
"""

import json
import os
import time

import requests

from playlist_etl.constants import PLAYLIST_GENRES, SERVICE_CONFIGS
from playlist_etl.rapid_api_client import fetch_playlist_data


def fetch_and_save(service_name: str, genre: str) -> bool:
    """Fetch data from API and save raw response to file."""
    print(f" Fetching {service_name}/{genre}...")

    try:
        data = fetch_playlist_data(service_name, genre)

        # Save exact raw response
        output_dir = f"real_api_data/{service_name}"
        os.makedirs(output_dir, exist_ok=True)
        output_file = f"{output_dir}/{genre}.json"

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        # Show what we got
        track_count: int | str
        if isinstance(data, dict):
            if "items" in data:
                track_count = len(data["items"])
            elif "tracks" in data and isinstance(data["tracks"], dict) and "items" in data["tracks"]:
                track_count = len(data["tracks"]["items"])
            elif "album_details" in data:
                track_count = len(data["album_details"])
            else:
                track_count = "unknown structure"
        elif isinstance(data, list):
            track_count = len(data)
        else:
            track_count = "unknown"

        print(f"   ✅ Saved to {output_file} ({track_count} tracks)")
        return True

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Failed: {e!s}")
        # Save error for debugging
        error_file = f"real_api_data/{service_name}/{genre}_error.json"
        with open(error_file, "w") as f:
            json.dump({"error": str(e), "service": service_name, "genre": genre}, f, indent=2)
        return False


def main() -> None:
    """Fetch all real API data."""
    print(" Starting REAL API data fetch...")
    print("=" * 50)

    success_count = 0
    total_count = 0

    # Fetch data for each service/genre combination
    for service_name in SERVICE_CONFIGS:
        for genre in PLAYLIST_GENRES:
            total_count += 1
            if fetch_and_save(service_name, genre):
                success_count += 1
            time.sleep(1)  # Rate limiting

    print("=" * 50)
    print(f" Results: {success_count}/{total_count} successful API calls")
    print(" Data saved in: real_api_data/")
    print("✅ Done! Use this EXACT data for staging.")


if __name__ == "__main__":
    main()
