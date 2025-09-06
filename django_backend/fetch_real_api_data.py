"""
Fetch REAL data from RapidAPI - ONE call per service/genre combination.
Store exact raw responses in separate files. This is to create the staging environment
so we don't have to call RapidAPI during development because we don't have unlimited calls.
"""

import json
import os
import time

import requests

from playlist_etl.constants import PLAYLIST_GENRES, SERVICE_CONFIGS, GenreName, ServiceName
from playlist_etl.rapid_api_client import fetch_playlist_data


def fetch_and_save(service_name: ServiceName, genre: GenreName) -> bool:
    """Fetch data from API and save raw response to file."""
    try:
        data = fetch_playlist_data(service_name, genre)

        output_dir = f"real_api_data/{service_name.value}"
        os.makedirs(output_dir, exist_ok=True)
        output_file = f"{output_dir}/{genre.value}.json"

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        return True

    except requests.exceptions.RequestException as e:
        error_file = f"real_api_data/{service_name.value}/{genre.value}_error.json"
        with open(error_file, "w") as f:
            json.dump({"error": str(e), "service": service_name.value, "genre": genre.value}, f, indent=2)
        return False


def main() -> None:
    """Fetch all real API data."""
    for service_name_str in SERVICE_CONFIGS:
        service_name = ServiceName(service_name_str)
        for genre_str in PLAYLIST_GENRES:
            genre = GenreName(genre_str)
            fetch_and_save(service_name, genre)
            time.sleep(1)  # Rate limiting


if __name__ == "__main__":
    main()
