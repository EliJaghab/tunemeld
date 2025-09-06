#!/usr/bin/env python3
import sys

sys.path.insert(0, "/Users/eli/github/tunemeld")
sys.path.insert(0, "/Users/eli/github/tunemeld/django_backend")

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django

django.setup()

import requests  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

from playlist_etl.constants import SERVICE_CONFIGS  # noqa: E402


def test_apple_music_metadata():
    config = SERVICE_CONFIGS["apple_music"]
    genres = ["pop", "rap", "dance", "country"]

    for genre in genres:
        print(f"\n=== Testing Apple Music {genre} metadata ===")
        url = config["links"][genre]
        print(f"URL: {url}")

        try:
            response = requests.get(url)
            response.raise_for_status()
            doc = BeautifulSoup(response.text, "html.parser")

            title_tag = doc.select_one("a.click-action")
            title = title_tag.get_text(strip=True) if title_tag else "Unknown"
            print(f"  Title: '{title}'")

            subtitle_tag = doc.select_one("h1")
            subtitle = subtitle_tag.get_text(strip=True) if subtitle_tag else "Unknown"
            print(f"  Subtitle: '{subtitle}'")

            stream_tag = doc.find("amp-ambient-video", {"class": "editorial-video"})
            playlist_stream_url = stream_tag["src"] if stream_tag and stream_tag.get("src") else None
            print(f"  Stream URL: {playlist_stream_url}")

            description_tag = doc.find("p", {"data-testid": "truncate-text"})
            description = description_tag.get_text(strip=True) if description_tag else None
            print(f"  Description: {description}")

            print(f"✅ {genre}: Metadata extraction successful")

        except Exception as e:
            print(f"❌ {genre}: Error - {e}")


if __name__ == "__main__":
    test_apple_music_metadata()
