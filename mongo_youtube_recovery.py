#!/usr/bin/env python3
"""
Recover YouTube URLs from MongoDB cache and migrate to Cloudflare/PostgreSQL
"""

import os
import sys

from pymongo import MongoClient

sys.path.append("django_backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django

django.setup()

from core.models import Track
from core.utils.cache_utils import CachePrefix, cache_get, cache_set


def connect_to_mongo():
    """Connect to MongoDB"""
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("❌ MONGO_URI not found in environment variables")
        return None

    try:
        client = MongoClient(mongo_uri)
        db = client.tunemeld
        return db
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return None


def analyze_mongo_youtube_cache():
    """Analyze YouTube URLs stored in MongoDB cache"""

    db = connect_to_mongo()
    if db is None:
        return

    print("🔍 Analyzing MongoDB cache for YouTube URLs...")
    print("=" * 60)

    # Look for YouTube URL cache entries
    cache_collection = db.cache

    # Find all YouTube URL cache entries
    youtube_cache_entries = cache_collection.find({"key": {"$regex": "^youtube_url:"}})

    youtube_urls_found = []
    placeholder_urls = []

    for entry in youtube_cache_entries:
        key = entry.get("key", "")
        value = entry.get("value", "")

        if value and value != "https://youtube.com":
            # Extract track info from key format: "youtube_url:track_name|artist_name"
            if key.startswith("youtube_url:"):
                track_info = key.replace("youtube_url:", "")
                youtube_urls_found.append({"key": track_info, "url": value, "mongo_id": entry.get("_id")})
        elif value == "https://youtube.com":
            placeholder_urls.append(key)

    print("📊 MongoDB YouTube cache analysis:")
    print(f"   Real YouTube URLs found: {len(youtube_urls_found)}")
    print(f"   Placeholder URLs found: {len(placeholder_urls)}")

    if youtube_urls_found:
        print("\n🎵 Sample YouTube URLs from MongoDB (first 5):")
        for item in youtube_urls_found[:5]:
            track_artist = item["key"].split("|")
            if len(track_artist) == 2:
                print(f"   • {track_artist[0]} by {track_artist[1]}")
                print(f"     URL: {item['url']}")

    return youtube_urls_found


def migrate_youtube_urls_to_postgres():
    """Migrate YouTube URLs from MongoDB to PostgreSQL"""

    youtube_urls = analyze_mongo_youtube_cache()
    if not youtube_urls:
        print("❌ No YouTube URLs found in MongoDB cache")
        return

    print("\n🔄 Starting migration to PostgreSQL...")
    print("=" * 60)

    updated_count = 0
    already_has_url = 0
    not_found = 0

    for item in youtube_urls:
        try:
            # Parse track and artist from key
            track_artist = item["key"].split("|")
            if len(track_artist) != 2:
                continue

            track_name = track_artist[0]
            artist_name = track_artist[1]
            youtube_url = item["url"]

            # Find matching track in PostgreSQL
            tracks = Track.objects.filter(track_name__iexact=track_name, artist_name__iexact=artist_name)

            if tracks.exists():
                track = tracks.first()

                # Check if track needs YouTube URL
                if not track.youtube_url or track.youtube_url == "https://youtube.com":
                    track.youtube_url = youtube_url
                    track.save()
                    updated_count += 1
                    print(f"   ✅ Updated: {track_name} by {artist_name}")
                else:
                    already_has_url += 1
            else:
                not_found += 1

        except Exception as e:
            print(f"   ❌ Error processing {item['key']}: {e}")

    print("\n📊 Migration Results:")
    print(f"   ✅ Tracks updated: {updated_count}")
    print(f"   ⏭️  Already had URL: {already_has_url}")
    print(f"   ❓ Tracks not found: {not_found}")


def copy_mongo_cache_to_cloudflare():
    """Copy YouTube URL cache entries from MongoDB to Cloudflare KV"""

    youtube_urls = analyze_mongo_youtube_cache()
    if not youtube_urls:
        return

    print("\n🔄 Copying cache to Cloudflare KV...")
    print("=" * 60)

    copied_count = 0
    skipped_count = 0

    for item in youtube_urls:
        key_data = item["key"]
        youtube_url = item["url"]

        # Check if already in cache
        existing = cache_get(CachePrefix.YOUTUBE_URL, key_data)
        if not existing or existing == "https://youtube.com":
            # Set in cache (no expiration for YouTube URLs)
            cache_set(CachePrefix.YOUTUBE_URL, key_data, youtube_url)
            copied_count += 1
            print(f"   ✅ Cached: {key_data[:50]}...")
        else:
            skipped_count += 1

    print("\n📊 Cache Copy Results:")
    print(f"   ✅ Entries copied: {copied_count}")
    print(f"   ⏭️  Entries skipped: {skipped_count}")


def check_track_youtube_coverage():
    """Check current YouTube URL coverage after migration"""

    print("\n📊 Final YouTube URL Coverage:")
    print("=" * 60)

    total = Track.objects.count()
    real_urls = Track.objects.filter(youtube_url__startswith="https://www.youtube.com/watch?v=").count()
    placeholder = Track.objects.filter(youtube_url="https://youtube.com").count()
    no_url = Track.objects.filter(youtube_url__isnull=True).count()

    print(f"   Total tracks: {total}")
    print(f"   Real YouTube URLs: {real_urls} ({(real_urls / total) * 100:.1f}%)")
    print(f"   Placeholder URLs: {placeholder}")
    print(f"   No URL: {no_url}")


if __name__ == "__main__":
    print("🎵 YouTube URL Recovery from MongoDB")
    print("=" * 60)

    # First analyze what's in MongoDB
    youtube_urls = analyze_mongo_youtube_cache()

    if youtube_urls:
        print("\n📝 Options:")
        print("1. Migrate YouTube URLs to PostgreSQL (update Track models)")
        print("2. Copy MongoDB cache to Cloudflare KV")
        print("3. Both")
        print("4. Exit")

        choice = input("\nSelect option (1-4): ")

        if choice == "1":
            migrate_youtube_urls_to_postgres()
            check_track_youtube_coverage()
        elif choice == "2":
            copy_mongo_cache_to_cloudflare()
        elif choice == "3":
            migrate_youtube_urls_to_postgres()
            copy_mongo_cache_to_cloudflare()
            check_track_youtube_coverage()
    else:
        print("\n❌ No YouTube URLs found in MongoDB to migrate")
