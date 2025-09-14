import concurrent.futures
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from core.models.b_genre_service import Service
from core.models.f_track import Track
from core.models.z_view_counts import HistoricalTrackViewCount
from core.services.spotify_service import get_spotify_track_view_count
from core.services.youtube_service import get_youtube_track_view_count
from core.utils.constants import ServiceName
from core.utils.utils import get_logger
from django.core.management.base import BaseCommand, CommandError
from django.db import models
from django.utils import timezone

logger = get_logger(__name__)


@dataclass
class ProcessingStats:
    total_processed: int = 0
    successful_retrievals: int = 0
    failed_retrievals: int = 0
    rate_limited_failures: int = 0

    @property
    def failure_rate(self) -> float:
        if self.total_processed == 0:
            return 0.0
        return self.failed_retrievals / self.total_processed


class Command(BaseCommand):
    help = "Extract historical view counts for all tracks with parallel processing"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, help="Limit tracks to process for testing")

    def handle(self, *args, **options):
        start_time = time.time()
        limit = options.get("limit")
        failure_threshold = 0.25

        tracks = Track.objects.filter(
            models.Q(spotify_url__isnull=False) | models.Q(youtube_url__isnull=False)
        ).order_by("isrc")
        if limit:
            tracks = tracks[:limit]

        tracks_list = list(tracks)
        logger.info(f"Processing {len(tracks_list)} tracks with 3 workers...")
        logger.info("Fail-fast enabled: Will terminate if >25% of tracks fail")

        spotify_service = Service.objects.get(name=ServiceName.SPOTIFY)
        youtube_service = Service.objects.get(name=ServiceName.YOUTUBE)
        stats = ProcessingStats()

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for track in tracks_list:
                future = executor.submit(self._process_track_safe, track, spotify_service, youtube_service)
                futures.append(future)

            for completed, future in enumerate(concurrent.futures.as_completed(futures), start=1):
                try:
                    result = future.result()
                    stats.total_processed += 1

                    if result["success"]:
                        stats.successful_retrievals += result["successful_counts"]
                    else:
                        stats.failed_retrievals += 1
                        if result.get("rate_limited", False):
                            stats.rate_limited_failures += 1

                    # Check fail-fast condition every 10 tracks
                    if completed % 10 == 0:
                        failure_rate = stats.failure_rate
                        logger.info(
                            f"Completed {completed}/{len(tracks_list)} tracks... "
                            f"Success rate: {(1 - failure_rate) * 100:.1f}% "
                            f"(Rate limited: {stats.rate_limited_failures})"
                        )

                        if completed >= 20 and failure_rate > failure_threshold:
                            if stats.rate_limited_failures / stats.total_processed > 0.15:
                                logger.warning(
                                    f"High rate limiting detected "
                                    f"({stats.rate_limited_failures}/{stats.total_processed}). "
                                    f"This is expected - continuing without failing."
                                )
                            else:
                                logger.error(
                                    f"Failure rate {failure_rate:.1%} exceeds threshold {failure_threshold:.1%}"
                                )
                                raise CommandError(
                                    f"Pipeline terminated: {failure_rate:.1%} failure rate "
                                    f"exceeds {failure_threshold:.1%} threshold"
                                )

                except Exception as e:
                    logger.error(f"Unexpected error processing track: {e}")
                    stats.total_processed += 1
                    stats.failed_retrievals += 1

        duration = time.time() - start_time
        avg_per_track = duration / len(tracks_list) if tracks_list else 0
        success_rate = (1 - stats.failure_rate) * 100

        logger.info(
            f"Completed processing {len(tracks_list)} tracks in {duration:.1f} seconds ({avg_per_track:.2f}s per track)"
        )
        logger.info(f"Success rate: {success_rate:.1f}% ({stats.successful_retrievals} successful retrievals)")
        logger.info(f"Rate limited failures: {stats.rate_limited_failures}/{stats.total_processed}")

        if stats.failure_rate > failure_threshold and stats.rate_limited_failures / stats.total_processed <= 0.15:
            raise CommandError(
                f"Pipeline completed but {stats.failure_rate:.1%} failure rate exceeds acceptable threshold"
            )

    def _process_track_safe(self, track, spotify_service, youtube_service):
        """Process a track with comprehensive error handling and rate limit detection."""
        result = {"success": False, "successful_counts": 0, "rate_limited": False, "errors": []}

        # Process Spotify
        if track.spotify_url:
            try:
                count = get_spotify_track_view_count(track.spotify_url)
                if count:
                    HistoricalTrackViewCount.objects.update_or_create(
                        isrc=track.isrc,
                        service=spotify_service,
                        recorded_date=timezone.now().date(),
                        defaults={"current_view_count": count},
                    )
                    logger.info(f"{track.isrc} Spotify: {count:,}")
                    result["successful_counts"] += 1
            except Exception as e:
                error_msg = f"Spotify error for {track.isrc}: {e!s}"
                logger.warning(error_msg)
                result["errors"].append(error_msg)

        # Process YouTube
        if track.youtube_url:
            try:
                count = get_youtube_track_view_count(track.youtube_url)
                if count:
                    HistoricalTrackViewCount.objects.update_or_create(
                        isrc=track.isrc,
                        service=youtube_service,
                        recorded_date=timezone.now().date(),
                        defaults={"current_view_count": count},
                    )
                    logger.info(f"{track.isrc} YouTube: {count:,}")
                    result["successful_counts"] += 1
            except Exception as e:
                error_msg = str(e).lower()
                is_rate_limited = any(
                    keyword in error_msg
                    for keyword in ["quota", "rate limit", "429", "too many requests", "quotaExceeded"]
                )

                if is_rate_limited:
                    result["rate_limited"] = True
                    logger.warning(f"{track.isrc} YouTube rate limited: {e!s}")
                else:
                    logger.warning(f"{track.isrc} YouTube error: {e!s}")

                result["errors"].append(f"YouTube error for {track.isrc}: {e!s}")

        # Determine overall success
        has_urls = bool(track.spotify_url or track.youtube_url)
        result["success"] = has_urls and result["successful_counts"] > 0

        return result

    def _process_track(self, track, spotify_service, youtube_service):
        """Legacy method - kept for compatibility but not used in new implementation."""
        if track.spotify_url:
            count = get_spotify_track_view_count(track.spotify_url)
            if count:
                HistoricalTrackViewCount.objects.update_or_create(
                    isrc=track.isrc,
                    service=spotify_service,
                    recorded_date=timezone.now().date(),
                    defaults={"current_view_count": count},
                )
                logger.info(f"{track.isrc} Spotify: {count:,}")

        if track.youtube_url:
            count = get_youtube_track_view_count(track.youtube_url)
            if count:
                HistoricalTrackViewCount.objects.update_or_create(
                    isrc=track.isrc,
                    service=youtube_service,
                    recorded_date=timezone.now().date(),
                    defaults={"current_view_count": count},
                )
                logger.info(f"{track.isrc} YouTube: {count:,}")
