#!/usr/bin/env python3

import os
import sys

sys.path.append("django_backend")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django

django.setup()

from core.services.youtube_service import get_youtube_url


def test_youtube_api():
    print("🎵 Testing YouTube API with sample tracks...\n")

    test_tracks = [
        ("Flowers", "Miley Cyrus"),
        ("Bad Dreams", "Teddy Swims"),
        ("Tears", "Sabrina Carpenter"),
        ("Anti-Hero", "Taylor Swift"),
        ("As It Was", "Harry Styles"),
    ]

    # Check if API key is available
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY environment variable not found!")
        print("   Set it with: export GOOGLE_API_KEY='your_key_here'")
        return
    else:
        print(f"✅ API key found: {api_key[:10]}...")

    print("\n🔍 Testing YouTube URL lookups:")
    print("=" * 60)

    successful_fetches = 0
    failed_fetches = 0

    for track_name, artist_name in test_tracks:
        try:
            print(f"\n🎵 Searching: '{track_name}' by '{artist_name}'")
            youtube_url = get_youtube_url(track_name, artist_name)

            if youtube_url and youtube_url != "https://youtube.com":
                print(f"   ✅ Found: {youtube_url}")
                successful_fetches += 1
            elif youtube_url == "https://youtube.com":
                print("   ⚠️  Quota exceeded - got placeholder URL")
                failed_fetches += 1
            else:
                print("   ❌ No URL found")
                failed_fetches += 1

        except Exception as e:
            print(f"   💥 Error: {e}")
            failed_fetches += 1

    print("\n" + "=" * 60)
    print("📊 Results Summary:")
    print(f"   ✅ Successful: {successful_fetches}")
    print(f"   ❌ Failed: {failed_fetches}")
    print(f"   📈 Success rate: {(successful_fetches / len(test_tracks)) * 100:.1f}%")

    if failed_fetches > 0:
        print("\n🔍 Possible issues:")
        print("   - YouTube API quota exceeded")
        print("   - Network connectivity issues")
        print("   - API key permissions/billing issues")
        print("   - Rate limiting")


if __name__ == "__main__":
    test_youtube_api()
