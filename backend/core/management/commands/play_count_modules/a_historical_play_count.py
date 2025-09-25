import concurrent.futures
import time
from collections import Counter
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from core.constants import ServiceName
from core.models.genre_service import Service
from core.models.play_counts import HistoricalTrackPlayCount
from core.models.playlist import Playlist
from core.models.track import Track
from core.services.soundcloud_service import get_soundcloud_track_view_count
from core.services.spotify_service import get_spotify_track_view_count
from core.services.youtube_service import get_youtube_track_view_count
from core.utils.utils import get_logger
from django.core.management.base import BaseCommand
from django.db import models
from django.utils import timezone

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Extract historical play counts for all tracks with parallel processing"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, help="Limit tracks to process for testing")

    def handle(self, *args, **options):
        start_time = time.time()
        limit = options.get("limit")

        tunemeld_isrcs = set(
            Playlist.objects.filter(service__name=ServiceName.TUNEMELD).values_list("isrc", flat=True).distinct()
        )

        if not tunemeld_isrcs:
            logger.warning("No TuneMeld playlist tracks found. Ensure playlist aggregation has run.")
            return

        tracks = (
            Track.objects.filter(isrc__in=tunemeld_isrcs)
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
        logger.info(f"Processing {len(tracks_list)} tracks with valid URLs using 3 workers...")

        services = {
            ServiceName.SPOTIFY: Service.objects.filter(name=ServiceName.SPOTIFY).order_by("-id").first(),
            ServiceName.YOUTUBE: Service.objects.filter(name=ServiceName.YOUTUBE).order_by("-id").first(),
            ServiceName.SOUNDCLOUD: Service.objects.filter(name=ServiceName.SOUNDCLOUD).order_by("-id").first(),
        }

        success_count = Counter()
        error_count = Counter()
        errors = []

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for track in tracks_list:
                future = executor.submit(self.process_track, track, services)
                futures.append(future)

            for completed, future in enumerate(concurrent.futures.as_completed(futures), start=1):
                try:
                    results = future.result()
                    for service, count in results:
                        if count is not None:
                            success_count[service] += 1
                        else:
                            error_count[service] += 1

                    # Progress update every 10 tracks
                    if completed % 10 == 0:
                        total_success = sum(success_count.values())
                        total_attempts = total_success + sum(error_count.values())
                        success_rate = (total_success / total_attempts * 100) if total_attempts else 0
                        logger.info(
                            f"Completed {completed}/{len(tracks_list)} tracks... Success rate: {success_rate:.1f}%"
                        )

                except Exception as e:
                    logger.error(f"Error processing track: {e}")
                    errors.append(str(e))

        duration = time.time() - start_time
        self._print_summary(success_count, error_count, errors, duration, len(tracks_list))

    def _process_service(
        self,
        track: "Track",
        service_name: str,
        url: str,
        get_count_func: Callable[[str], int],
        service_obj: "Service",
    ) -> tuple[str, int | None]:
        """Process a single service for a track."""
        try:
            count = get_count_func(url)
            HistoricalTrackPlayCount.objects.update_or_create(
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

    def process_track(self, track: "Track", services: dict[ServiceName, "Service"]) -> list[tuple[str, int | None]]:
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
