#!/usr/bin/env python3
"""
Clear and rewarm production GraphQL cache to fix youtube.com placeholder URLs
"""

import os
import sys

# Set production environment
os.environ["DATABASE_URL"] = (
    "postgresql://postgres:TMvEddPnHxNAtoxkPZmYaKYYawSScutY@switchback.proxy.rlwy.net:39383/railway"
)
os.environ["DJANGO_SETTINGS_MODULE"] = "core.settings"
os.environ["DEBUG"] = "False"

# Set production cache credentials
os.environ["CF_ACCOUNT_ID"] = "b8a3bf4fc8e54308300b0fa9b11a41a1"
os.environ["CF_NAMESPACE_ID"] = "12a02c4cb50a379e20e15717eb431a72"  # This might need to be updated
os.environ["CF_API_TOKEN"] = "HEMtqXKa1hsfGFT7_wR6vFseC5vs6HlQ1UtwEStF"

sys.path.append("django_backend")

import django

django.setup()

from core.management.commands.playlist_etl.h_clear_gql_cache import Command as ClearGqlCacheCommand
from core.management.commands.playlist_etl.i_warm_gql_cache import Command as WarmGqlCacheCommand


def clear_production_cache():
    """Clear and rewarm production GraphQL cache"""

    print("🎵 Clearing Production GraphQL Cache")
    print("=" * 50)

    try:
        print("🗑️  Step 1: Clearing GraphQL cache...")
        ClearGqlCacheCommand().handle()
        print("   ✅ GraphQL cache cleared successfully")

        print("\n🔥 Step 2: Warming GraphQL cache...")
        WarmGqlCacheCommand().handle()
        print("   ✅ GraphQL cache warmed successfully")

        print("\n🎉 Production GraphQL cache has been cleared and rewarmed!")
        print("   The youtube.com placeholder URLs should now be fixed.")

    except Exception as e:
        print(f"❌ Error clearing/warming cache: {e}")
        print("   This might be due to Cloudflare credentials or connection issues.")


if __name__ == "__main__":
    clear_production_cache()
