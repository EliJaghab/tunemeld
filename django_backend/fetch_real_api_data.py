"""
Fetch REAL data from RapidAPI - ONE call per service/genre combination.
Store exact raw responses in separate files.
"""

import json
import os
import time

import requests

# Service configurations with exact API endpoints
SERVICE_CONFIGS = {
    "spotify": {
        "host": "spotify23.p.rapidapi.com",
        "endpoint": "https://spotify23.p.rapidapi.com/playlist_tracks/",
        "links": {
            "pop": "37i9dQZF1DXcBWIGoYBM5M",
            "rap": "37i9dQZF1DX0XUsuxWHRQd",
            "dance": "37i9dQZF1DX4dyzvuaRJ0n",
            "country": "37i9dQZF1DX1lVhptIYRda",
        },
    },
    "apple_music": {
        "host": "soundcloud-scraper.p.rapidapi.com",
        "endpoint": "https://soundcloud-scraper.p.rapidapi.com/v1/playlist/tracks",
        "links": {
            "pop": "https://music.apple.com/us/playlist/a-list-pop/pl.5ee8333dbe944d9f9151e97d92d1ead9",
            "rap": "https://music.apple.com/us/playlist/rap-life/pl.abe8ba42278f4ef490e3a9fc5ec8e8c5",
            "dance": "https://music.apple.com/us/playlist/dancefloor-hits/pl.6bf4415b83ce4f3789614ac4c3675740",
            "country": "https://music.apple.com/us/playlist/today-s-country/pl.87bb5b36a9bd49db8c975607452bfa2b",
        },
    },
    "soundcloud": {
        "host": "soundcloud-scraper.p.rapidapi.com",
        "endpoint": "https://soundcloud-scraper.p.rapidapi.com/v1/playlist/tracks",
        "links": {
            "pop": "https://soundcloud.com/soundcloud-the-peak/sets/on-the-up-the-best-new-pop",
            "rap": "https://soundcloud.com/soundcloud-hustle/sets/drippin-best-rap-right-now",
            "dance": "https://soundcloud.com/discover/sets/charts-top:all-music:dk",
            "country": "https://soundcloud.com/soundcloud-today/sets/the-upload-country",
        },
    },
}


def fetch_and_save(service_name, genre, api_key):
    """Fetch data from API and save raw response to file."""
    config = SERVICE_CONFIGS[service_name]

    if service_name == "spotify":
        # Spotify uses different API structure
        playlist_id = config["links"][genre]
        url = f"{config['endpoint']}?id={playlist_id}&offset=0&limit=100"
    else:
        # Apple Music and SoundCloud use same scraper API
        playlist_url = config["links"][genre]
        url = f"{config['endpoint']}?playlist={playlist_url}"

    headers = {"X-RapidAPI-Key": api_key, "X-RapidAPI-Host": config["host"]}

    print(f"📡 Fetching {service_name}/{genre}...")
    print(f"   URL: {url}")

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Save exact raw response
        output_dir = f"real_api_data/{service_name}"
        output_file = f"{output_dir}/{genre}.json"

        with open(output_file, "w") as f:
            json.dump(response.json(), f, indent=2)

        # Show what we got
        data = response.json()
        if isinstance(data, dict):
            if "items" in data:
                track_count = len(data["items"])
            elif "tracks" in data and "items" in data["tracks"]:
                track_count = len(data["tracks"]["items"])
            elif "album_details" in data:
                track_count = len(data["album_details"])
            else:
                track_count = "unknown structure"
        else:
            track_count = len(data) if isinstance(data, list) else "unknown"

        print(f"   ✅ Saved to {output_file} ({track_count} tracks)")
        return True

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Failed: {e!s}")
        # Save error for debugging
        error_file = f"real_api_data/{service_name}/{genre}_error.json"
        with open(error_file, "w") as f:
            json.dump({"error": str(e), "service": service_name, "genre": genre}, f, indent=2)
        return False


def main():
    """Fetch all real API data."""
    api_key = os.getenv("X_RAPIDAPI_KEY")
    if not api_key:
        print("❌ X_RAPIDAPI_KEY not found in environment")
        print("Set it with: export X_RAPIDAPI_KEY='your-key-here'")
        return

    print("🚀 Starting REAL API data fetch...")
    print("=" * 50)

    success_count = 0
    total_count = 0

    # Fetch data for each service/genre combination
    for service_name in SERVICE_CONFIGS:
        for genre in ["pop", "rap", "dance", "country"]:
            total_count += 1
            if fetch_and_save(service_name, genre, api_key):
                success_count += 1
            time.sleep(1)  # Rate limiting

    print("=" * 50)
    print(f"📊 Results: {success_count}/{total_count} successful API calls")
    print("📁 Data saved in: real_api_data/")
    print("✅ Done! Use this EXACT data for staging.")


if __name__ == "__main__":
    main()
