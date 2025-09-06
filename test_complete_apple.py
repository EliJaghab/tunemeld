#!/usr/bin/env python3
import sys

sys.path.insert(0, "/Users/eli/github/tunemeld")
sys.path.insert(0, "/Users/eli/github/tunemeld/django_backend")

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django

django.setup()

from playlist_etl.extract import get_apple_music_playlist


def test_complete_apple_music():
    genres = ["pop", "rap", "dance", "country"]

    for genre in genres:
        print(f"\n=== Testing complete Apple Music {genre} extraction ===")

        try:
            playlist_data = get_apple_music_playlist(genre)
            metadata = playlist_data["metadata"]
            tracks = playlist_data["tracks"]

            print(f"✅ {genre}: Extraction successful")
            print(f"   Playlist name: {metadata['playlist_name']}")
            print(f"   Tracks data type: {type(tracks)}")

            if isinstance(tracks, dict) and "album_details" in tracks:
                track_count = len(tracks["album_details"])
                print(f"   Track count: {track_count}")
            else:
                print(f"   Tracks data: {str(tracks)[:100]}...")

        except Exception as e:
            print(f"❌ {genre}: Error - {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_complete_apple_music()
