import concurrent.futures
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from core.constants import ServiceName
from core.models.genre_service import Service
from core.models.playlist import Playlist
from core.models.track import Track
from core.models.view_counts import HistoricalTrackViewCount
from core.services.spotify_service import get_spotify_track_view_count
from core.services.youtube_service import get_youtube_track_view_count
from core.utils.utils import get_logger
from django.core.management.base import BaseCommand, CommandError
from django.db import models
from django.utils import timezone

logger = get_logger(__name__)


@dataclass
class ServiceStats:
    attempted: int = 0
    successful: int = 0
    authentication_errors: int = 0
    rate_limit_errors: int = 0
    parsing_errors: int = 0
    missing_data_errors: int = 0
    network_errors: int = 0
    other_errors: int = 0
    error_messages: dict = None

    def __post_init__(self):
        if self.error_messages is None:
            self.error_messages = {}

    @property
    def total_failed(self) -> int:
        return self.attempted - self.successful

    @property
    def success_rate(self) -> float:
        return (self.successful / self.attempted) if self.attempted > 0 else 0.0

    def add_error_message(self, error_message: str):
        """Track frequency of specific error messages."""
        if error_message in self.error_messages:
            self.error_messages[error_message] += 1
        else:
            self.error_messages[error_message] = 1


@dataclass
class ProcessingStats:
    total_tracks_processed: int = 0
    tracks_with_spotify_urls: int = 0
    tracks_with_youtube_urls: int = 0
    spotify: ServiceStats = None
    youtube: ServiceStats = None

    def __post_init__(self):
        if self.spotify is None:
            self.spotify = ServiceStats()
        if self.youtube is None:
            self.youtube = ServiceStats()

    @property
    def overall_success_rate(self) -> float:
        total_attempts = self.spotify.attempted + self.youtube.attempted
        total_successful = self.spotify.successful + self.youtube.successful
        return (total_successful / total_attempts) if total_attempts > 0 else 0.0


class Command(BaseCommand):
    help = "Extract historical view counts for all tracks with parallel processing"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, help="Limit tracks to process for testing")

    def handle(self, *args, **options):
        start_time = time.time()
        limit = options.get("limit")
        failure_threshold = 0.25

        tunemeld_isrcs = set(
            Playlist.objects.filter(service__name=ServiceName.TUNEMELD).values_list("isrc", flat=True).distinct()
        )

        if not tunemeld_isrcs:
            logger.warning("No TuneMeld playlist tracks found. Ensure playlist aggregation has run.")
            return

        tracks = (
            Track.objects.filter(isrc__in=tunemeld_isrcs)
            .filter(models.Q(spotify_url__isnull=False) | models.Q(youtube_url__isnull=False))
            .order_by("isrc")
        )

        if limit:
            tracks = tracks[:limit]

        tracks_list = list(tracks)
        logger.info(f"Found {len(tunemeld_isrcs)} unique TuneMeld playlist tracks")
        logger.info(f"Processing {len(tracks_list)} tracks with valid URLs using 3 workers...")
        logger.info("Fail-fast enabled: Will terminate if >25% of tracks fail")

        spotify_service = Service.objects.get(name=ServiceName.SPOTIFY)
        youtube_service = Service.objects.get(name=ServiceName.YOUTUBE)
        stats = ProcessingStats()

        # Count tracks with URLs
        for track in tracks_list:
            if track.spotify_url:
                stats.tracks_with_spotify_urls += 1
            if track.youtube_url:
                stats.tracks_with_youtube_urls += 1

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for track in tracks_list:
                future = executor.submit(self.process_track, track, spotify_service, youtube_service)
                futures.append(future)

            for completed, future in enumerate(concurrent.futures.as_completed(futures), start=1):
                try:
                    result = future.result()
                    stats.total_tracks_processed += 1

                    # Update service-specific stats
                    if "spotify" in result:
                        spotify_result = result["spotify"]
                        stats.spotify.attempted += 1
                        if spotify_result["success"]:
                            stats.spotify.successful += 1
                        else:
                            error_type = spotify_result["error_type"]
                            error_message = spotify_result["error_message"]
                            stats.spotify.add_error_message(error_message)

                            if error_type == "authentication":
                                stats.spotify.authentication_errors += 1
                            elif error_type == "rate_limit":
                                stats.spotify.rate_limit_errors += 1
                            elif error_type == "parsing":
                                stats.spotify.parsing_errors += 1
                            elif error_type == "missing_data":
                                stats.spotify.missing_data_errors += 1
                            elif error_type == "network":
                                stats.spotify.network_errors += 1
                            else:
                                stats.spotify.other_errors += 1

                    if "youtube" in result:
                        youtube_result = result["youtube"]
                        stats.youtube.attempted += 1
                        if youtube_result["success"]:
                            stats.youtube.successful += 1
                        else:
                            error_type = youtube_result["error_type"]
                            error_message = youtube_result["error_message"]
                            stats.youtube.add_error_message(error_message)

                            if error_type == "authentication":
                                stats.youtube.authentication_errors += 1
                            elif error_type == "rate_limit":
                                stats.youtube.rate_limit_errors += 1
                            elif error_type == "parsing":
                                stats.youtube.parsing_errors += 1
                            elif error_type == "missing_data":
                                stats.youtube.missing_data_errors += 1
                            elif error_type == "network":
                                stats.youtube.network_errors += 1
                            else:
                                stats.youtube.other_errors += 1

                    # Check fail-fast condition every 10 tracks
                    if completed % 10 == 0:
                        overall_success = stats.overall_success_rate
                        rate_limit_count = stats.spotify.rate_limit_errors + stats.youtube.rate_limit_errors
                        logger.info(
                            f"Completed {completed}/{len(tracks_list)} tracks... "
                            f"Overall success rate: {overall_success * 100:.1f}% "
                            f"(Rate limited: {rate_limit_count})"
                        )

                        failure_rate = 1 - overall_success
                        if completed >= 20 and failure_rate > failure_threshold:
                            total_attempts = stats.spotify.attempted + stats.youtube.attempted
                            if rate_limit_count / max(total_attempts, 1) > 0.15:
                                logger.warning(
                                    f"High rate limiting detected "
                                    f"({rate_limit_count}/{total_attempts}). "
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
                    stats.total_tracks_processed += 1

        duration = time.time() - start_time
        avg_per_track = duration / len(tracks_list) if tracks_list else 0

        # Print comprehensive summary
        self._print_comprehensive_summary(stats, duration, avg_per_track, len(tracks_list))

        # Check if pipeline should fail due to excessive non-rate-limit failures
        total_attempts = stats.spotify.attempted + stats.youtube.attempted
        rate_limit_count = stats.spotify.rate_limit_errors + stats.youtube.rate_limit_errors
        failure_rate = 1 - stats.overall_success_rate

        if failure_rate > failure_threshold and rate_limit_count / max(total_attempts, 1) <= 0.15:
            raise CommandError(f"Pipeline completed but {failure_rate:.1%} failure rate exceeds acceptable threshold")

    def process_track(self, track, spotify_service, youtube_service):
        """Process a track with comprehensive error handling and detailed error categorization."""
        result = {}

        # Process Spotify
        if track.spotify_url:
            result["spotify"] = self._process_service_track(
                track, track.spotify_url, spotify_service, "Spotify", get_spotify_track_view_count
            )

        # Process YouTube
        if track.youtube_url:
            result["youtube"] = self._process_service_track(
                track, track.youtube_url, youtube_service, "YouTube", get_youtube_track_view_count
            )

        return result

    def _process_service_track(self, track, url, service, service_name, get_count_func):
        """Process a single service track and categorize any errors."""
        try:
            count = get_count_func(url)
            if count:
                HistoricalTrackViewCount.objects.update_or_create(
                    isrc=track.isrc,
                    service=service,
                    recorded_date=timezone.now().date(),
                    defaults={"current_view_count": count},
                )
                logger.info(f"{track.isrc} {service_name}: {count:,}")
                return {"success": True, "error_type": None, "error_message": None}
            else:
                logger.warning(f"{track.isrc} {service_name}: No view count returned")
                return {"success": False, "error_type": "missing_data", "error_message": "No view count returned"}

        except Exception as e:
            error_msg = str(e).lower()
            error_type = self._categorize_error(error_msg, service_name)

            if error_type == "rate_limit":
                logger.warning(f"{track.isrc} {service_name} rate limited: {e!s}")
            else:
                logger.warning(f"{track.isrc} {service_name} error ({error_type}): {e!s}")

            return {"success": False, "error_type": error_type, "error_message": str(e)}

    def _categorize_error(self, error_msg: str, service_name: str) -> str:
        """Categorize error based on error message content."""
        if service_name == "YouTube":
            if "quota exceeded" in error_msg or "rate limit hit" in error_msg or "quotaexceeded" in error_msg:
                return "rate_limit"
            elif "403" in error_msg and ("forbidden" in error_msg or "unauthorized" in error_msg):
                return "authentication"
            elif "404" in error_msg or "not found" in error_msg:
                return "missing_data"
            elif "timeout" in error_msg or "connection" in error_msg or "network" in error_msg:
                return "network"
            elif "parsing" in error_msg or "json" in error_msg or "decode" in error_msg:
                return "parsing"
        elif service_name == "Spotify":
            if "view count element not found" in error_msg:
                return "missing_data"
            elif "non-numeric view count text" in error_msg or "error converting" in error_msg:
                return "parsing"
            elif "timeout" in error_msg or "connection" in error_msg or "network" in error_msg:
                return "network"
            elif "401" in error_msg or "403" in error_msg:
                return "authentication"
            elif "empty text in view count element" in error_msg:
                return "missing_data"

        return "other"

    def _print_comprehensive_summary(
        self, stats: ProcessingStats, duration: float, avg_per_track: float, total_tracks: int
    ):
        logger.info("\n" + "=" * 80)
        logger.info("HISTORICAL TRACK VIEW COUNT ETL RESULTS")
        logger.info("=" * 80)

        logger.info(f"Processing completed in {duration:.1f} seconds ({avg_per_track:.2f}s per track)")
        logger.info(f"Total tracks processed: {total_tracks}")
        logger.info(f"Tracks with Spotify URLs: {stats.tracks_with_spotify_urls}")
        logger.info(f"Tracks with YouTube URLs: {stats.tracks_with_youtube_urls}")
        logger.info(f"Overall success rate: {stats.overall_success_rate * 100:.1f}%")

        logger.info("\nBREAKDOWN BY SERVICE:")
        logger.info("-" * 40)

        if stats.spotify.attempted > 0:
            logger.info(
                f"Spotify: {stats.spotify.successful}/{stats.spotify.attempted} successful "
                f"({stats.spotify.success_rate * 100:.1f}%)"
            )
            if stats.spotify.total_failed > 0:
                logger.info("  Failure breakdown:")
                if stats.spotify.authentication_errors > 0:
                    logger.info(f"    Authentication errors: {stats.spotify.authentication_errors}")
                if stats.spotify.rate_limit_errors > 0:
                    logger.info(f"    Rate limit errors: {stats.spotify.rate_limit_errors}")
                if stats.spotify.parsing_errors > 0:
                    logger.info(f"    Parsing errors: {stats.spotify.parsing_errors}")
                if stats.spotify.missing_data_errors > 0:
                    logger.info(f"    Missing data errors: {stats.spotify.missing_data_errors}")
                if stats.spotify.network_errors > 0:
                    logger.info(f"    Network errors: {stats.spotify.network_errors}")
                if stats.spotify.other_errors > 0:
                    logger.info(f"    Other errors: {stats.spotify.other_errors}")
        else:
            logger.info("Spotify: No tracks attempted")

        if stats.youtube.attempted > 0:
            logger.info(
                f"YouTube: {stats.youtube.successful}/{stats.youtube.attempted} successful "
                f"({stats.youtube.success_rate * 100:.1f}%)"
            )
            if stats.youtube.total_failed > 0:
                logger.info("  Failure breakdown:")
                if stats.youtube.authentication_errors > 0:
                    logger.info(f"    Authentication errors: {stats.youtube.authentication_errors}")
                if stats.youtube.rate_limit_errors > 0:
                    logger.info(f"    Rate limit errors: {stats.youtube.rate_limit_errors}")
                if stats.youtube.parsing_errors > 0:
                    logger.info(f"    Parsing errors: {stats.youtube.parsing_errors}")
                if stats.youtube.missing_data_errors > 0:
                    logger.info(f"    Missing data errors: {stats.youtube.missing_data_errors}")
                if stats.youtube.network_errors > 0:
                    logger.info(f"    Network errors: {stats.youtube.network_errors}")
                if stats.youtube.other_errors > 0:
                    logger.info(f"    Other errors: {stats.youtube.other_errors}")
        else:
            logger.info("YouTube: No tracks attempted")

        self._print_error_message_analysis(stats)

        logger.info("=" * 80)

    def _print_error_message_analysis(self, stats: ProcessingStats):
        if stats.spotify.error_messages or stats.youtube.error_messages:
            logger.info("\nDETAILED ERROR MESSAGE ANALYSIS:")
            logger.info("-" * 40)

        if stats.spotify.error_messages:
            logger.info("Spotify error messages:")
            sorted_errors = sorted(stats.spotify.error_messages.items(), key=lambda x: x[1], reverse=True)
            for error_msg, count in sorted_errors:
                logger.info(f"  {count}x: {error_msg}")

        if stats.youtube.error_messages:
            logger.info("YouTube error messages:")
            sorted_errors = sorted(stats.youtube.error_messages.items(), key=lambda x: x[1], reverse=True)
            for error_msg, count in sorted_errors:
                logger.info(f"  {count}x: {error_msg}")

        self._print_failure_insights(stats)

    def _print_failure_insights(self, stats: ProcessingStats):
        insights = []

        if stats.spotify.attempted > 0:
            if stats.spotify.parsing_errors > stats.spotify.successful * 0.1:
                insights.append("High Spotify parsing errors - check if page structure changed")
            if stats.spotify.missing_data_errors > stats.spotify.successful * 0.2:
                insights.append("Many Spotify tracks missing view count data - investigate selector changes")
            if stats.spotify.authentication_errors > 0:
                insights.append("Spotify authentication issues detected - check credentials")

        if stats.youtube.attempted > 0:
            if stats.youtube.rate_limit_errors > stats.youtube.attempted * 0.3:
                insights.append("High YouTube rate limiting - consider reducing request frequency")
            if stats.youtube.authentication_errors > 0:
                insights.append("YouTube authentication issues - check API key quotas")
            if stats.youtube.missing_data_errors > stats.youtube.successful * 0.1:
                insights.append("YouTube missing data errors - some videos may be private/deleted")

        if insights:
            logger.info("\nACTIONABLE INSIGHTS:")
            logger.info("-" * 40)
            for insight in insights:
                logger.info(f"{insight}")
