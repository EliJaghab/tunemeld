from django.core.management.base import BaseCommand
from core.models import Track
from core.utils.utils import get_logger

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Remove all placeholder YouTube URLs from database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be cleaned without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        
        self.stdout.write("🧹 Cleaning placeholder YouTube URLs...")
        self.stdout.write("=" * 50)
        
        # Find all tracks with placeholder URLs
        placeholder_tracks = Track.objects.filter(youtube_url="https://youtube.com")
        count = placeholder_tracks.count()
        
        self.stdout.write(f"Found {count} tracks with placeholder URLs")
        
        if count > 0:
            if dry_run:
                self.stdout.write(f"[DRY RUN] Would clean {count} placeholder URLs")
                # Show sample tracks that would be affected
                for track in placeholder_tracks[:5]:
                    self.stdout.write(f"   Would clean: {track.track_name} by {track.artist_name}")
                if count > 5:
                    self.stdout.write(f"   ... and {count - 5} more")
            else:
                # Set placeholder URLs to None
                updated = placeholder_tracks.update(youtube_url=None)
                self.stdout.write(f"✅ Cleaned {updated} placeholder URLs (set to NULL)")
                logger.info(f"Cleaned {updated} placeholder YouTube URLs from database")
        else:
            self.stdout.write("✅ No placeholder URLs found")
        
        # Verify cleanup
        remaining = Track.objects.filter(youtube_url="https://youtube.com").count()
        total_with_urls = Track.objects.filter(youtube_url__isnull=False).count()
        total_tracks = Track.objects.count()
        
        self.stdout.write(f"\n📊 Final status:")
        self.stdout.write(f"   Total tracks: {total_tracks}")
        self.stdout.write(f"   With YouTube URLs: {total_with_urls}")
        self.stdout.write(f"   Remaining placeholders: {remaining}")
        
        if not dry_run and remaining == 0:
            self.stdout.write(self.style.SUCCESS("✅ All placeholder URLs successfully removed!"))
        elif dry_run:
            self.stdout.write(self.style.WARNING("ℹ️  This was a dry run - no changes were made"))
        elif remaining > 0:
            self.stdout.write(self.style.ERROR(f"❌ {remaining} placeholder URLs still remain"))