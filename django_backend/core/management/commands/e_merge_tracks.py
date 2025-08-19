"""
Phase E: Merge Duplicate Tracks by ISRC

WHAT THIS DOES:
For each ISRC with multiple Track records:
1. Pick the best track (highest priority data source)
2. Update its missing fields from other tracks
3. Delete the duplicate tracks

DATA SOURCE PRIORITY:
1. Spotify (highest priority)
2. Apple Music 
3. SoundCloud (lowest priority)
"""

from typing import Any

from core.models import Track
from django.core.management.base import BaseCommand
from django.db.models import Count

from playlist_etl.helpers import get_logger

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Merge duplicate Track records by ISRC"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be merged without making changes",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        dry_run = options.get("dry_run", False)
        
        logger.info("Starting Track deduplication by ISRC...")
        
        duplicate_isrcs = self.find_duplicate_isrcs()
        if not duplicate_isrcs:
            logger.info("No duplicate ISRCs found")
            return
        
        logger.info(f"Found {len(duplicate_isrcs)} ISRCs with duplicates")
        
        for isrc in duplicate_isrcs:
            tracks = Track.objects.filter(isrc=isrc)
            
            # Pick the best track
            primary_track = self.choose_primary_track(tracks)
            duplicates = tracks.exclude(pk=primary_track.pk)
            
            # Update missing fields from duplicates
            self.update_missing_fields(primary_track, duplicates, dry_run)
            
            if not dry_run:
                duplicates.delete()
                logger.info(f"Merged {isrc}: kept 1, deleted {duplicates.count()}")
            else:
                logger.info(f"Would merge {isrc}: keep 1, delete {duplicates.count()}")
        
        if not dry_run:
            self.validate_unique_isrcs()

    def find_duplicate_isrcs(self):
        """Find ISRCs that have multiple Track records."""
        duplicates = (
            Track.objects.values("isrc")
            .annotate(count=Count("isrc"))
            .filter(count__gt=1)
        )
        return [item["isrc"] for item in duplicates]

    def choose_primary_track(self, tracks):
        """Pick the track with highest priority data source."""
        # Priority: Spotify > Apple Music > SoundCloud
        for track in tracks:
            if track.spotify_url:
                return track
        
        for track in tracks:
            if track.apple_music_url:
                return track
        
        return tracks.first()

    def update_missing_fields(self, primary_track, duplicates, dry_run):
        """Update missing fields in primary track from duplicates."""
        updated_fields = []
        
        for duplicate in duplicates:
            if not primary_track.spotify_url and duplicate.spotify_url:
                primary_track.spotify_url = duplicate.spotify_url
                updated_fields.append("spotify_url")
            
            if not primary_track.apple_music_url and duplicate.apple_music_url:
                primary_track.apple_music_url = duplicate.apple_music_url
                updated_fields.append("apple_music_url")
            
            if not primary_track.youtube_url and duplicate.youtube_url:
                primary_track.youtube_url = duplicate.youtube_url
                updated_fields.append("youtube_url")
            
            if not primary_track.soundcloud_url and duplicate.soundcloud_url:
                primary_track.soundcloud_url = duplicate.soundcloud_url
                updated_fields.append("soundcloud_url")
            
            if not primary_track.album_cover_url and duplicate.album_cover_url:
                primary_track.album_cover_url = duplicate.album_cover_url
                updated_fields.append("album_cover_url")
        
        if updated_fields and not dry_run:
            primary_track.save()
            logger.info(f"Updated {primary_track.isrc}: {updated_fields}")
        elif updated_fields:
            logger.info(f"Would update {primary_track.isrc}: {updated_fields}")

    def validate_unique_isrcs(self):
        """Validate that all ISRCs are unique after merging."""
        all_isrcs = list(Track.objects.values_list("isrc", flat=True))
        unique_isrcs = set(all_isrcs)
        
        total_tracks = len(all_isrcs)
        unique_count = len(unique_isrcs)
        
        if total_tracks == unique_count:
            logger.info(f"✓ VALIDATION PASSED: {total_tracks} tracks with {unique_count} unique ISRCs")
        else:
            duplicates = total_tracks - unique_count
            logger.error(f"✗ VALIDATION FAILED: {total_tracks} tracks but only {unique_count} unique ISRCs ({duplicates} duplicates remain)")
            
            # Find remaining duplicates
            remaining_duplicates = self.find_duplicate_isrcs()
            if remaining_duplicates:
                logger.error(f"Remaining duplicate ISRCs: {remaining_duplicates}")
            
            raise ValueError("Track merge validation failed: duplicate ISRCs still exist")