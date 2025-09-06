from datetime import datetime, timedelta

from core.models.b_genre_service import Service
from core.models.z_view_counts import HistoricalViewCount, ViewCount
from core.utils.utils import get_logger
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone as django_timezone

from playlist_etl.constants import ServiceName

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Load view count data into PostgreSQL tables"

    def handle(self, *args, **options):
        logger.info("Load view counts command - use this to load extracted data")

    def load_view_counts(self, spotify_data: dict[str, dict], youtube_data: dict[str, dict]) -> dict:
        try:
            spotify_service = Service.objects.get(name=ServiceName.SPOTIFY)
            youtube_service = Service.objects.get(name=ServiceName.YOUTUBE)
        except Service.DoesNotExist as e:
            logger.error(f"Error: Required service not found in database: {e}")
            return {"success": False, "error": str(e)}

        stats = {
            "spotify_loaded": 0,
            "spotify_errors": 0,
            "youtube_loaded": 0,
            "youtube_errors": 0,
            "total_loaded": 0,
            "total_errors": 0,
        }

        logger.info(f"Loading {len(spotify_data)} Spotify view counts...")
        for isrc, data in spotify_data.items():
            success = self._load_single_view_count(
                isrc=isrc, service=spotify_service, view_count=data["view_count"], timestamp=data["timestamp"]
            )
            if success:
                stats["spotify_loaded"] += 1
            else:
                stats["spotify_errors"] += 1

        logger.info(f"Loading {len(youtube_data)} YouTube view counts...")
        for isrc, data in youtube_data.items():
            success = self._load_single_view_count(
                isrc=isrc, service=youtube_service, view_count=data["view_count"], timestamp=data["timestamp"]
            )
            if success:
                stats["youtube_loaded"] += 1
            else:
                stats["youtube_errors"] += 1

        stats["total_loaded"] = stats["spotify_loaded"] + stats["youtube_loaded"]
        stats["total_errors"] = stats["spotify_errors"] + stats["youtube_errors"]

        return stats

    def _load_single_view_count(self, isrc: str, service: Service, view_count: int, timestamp: datetime) -> bool:
        try:
            with transaction.atomic():
                view_record, created = ViewCount.objects.update_or_create(
                    isrc=isrc,
                    service=service,
                    defaults={"view_count": view_count, "last_updated": django_timezone.now()},
                )

                delta_count = self._calculate_delta(isrc, service, view_count)
                historical_record, hist_created = HistoricalViewCount.objects.update_or_create(
                    isrc=isrc,
                    service=service,
                    recorded_date=django_timezone.now().date(),
                    defaults={"view_count": view_count, "delta_count": delta_count},
                )

            return True

        except Exception as e:
            logger.error(f"Error loading view count for {isrc} on {service.name}: {e}")
            return False

    def _calculate_delta(self, isrc: str, service: Service, current_count: int) -> int | None:
        try:
            yesterday = django_timezone.now().date() - timedelta(days=1)
            previous = HistoricalViewCount.objects.filter(isrc=isrc, service=service, recorded_date=yesterday).first()

            if previous and previous.view_count is not None:
                delta = max(0, current_count - previous.view_count)
                return delta
            else:
                return 0

        except Exception as e:
            logger.error(f"Error calculating delta for {isrc}: {e}")
            return 0
