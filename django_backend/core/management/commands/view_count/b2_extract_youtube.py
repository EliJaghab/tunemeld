from datetime import datetime, timezone

from core.models.f_track import Track
from core.services.youtube_service import get_youtube_track_view_count
from core.utils.utils import get_logger
from django.core.management.base import BaseCommand

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Extract view counts from YouTube for all tracks with YouTube URLs"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, help="Limit number of tracks to process")

    def handle(self, *args, **options) -> dict[str, dict]:
        limit = options.get("limit")

        tracks = Track.objects.filter(youtube_url__isnull=False).distinct().order_by("isrc")
        if limit:
            tracks = tracks[:limit]

        tracks = list(tracks)
        logger.info(f"Processing {len(tracks)} YouTube tracks")

        results: dict[str, dict] = {}

        for _i, track in enumerate(tracks, 1):
            try:
                view_count = get_youtube_track_view_count(track.youtube_url)
                if view_count is not None:
                    results[track.isrc] = {
                        "service": "youtube",
                        "view_count": view_count,
                        "url": track.youtube_url,
                        "timestamp": datetime.now(timezone.utc),
                    }
                    logger.info(f"YouTube {track.isrc}: {view_count:,}")
            except Exception as e:
                logger.error(f"Error {track.isrc}: {e}")

        logger.info(f"Extracted {len(results)} YouTube view counts")
        return results
