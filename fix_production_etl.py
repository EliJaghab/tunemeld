#!/usr/bin/env python3
"""
Fix production ETL pipeline - run missing steps to create Apple Music and TuneMeld playlists
"""

import os
import sys

# Set production environment
os.environ["DATABASE_URL"] = (
    "postgresql://postgres:TMvEddPnHxNAtoxkPZmYaKYYawSScutY@switchback.proxy.rlwy.net:39383/railway"
)
os.environ["DJANGO_SETTINGS_MODULE"] = "core.settings"
os.environ["DEBUG"] = "False"

# Set other production credentials
os.environ["X_RAPIDAPI_KEY"] = "be4693d6fdmshe2eb13bfc1b963dp1076a4jsndf37b2dc83bb"
os.environ["GOOGLE_API_KEY"] = "AIzaSyArMaqnWhqTXIQRVUBgJW851tXzxnoRYHk"
os.environ["SPOTIFY_CLIENT_ID"] = "943b6c1c8113466d8d004e148b43d857"
os.environ["SPOTIFY_CLIENT_SECRET"] = "6b1492cd2795463097724b1a9458bf32"
os.environ["CF_ACCOUNT_ID"] = "b8a3bf4fc8e54308300b0fa9b11a41a1"
os.environ["CF_API_TOKEN"] = "HEMtqXKa1hsfGFT7_wR6vFseC5vs6HlQ1UtwEStF"

sys.path.append("django_backend")

import django

django.setup()

from core.management.commands.playlist_etl.e_playlist_service_track import Command as ServiceTrackCommand
from core.management.commands.playlist_etl.g_aggregate import Command as AggregateCommand
from core.management.commands.playlist_etl.h_clear_gql_cache import Command as ClearGqlCacheCommand
from core.management.commands.playlist_etl.i_warm_gql_cache import Command as WarmGqlCacheCommand


def fix_production_etl():
    """Fix the production ETL pipeline by running missing steps"""

    print("🔧 Fixing Production ETL Pipeline")
    print("=" * 50)

    try:
        print("📊 Step 1: Re-creating service tracks (Apple Music missing)...")
        ServiceTrackCommand().handle()
        print("   ✅ Service tracks created successfully")

        print("\n🔄 Step 2: Re-running aggregation to create TuneMeld playlists...")
        AggregateCommand().handle()
        print("   ✅ Aggregation completed successfully")

        print("\n🗑️  Step 3: Clearing GraphQL cache...")
        ClearGqlCacheCommand().handle()
        print("   ✅ GraphQL cache cleared")

        print("\n🔥 Step 4: Warming GraphQL cache...")
        WarmGqlCacheCommand().handle()
        print("   ✅ GraphQL cache warmed")

        print("\n🎉 Production ETL fix completed successfully!")
        print("   - Apple Music playlists should now exist")
        print("   - TuneMeld aggregated playlists should be created")
        print("   - GraphQL cache refreshed with correct YouTube URLs")

    except Exception as e:
        print(f"❌ ETL fix failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    fix_production_etl()
