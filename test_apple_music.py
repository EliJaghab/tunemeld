#!/usr/bin/env python3
import sys

sys.path.insert(0, "/Users/eli/github/tunemeld")

from playlist_etl.rapid_api_client import fetch_playlist_data


def test_apple_music_genres():
    genres = ["pop", "rap", "dance", "country"]

    for genre in genres:
        print(f"\n=== Testing Apple Music {genre} ===")
        try:
            data = fetch_playlist_data("apple_music", genre)
            if data and "data" in data:
                track_count = len(data["data"])
                print(f"✅ {genre}: {track_count} tracks")
            else:
                print(f"❌ {genre}: No data or empty response")
                print(f"   Response: {data}")
        except Exception as e:
            print(f"❌ {genre}: Error - {e}")


if __name__ == "__main__":
    test_apple_music_genres()
