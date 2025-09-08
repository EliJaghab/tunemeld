from datetime import datetime, timezone

from core.models.f_track import Track
from core.services.spotify_service import get_spotify_track_view_count
from core.utils.utils import get_logger
from core.utils.webdriver import get_cached_webdriver
from django.core.management.base import BaseCommand

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Extract view counts from Spotify for all tracks with Spotify URLs"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, help="Limit number of tracks to process")

    def handle(self, *args, **options) -> dict[str, dict]:
        limit = options.get("limit")

        tracks = Track.objects.filter(spotify_url__isnull=False).distinct().order_by("isrc")
        if limit:
            tracks = tracks[:limit]

        tracks = list(tracks)
        logger.info(f"Processing {len(tracks)} Spotify tracks")

        results: dict[str, dict] = {}
        webdriver = None

        try:
            webdriver = get_cached_webdriver()

            for _i, track in enumerate(tracks, 1):
                try:
                    view_count = get_spotify_track_view_count(track.spotify_url)
                    if view_count is not None:
                        results[track.isrc] = {
                            "service": "spotify",
                            "view_count": view_count,
                            "url": track.spotify_url,
                            "timestamp": datetime.now(timezone.utc),
                        }
                        logger.info(f"Spotify {track.isrc}: {view_count:,}")
                except Exception as e:
                    logger.error(f"Error {track.isrc}: {e}")

        finally:
            if webdriver:
                webdriver.close_driver()

        logger.info(f"Extracted {len(results)} Spotify view counts")
        return results
