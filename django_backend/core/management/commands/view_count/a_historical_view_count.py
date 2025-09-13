import concurrent.futures
import time
from concurrent.futures import ThreadPoolExecutor

from core.models.b_genre_service import Service
from core.models.f_track import Track
from core.models.z_view_counts import HistoricalTrackViewCount
from core.services.spotify_service import get_spotify_track_view_count
from core.services.youtube_service import get_youtube_track_view_count
from core.utils.utils import get_logger
from django.core.management.base import BaseCommand
from django.db import models
from django.utils import timezone

from playlist_etl.constants import ServiceName

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Extract historical view counts for all tracks with parallel processing"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, help="Limit tracks to process for testing")

    def handle(self, *args, **options):
        start_time = time.time()
        limit = options.get("limit")

        tracks = Track.objects.filter(
            models.Q(spotify_url__isnull=False) | models.Q(youtube_url__isnull=False)
        ).order_by("isrc")
        if limit:
            tracks = tracks[:limit]

        tracks_list = list(tracks)
        logger.info(f"Processing {len(tracks_list)} tracks with 3 workers...")

        spotify_service = Service.objects.get(name=ServiceName.SPOTIFY)
        youtube_service = Service.objects.get(name=ServiceName.YOUTUBE)

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for track in tracks_list:
                future = executor.submit(self._process_track, track, spotify_service, youtube_service)
                futures.append(future)

            completed = 0
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                    completed += 1
                    if completed % 10 == 0:
                        logger.info(f"Completed {completed}/{len(tracks_list)} tracks...")
                except Exception as e:
                    logger.error(f"Error processing track: {e}")
                    # Fail fast on API quota/auth errors
                    if "403" in str(e) or "401" in str(e) or "429" in str(e):
                        logger.error("Critical API error detected - failing fast to prevent resource waste")
                        raise

        duration = time.time() - start_time
        avg_per_track = duration / len(tracks_list) if tracks_list else 0
        logger.info(f"Processed {len(tracks_list)} tracks in {duration:.1f} seconds ({avg_per_track:.2f}s per track)")

    def _process_track(self, track, spotify_service, youtube_service):
        try:
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
        except Exception as e:
            logger.error(f"Error processing track {track.isrc}: {e}")
            # Fail fast on API quota/auth errors in worker threads
            if "403" in str(e) or "401" in str(e) or "429" in str(e):
                logger.error("Critical API error detected in worker thread - failing fast to prevent resource waste")
                raise
