#!/usr/bin/env python3
"""
AGGRESSIVE cleanup of placeholder URLs in production database
"""

import os
import sys
import django

# Force production database settings
os.environ["DATABASE_URL"] = "postgresql://postgres:TMvEddPnHxNAtoxkPZmYaKYYawSScutY@switchback.proxy.rlwy.net:39383/railway"
os.environ["DJANGO_SETTINGS_MODULE"] = "core.settings" 
os.environ["DEBUG"] = "False"

sys.path.append("django_backend")
django.setup()

from core.models import Track
from django.db import transaction

def aggressive_cleanup():
    """Aggressively clean ALL placeholder YouTube URLs"""
    
    print("🧹 AGGRESSIVE PRODUCTION DATABASE CLEANUP")
    print("=" * 60)
    
    with transaction.atomic():
        # Find ALL placeholder URLs
        placeholders = Track.objects.filter(youtube_url="https://youtube.com")
        count = placeholders.count()
        
        print(f"Found {count} tracks with placeholder URLs")
        
        if count > 0:
            print("Placeholder tracks:")
            for track in placeholders[:15]:  # Show first 15
                print(f"   • {track.track_name} by {track.artist_name} (ID: {track.id})")
            
            if count > 15:
                print(f"   ... and {count - 15} more")
            
            # SET ALL TO NULL
            updated = placeholders.update(youtube_url=None)
            print(f"\n✅ FORCE CLEANED {updated} placeholder URLs (set to NULL)")
            
            # Double-check
            remaining = Track.objects.filter(youtube_url="https://youtube.com").count()
            print(f"Remaining placeholders after cleanup: {remaining}")
            
            if remaining > 0:
                print("❌ STILL HAVE PLACEHOLDERS - trying individual deletion")
                # Try deleting one by one
                for track in Track.objects.filter(youtube_url="https://youtube.com"):
                    print(f"Force cleaning: {track.track_name} by {track.artist_name}")
                    track.youtube_url = None
                    track.save()
                
                final_remaining = Track.objects.filter(youtube_url="https://youtube.com").count()
                print(f"Final remaining: {final_remaining}")
            
        else:
            print("✅ No placeholder URLs found")
        
        # Final verification
        total = Track.objects.count()
        with_youtube = Track.objects.filter(youtube_url__isnull=False).count()
        null_youtube = Track.objects.filter(youtube_url__isnull=True).count()
        
        print(f"\n📊 Final database status:")
        print(f"   Total tracks: {total}")
        print(f"   With YouTube URLs: {with_youtube}")
        print(f"   Without YouTube URLs (null): {null_youtube}")
        
        # Check for any remaining placeholders
        final_placeholders = Track.objects.filter(youtube_url="https://youtube.com").count()
        if final_placeholders == 0:
            print("🎉 SUCCESS: All placeholder URLs removed!")
        else:
            print(f"❌ FAILED: {final_placeholders} placeholder URLs still remain")

if __name__ == "__main__":
    aggressive_cleanup()