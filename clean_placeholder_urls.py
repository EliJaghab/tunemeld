#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'django_backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tunemeld_backend.settings')

import django
django.setup()

from core.models import Track

def clean_placeholder_urls():
    """Remove all placeholder YouTube URLs from database"""
    
    print("🧹 Cleaning placeholder YouTube URLs...")
    print("=" * 50)
    
    # Find all tracks with placeholder URLs
    placeholder_tracks = Track.objects.filter(youtube_url="https://youtube.com")
    count = placeholder_tracks.count()
    
    print(f"Found {count} tracks with placeholder URLs")
    
    if count > 0:
        # Set placeholder URLs to None
        placeholder_tracks.update(youtube_url=None)
        print(f"✅ Cleaned {count} placeholder URLs (set to NULL)")
    else:
        print("✅ No placeholder URLs found")
    
    # Verify cleanup
    remaining = Track.objects.filter(youtube_url="https://youtube.com").count()
    total_with_urls = Track.objects.filter(youtube_url__isnull=False).count()
    total_tracks = Track.objects.count()
    
    print(f"\n📊 Final status:")
    print(f"   Total tracks: {total_tracks}")
    print(f"   With YouTube URLs: {total_with_urls}")
    print(f"   Remaining placeholders: {remaining}")

if __name__ == "__main__":
    clean_placeholder_urls()