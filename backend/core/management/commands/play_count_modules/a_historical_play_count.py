import time
from collections import Counter
from collections.abc import Callable
from typing import TYPE_CHECKING

from core.api.genre_service_api import get_service
from core.api.playlist import get_playlist_isrcs_by_service
from core.constants import ServiceName
from core.models.play_counts import HistoricalTrackPlayCountModel
from core.models.track import TrackModel
from core.services.soundcloud_service import get_soundcloud_track_view_count
from core.services.spotify_service import get_spotify_track_view_count
from core.services.youtube_service import get_youtube_track_view_count
from core.utils.utils import get_logger, process_in_parallel
from django.core.management.base import BaseCommand
from django.db import models
from django.utils import timezone

if TYPE_CHECKING:
    from core.models.genre_service import ServiceModel

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Extract historical play counts for all tracks with parallel processing"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, help="Limit tracks to process for testing")

    def handle(self, *args, **options):
        start_time = time.time()
        limit = options.get("limit")

        tunemeld_isrcs = get_playlist_isrcs_by_service(ServiceName.TUNEMELD)

        if not tunemeld_isrcs:
            logger.warning("No TuneMeld playlist tracks found. Ensure playlist aggregation has run.")
            return

        tracks = (
            TrackModel.objects.filter(isrc__in=tunemeld_isrcs)
            .filter(
                models.Q(spotify_url__isnull=False)
                | models.Q(youtube_url__isnull=False)
                | models.Q(soundcloud_url__isnull=False)
            )
            .order_by("isrc")
        )

        if limit:
            tracks = tracks[:limit]

        tracks_list = list(tracks)
        logger.info(f"Found {len(tunemeld_isrcs)} unique TuneMeld playlist tracks")
        logger.info(f"Processing {len(tracks_list)} tracks with valid URLs using parallel processing...")

        services = {
            ServiceName.SPOTIFY: get_service(ServiceName.SPOTIFY),
            ServiceName.YOUTUBE: get_service(ServiceName.YOUTUBE),
            ServiceName.SOUNDCLOUD: get_service(ServiceName.SOUNDCLOUD),
        }

        success_count = Counter()
        error_count = Counter()
        errors = []

        results = process_in_parallel(
            items=tracks_list,
            process_func=lambda track: self.process_track(track, services),
            log_progress=True,
            progress_interval=10,
        )

        for track, track_results, exc in results:
            if exc:
                logger.error(f"Error processing track {track.isrc}: {exc}")
                errors.append(str(exc))
            elif track_results:
                for service, count in track_results:
                    if count is not None:
                        success_count[service] += 1
                    else:
                        error_count[service] += 1

        duration = time.time() - start_time
        self._print_summary(success_count, error_count, errors, duration, len(tracks_list))

    def _process_service(
        self,
        track: "TrackModel",
        service_name: str,
        url: str,
        get_count_func: Callable[[str], int],
        service_obj: "ServiceModel",
    ) -> tuple[str, int | None]:
        """Process a single service for a track."""
        try:
            count = get_count_func(url)
            HistoricalTrackPlayCountModel.objects.update_or_create(
                isrc=track.isrc,
                service=service_obj,
                recorded_date=timezone.now().date(),
                defaults={"current_play_count": count},
            )
            logger.info(f"{track.isrc} {service_name}: {count:,}")
            return (service_name, count)
        except Exception as e:
            logger.warning(f"{track.isrc} {service_name}: {e}")
            return (service_name, None)

    def process_track(
        self, track: "TrackModel", services: dict[ServiceName, "ServiceModel"]
    ) -> list[tuple[str, int | None]]:
        """Process a track and return results for all services."""
        results: list[tuple[str, int | None]] = []

        service_configs: list[tuple[ServiceName, str | None, Callable[[str], int]]] = [
            (ServiceName.SPOTIFY, track.spotify_url, get_spotify_track_view_count),
            (ServiceName.YOUTUBE, track.youtube_url, get_youtube_track_view_count),
            (ServiceName.SOUNDCLOUD, track.soundcloud_url, get_soundcloud_track_view_count),
        ]

        for service_enum, url, get_count_func in service_configs:
            if url:
                result = self._process_service(track, service_enum.value, url, get_count_func, services[service_enum])
                results.append(result)

        return results

    def _print_summary(
        self,
        success_count: Counter[str],
        error_count: Counter[str],
        errors: list[str],
        duration: float,
        total_tracks: int,
    ) -> None:
        """Print execution summary."""
        logger.info("\n" + "=" * 80)
        logger.info("HISTORICAL TRACK PLAY COUNT ETL RESULTS")
        logger.info("=" * 80)
        logger.info(f"Processing completed in {duration:.1f} seconds ({duration / total_tracks:.2f}s per track)")
        logger.info(f"Total tracks processed: {total_tracks}")

        logger.info("\nBREAKDOWN BY SERVICE:")
        logger.info("-" * 40)

        for service in [ServiceName.SPOTIFY.value, ServiceName.YOUTUBE.value, ServiceName.SOUNDCLOUD.value]:
            success = success_count[service]
            errors_num = error_count[service]
            total = success + errors_num
            if total > 0:
                logger.info(f"{service}: {success}/{total} successful ({success / total * 100:.1f}%)")

        if errors:
            logger.info(f"\nERRORS ({len(errors)} total):")
            logger.info("-" * 40)
            for error in errors:
                logger.info(f"  {error}")

        logger.info("=" * 80)
