#!/usr/bin/env python3
"""
Check MongoDB for any cached data, especially YouTube URLs
"""

import os
import sys

from pymongo import MongoClient

sys.path.append("django_backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django

django.setup()


def explore_mongo():
    """Explore MongoDB to find YouTube URLs"""

    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("❌ MONGO_URI not found")
        return

    try:
        client = MongoClient(mongo_uri)
        db = client.tunemeld

        print("📊 MongoDB Collections:")
        print("=" * 60)

        # List all collections
        collections = db.list_collection_names()
        for coll_name in collections:
            coll = db[coll_name]
            count = coll.count_documents({})
            print(f"   • {coll_name}: {count} documents")

        # Check cache collection in detail
        print("\n🔍 Checking 'cache' collection for YouTube data:")
        print("-" * 40)

        cache_coll = db.cache

        # Check different key patterns
        patterns = [
            ("youtube_url:", "YouTube URL cache entries"),
            ("youtube:", "Any YouTube-related entries"),
            ("url", "Any URL-related entries"),
        ]

        for pattern, description in patterns:
            count = cache_coll.count_documents({"key": {"$regex": pattern}})
            print(f"   {description}: {count}")

            if count > 0 and count < 10:
                # Show sample entries
                print("   Sample entries:")
                for doc in cache_coll.find({"key": {"$regex": pattern}}).limit(5):
                    print(f"      - Key: {doc.get('key', 'N/A')[:50]}...")
                    print(f"        Value: {str(doc.get('value', 'N/A'))[:50]}...")

        # Check all unique key prefixes
        print("\n📋 Unique cache key prefixes:")
        print("-" * 40)

        # Get sample of keys to understand structure
        sample_keys = cache_coll.distinct("key")[:100]
        prefixes = set()
        for key in sample_keys:
            if ":" in key:
                prefix = key.split(":")[0]
                prefixes.add(prefix)

        for prefix in sorted(prefixes):
            count = cache_coll.count_documents({"key": {"$regex": f"^{prefix}:"}})
            print(f"   • {prefix}: {count} entries")

        # Check if there's a separate YouTube collection
        if "youtube" in collections:
            youtube_coll = db.youtube
            print(f"\n🎵 Found 'youtube' collection with {youtube_coll.count_documents({})} documents")

            # Show sample
            for doc in youtube_coll.find().limit(3):
                print(f"   Sample: {doc}")

        # Check if there's track data with YouTube URLs
        if "tracks" in collections:
            tracks_coll = db.tracks
            tracks_with_youtube = tracks_coll.count_documents({"youtube_url": {"$exists": True, "$ne": None}})
            print("\n🎵 Found 'tracks' collection:")
            print(f"   Total tracks: {tracks_coll.count_documents({})}")
            print(f"   With YouTube URLs: {tracks_with_youtube}")

            if tracks_with_youtube > 0:
                print("   Sample tracks with YouTube URLs:")
                for track in tracks_coll.find({"youtube_url": {"$exists": True, "$ne": None}}).limit(3):
                    print(f"      - {track.get('name', 'N/A')} by {track.get('artist', 'N/A')}")
                    print(f"        URL: {track.get('youtube_url', 'N/A')}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    explore_mongo()
