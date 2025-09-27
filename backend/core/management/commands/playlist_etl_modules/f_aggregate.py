from collections import defaultdict
from typing import Any

from core.api.genre_service_api import get_genre_by_id, get_service
from core.constants import GENRE_CONFIGS, SERVICE_CONFIGS, ServiceName
from core.models import Genre, ServiceTrack, Track
from core.models import PlaylistModel as Playlist
from core.models.playlist import RawPlaylistData
from core.utils.utils import get_logger
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from django.utils import timezone

logger = get_logger(__name__)

# Service ranking priority (highest to lowest)
SERVICE_RANK_PRIORITY = [
    ServiceName.APPLE_MUSIC,
    ServiceName.SOUNDCLOUD,
    ServiceName.SPOTIFY,
]


class Command(BaseCommand):
    help = "Generate cross-service aggregate playlists"

    def handle(self, *args: Any, **options: Any) -> None:
        logger.info("Starting aggregate playlist generation...")

        cross_service_matches = self.find_cross_service_isrcs()
        self.create_aggregate_playlists(cross_service_matches)
        self.create_tunemeld_raw_playlist_data()

    def find_cross_service_isrcs(self) -> dict[int, list[dict]]:
        duplicate_isrcs = (
            ServiceTrack.objects.all()
            .values("isrc", "genre")
            .annotate(service_count=Count("service", distinct=True))
            .filter(service_count__gt=1)
        )

        cross_service_matches = defaultdict(list)

        for item in duplicate_isrcs:
            isrc = item["isrc"]
            genre_id = item["genre"]

            service_tracks = ServiceTrack.objects.filter(isrc=isrc, genre_id=genre_id).select_related("service")

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
        # Check if track appears on all three main services
        has_all_three_services = all(
            service.value in service_positions
            for service in [ServiceName.SPOTIFY, ServiceName.APPLE_MUSIC, ServiceName.SOUNDCLOUD]
        )

        # Tracks on all three services get priority (0-999 range)
        if has_all_three_services:
            # Use highest priority service position for tracks on all three services
            for service_name in SERVICE_RANK_PRIORITY:
                if service_name.value in service_positions:
                    return float(service_positions[service_name.value])

        # Tracks on 2 services get secondary priority (1000+ range)
        else:
            for service_name in SERVICE_RANK_PRIORITY:
                if service_name.value in service_positions:
                    return 1000.0 + float(service_positions[service_name.value])

        raise ValueError(f"No valid service found in positions: {service_positions}")

    def create_aggregate_playlists(self, cross_service_matches: dict[int, list[dict]]) -> None:
        aggregate_service = get_service(ServiceName.TUNEMELD)

        with transaction.atomic():
            logger.info("Clearing existing TuneMeld aggregate playlists")
            Playlist.objects.filter(service=aggregate_service).delete()

            for genre_id, matches in cross_service_matches.items():
                genre = get_genre_by_id(genre_id)
                if not genre:
                    logger.warning(f"Genre with id {genre_id} not found, skipping")
                    continue

                sorted_matches = sorted(matches, key=lambda x: x["aggregate_rank"])

                playlist_count = 0
                for position, match in enumerate(sorted_matches, 1):
                    reference_service_track = match["service_tracks"].first()

                    Playlist.objects.update_or_create(
                        service=aggregate_service,
                        genre=genre,
                        position=position,
                        defaults={
                            "isrc": match["isrc"],
                            "service_track": reference_service_track,
                        },
                    )

                    if reference_service_track and reference_service_track.track:
                        Track.objects.filter(id=reference_service_track.track.id).update(
                            aggregate_rank=int(match["aggregate_rank"])
                        )

                    playlist_count += 1

                logger.info(f"Created aggregate playlist for {genre.name}: {playlist_count} tracks")

    def create_tunemeld_raw_playlist_data(self) -> None:
        aggregate_service = get_service(ServiceName.TUNEMELD)
        tunemeld_config = SERVICE_CONFIGS[ServiceName.TUNEMELD.value]

        genres_with_playlists = Genre.objects.filter(playlist__service=aggregate_service).distinct()

        for genre in genres_with_playlists:
            genre_display_name = GENRE_CONFIGS.get(genre.name, {}).get("display_name", genre.name.title())

            playlist_entry = (
                Playlist.objects.filter(genre=genre, service=aggregate_service)
                .select_related("service_track__track")
                .first()
            )

            if not playlist_entry or not playlist_entry.service_track:
                raise ValueError(f"Missing required playlist data for TuneMeld {genre.name} playlist")

            last_updated = timezone.now()
            formatted_date = last_updated.strftime("%b %d")
            description = (
                f"{genre_display_name} tracks seen on more than one curated playlist, last updated on {formatted_date}"
            )

            _raw_data, created = RawPlaylistData.objects.update_or_create(
                service=aggregate_service,
                genre=genre,
                defaults={
                    "playlist_url": f"https://tunemeld.com/{genre.name}",
                    "playlist_name": f"TuneMeld {genre_display_name}",
                    "playlist_cover_url": tunemeld_config["icon_url"],
                    "playlist_cover_description_text": description,
                    "data": {},
                },
            )

            logger.info(
                f"{'Created' if created else 'Updated'} TuneMeld raw playlist data for {genre.name}: {description}"
            )
