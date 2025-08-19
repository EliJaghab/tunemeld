"""
Phase F: Generate Aggregate Playlists
"""

from typing import Any
from collections import defaultdict

from core.models import Genre, PlaylistTrack, Track
from django.core.management.base import BaseCommand
from django.db.models import Count

from playlist_etl.helpers import get_logger

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Generate cross-service aggregate playlists"

    def handle(self, *args: Any, **options: Any) -> None:
        logger.info("Starting aggregate playlist generation...")
        
        cross_service_matches = self.find_cross_service_isrcs()
        
        logger.info("Aggregate playlist generation complete")

    def find_cross_service_isrcs(self):
        """Find ISRCs that appear in multiple playlists (cross-service matches)."""
        
        # Find ISRCs that appear more than once across all playlists
        duplicate_isrcs = (
            PlaylistTrack.objects.filter(isrc__isnull=False)
            .values("isrc", "genre")
            .annotate(service_count=Count("service", distinct=True))
            .filter(service_count__gt=1)
        )
        
        cross_service_matches = defaultdict(list)
        
        for item in duplicate_isrcs:
            isrc = item["isrc"]
            genre = item["genre"]
            
            # Get all playlist entries for this ISRC in this genre
            playlist_entries = PlaylistTrack.objects.filter(
                isrc=isrc, 
                genre_id=genre
            ).select_related("service")
            
            # Map to track
            try:
                track = Track.objects.get(isrc=isrc)
                
                # Collect service positions
                service_positions = {}
                for entry in playlist_entries:
                    service_positions[entry.service.name] = entry.position
                
                cross_service_matches[genre].append({
                    "isrc": isrc,
                    "track": track,
                    "service_positions": service_positions
                })
                
            except Track.DoesNotExist:
                logger.warning(f"Track with ISRC {isrc} not found")
                continue
        
        # Log results
        for genre_id, matches in cross_service_matches.items():
            genre = Genre.objects.get(id=genre_id)
            logger.info(f"{genre.name}: {len(matches)} cross-service matches")
            
            for match in matches[:3]:  # Show first 3
                logger.info(f"  {match['track'].track_name} - {match['service_positions']}")
        
        return cross_service_matches