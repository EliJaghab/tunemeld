#!/usr/bin/env python3
"""
YouTube API Quota Optimization Strategy

Current issue: Heavy quota usage during ETL runs
Solution: Batch processing, smart caching, and retry logic
"""

import os
import sys

sys.path.append("django_backend")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django

django.setup()

from core.models import Track


def analyze_youtube_needs():
    """Analyze how many tracks need YouTube URLs and estimate quota usage"""

    print("🎵 YouTube URL Coverage Analysis")
    print("=" * 50)

    total_tracks = Track.objects.count()
    tracks_with_youtube = Track.objects.filter(youtube_url__isnull=False).count()
    tracks_without_youtube = Track.objects.filter(youtube_url__isnull=True).count()

    print("📊 Current status:")
    print(f"   Total tracks: {total_tracks}")
    print(f"   With YouTube URLs: {tracks_with_youtube}")
    print(f"   Without YouTube URLs: {tracks_without_youtube}")
    print(f"   Coverage: {(tracks_with_youtube / total_tracks) * 100:.1f}%")

    # Estimate quota needed for full coverage
    quota_needed = tracks_without_youtube * 100  # 100 units per search
    daily_quota = 10000  # Standard free quota

    print("\n💰 Quota analysis:")
    print(f"   Quota needed for remaining tracks: {quota_needed} units")
    print(f"   Daily free quota: {daily_quota} units")
    print(f"   Days needed at current rate: {quota_needed / daily_quota:.1f}")

    # Show tracks that need YouTube URLs
    if tracks_without_youtube > 0:
        print("\n🎵 Tracks needing YouTube URLs:")
        print("-" * 40)
        missing_tracks = Track.objects.filter(youtube_url__isnull=True).values("track_name", "artist_name")[
            :10
        ]  # Show first 10

        for i, track in enumerate(missing_tracks, 1):
            print(f'{i:2d}. "{track["track_name"]}" by {track["artist_name"]}')

        if tracks_without_youtube > 10:
            print(f"    ... and {tracks_without_youtube - 10} more")


def suggest_optimizations():
    """Suggest quota optimization strategies"""

    print("\n💡 Optimization Strategies:")
    print("=" * 50)

    strategies = [
        ("🎯 Batch Processing", "Process YouTube URLs in smaller daily batches (e.g., 50 tracks/day)"),
        ("⏰ Off-peak Timing", "Run YouTube fetching at off-peak hours to avoid competition"),
        ("🎪 Smart Caching", "Cache successful searches indefinitely, failed searches for 24h"),
        ("🔄 Retry Logic", "Retry failed searches on subsequent days"),
        ("📊 Quota Monitoring", "Track daily quota usage and stop before exhaustion"),
        ("💳 Enable Billing", "Enable billing for 1M units/day (costs ~$0-5/month for your usage)"),
        ("🎮 Alternative APIs", "Consider Spotify Web API + web scraping as fallback"),
    ]

    for title, description in strategies:
        print(f"{title}")
        print(f"   {description}")
        print()


def create_quota_efficient_approach():
    """Create a more quota-efficient YouTube URL fetching approach"""

    print("\n🚀 Recommended Implementation:")
    print("=" * 50)

    implementation = """
1. **Modify f_track.py to be quota-aware:**
   - Check remaining daily quota before making calls
   - Limit YouTube searches to N per day (e.g., 50)
   - Log quota usage and remaining capacity

2. **Add quota tracking:**
   - Store daily quota usage in cache/DB
   - Reset counter at midnight Pacific
   - Skip YouTube fetching if quota low

3. **Implement graceful degradation:**
   - Create tracks without YouTube URLs if quota exhausted
   - Schedule retry for next day
   - Don't block ETL pipeline on YouTube failures

4. **Enable billing (recommended):**
   - Go to Google Cloud Console
   - Enable billing for your project
   - Quota increases to 1,000,000 units/day
   - Cost is minimal (~$0.001 per 100 searches)
"""

    print(implementation)


if __name__ == "__main__":
    analyze_youtube_needs()
    suggest_optimizations()
    create_quota_efficient_approach()
