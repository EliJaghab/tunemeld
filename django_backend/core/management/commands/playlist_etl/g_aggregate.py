import uuid
from collections import defaultdict
from typing import Any

from core.models import Genre, Service, ServiceTrack
from core.models import PlaylistModel as Playlist
from core.utils.utils import get_logger
from django.core.management.base import BaseCommand
from django.db.models import Count

from playlist_etl.constants import ServiceName

logger = get_logger(__name__)

# Service ranking priority (highest to lowest)
SERVICE_RANK_PRIORITY = [
    ServiceName.APPLE_MUSIC,
    ServiceName.SOUNDCLOUD,
    ServiceName.SPOTIFY,
]


class Command(BaseCommand):
    help = "Generate cross-service aggregate playlists"

    def handle(self, *args: Any, etl_run_id: uuid.UUID, **options: Any) -> None:
        logger.info("Starting aggregate playlist generation...")

        cross_service_matches = self.find_cross_service_isrcs(etl_run_id)
        self.create_aggregate_playlists(cross_service_matches, etl_run_id)

    def find_cross_service_isrcs(self, etl_run_id: uuid.UUID) -> dict[int, list[dict]]:
        """Find ISRCs that appear in multiple playlists (cross-service matches)."""

        duplicate_isrcs = (
            ServiceTrack.objects.filter(etl_run_id=etl_run_id)
            .values("isrc", "genre")
            .annotate(service_count=Count("service", distinct=True))
            .filter(service_count__gt=1)
        )

        cross_service_matches = defaultdict(list)

        for item in duplicate_isrcs:
            isrc = item["isrc"]
            genre_id = item["genre"]

            service_tracks = ServiceTrack.objects.filter(
                isrc=isrc, genre_id=genre_id, etl_run_id=etl_run_id
            ).select_related("service")

            # Collect service positions
            service_positions = {}
            for service_track in service_tracks:
                service_positions[service_track.service.name] = service_track.position

            # Determine aggregate rank based on service priority
            aggregate_rank = self.get_aggregate_rank(service_positions)

            cross_service_matches[genre_id].append(
                {
                    "isrc": isrc,
                    "service_positions": service_positions,
                    "service_tracks": service_tracks,
                    "aggregate_rank": aggregate_rank,
                }
            )

        return cross_service_matches

    def get_aggregate_rank(self, service_positions: dict[str, int]) -> float:
        """Get aggregate rank based on highest priority service."""
        for service_name in SERVICE_RANK_PRIORITY:
            if service_name in service_positions:
                return float(service_positions[service_name])

        # Fallback to lowest position if no priority service found
        return float(min(service_positions.values())) if service_positions else float("inf")

    def create_aggregate_playlists(self, cross_service_matches: dict[int, list[dict]], etl_run_id: uuid.UUID) -> None:
        """Create aggregate playlist entries for cross-service tracks."""

        aggregate_service, _ = Service.objects.get_or_create(name=ServiceName.TUNEMELD)

        for genre_id, matches in cross_service_matches.items():
            genre = Genre.objects.get(id=genre_id)

            sorted_matches = sorted(matches, key=lambda x: x["aggregate_rank"])

            playlist_entries = []
            for position, match in enumerate(sorted_matches, 1):
                # Use the first ServiceTrack as the reference for the aggregate playlist
                reference_service_track = match["service_tracks"].first()

                playlist_entry = Playlist(
                    service=aggregate_service,
                    genre=genre,
                    position=position,
                    isrc=match["isrc"],
                    service_track=reference_service_track,
                    etl_run_id=etl_run_id,
                )
                playlist_entries.append(playlist_entry)

            Playlist.objects.bulk_create(playlist_entries)
            logger.info(f"Created aggregate playlist for {genre.name}: {len(playlist_entries)} tracks")
