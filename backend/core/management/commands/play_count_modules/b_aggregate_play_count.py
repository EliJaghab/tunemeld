import logging
from datetime import timedelta

from core.constants import ServiceName
from core.models.genre_service import Service
from core.models.play_counts import AggregatePlayCount, HistoricalTrackPlayCount
from django.core.management.base import BaseCommand
from django.db.models import Q, Sum
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Calculate and store aggregate play counts using the new AggregatePlayCount model"

    def handle(self, *args, **options):
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)

        logger.info(f"Computing aggregate play counts for {today}")

        try:
            # Get services
            youtube_service = Service.objects.get(name=ServiceName.YOUTUBE)
            spotify_service = Service.objects.get(name=ServiceName.SPOTIFY)
            soundcloud_service = Service.objects.get(name=ServiceName.SOUNDCLOUD)
            all_service = Service.objects.get(name=ServiceName.TOTAL)
        except Service.DoesNotExist as e:
            logger.error(f"Required service not found: {e}")
            return

        # Get all unique TuneMeld ISRCs from today's data (any service)
        todays_isrcs = set(HistoricalTrackPlayCount.objects.filter(recorded_date=today).values_list("isrc", flat=True))

        created_count = 0
        updated_count = 0

        for isrc in todays_isrcs:
            # Get today's counts for all available services for this ISRC
            todays_counts = HistoricalTrackPlayCount.objects.filter(isrc=isrc, recorded_date=today).aggregate(
                youtube_count=Sum("current_play_count", filter=Q(service=youtube_service)),
                spotify_count=Sum("current_play_count", filter=Q(service=spotify_service)),
                soundcloud_count=Sum("current_play_count", filter=Q(service=soundcloud_service)),
            )

            youtube_count = todays_counts["youtube_count"] or 0
            spotify_count = todays_counts["spotify_count"] or 0
            soundcloud_count = todays_counts["soundcloud_count"] or 0
            total_count = youtube_count + spotify_count + soundcloud_count

            # Skip if no play count data available from any service
            if total_count == 0:
                continue

            # Get earliest available date for this ISRC (use min between earliest date and week ago)
            earliest_date = (
                HistoricalTrackPlayCount.objects.filter(isrc=isrc)
                .values_list("recorded_date", flat=True)
                .order_by("recorded_date")
                .first()
            )
            comparison_date = min(earliest_date, week_ago) if earliest_date else week_ago

            # Get comparison counts from the determined date
            comparison_counts = HistoricalTrackPlayCount.objects.filter(
                isrc=isrc, recorded_date=comparison_date
            ).aggregate(
                youtube_count=Sum("current_play_count", filter=Q(service=youtube_service)),
                spotify_count=Sum("current_play_count", filter=Q(service=spotify_service)),
                soundcloud_count=Sum("current_play_count", filter=Q(service=soundcloud_service)),
            )

            comparison_youtube = comparison_counts["youtube_count"] or 0
            comparison_spotify = comparison_counts["spotify_count"] or 0
            comparison_soundcloud = comparison_counts["soundcloud_count"] or 0
            comparison_total = comparison_youtube + comparison_spotify + comparison_soundcloud

            # Create individual service records
            service_data = [
                {
                    "service": youtube_service,
                    "current_count": youtube_count,
                    "comparison_count": comparison_youtube,
                },
                {
                    "service": spotify_service,
                    "current_count": spotify_count,
                    "comparison_count": comparison_spotify,
                },
                {
                    "service": soundcloud_service,
                    "current_count": soundcloud_count,
                    "comparison_count": comparison_soundcloud,
                },
                {
                    "service": all_service,
                    "current_count": total_count,
                    "comparison_count": comparison_total,
                },
            ]

            for service_info in service_data:
                service = service_info["service"]
                current_count = service_info["current_count"]
                comparison_count = service_info["comparison_count"]

                # Skip individual services with zero counts
                if service != all_service and current_count == 0:
                    continue

                # Calculate weekly change
                weekly_change = None
                weekly_change_percentage = None
                if comparison_count > 0:
                    weekly_change = current_count - comparison_count
                    weekly_change_percentage = (weekly_change / comparison_count) * 100

                # Create or update service-specific record
                _service_record, created = AggregatePlayCount.objects.update_or_create(
                    isrc=isrc,
                    service=service,
                    recorded_date=today,
                    defaults={
                        "current_play_count": current_count,
                        "weekly_change": weekly_change,
                        "weekly_change_percentage": weekly_change_percentage,
                    },
                )

                if created:
                    created_count += 1
                    logger.info(
                        f"Created {service.name} record for {isrc}: {current_count:,} plays"
                        + (f" Weekly: {weekly_change_percentage:+.2f}%" if weekly_change_percentage else "")
                    )
                else:
                    updated_count += 1
                    logger.info(
                        f"Updated {service.name} record for {isrc}: {current_count:,} plays"
                        + (f" Weekly: {weekly_change_percentage:+.2f}%" if weekly_change_percentage else "")
                    )

        logger.info(f"Aggregate play count processing completed. Created: {created_count}, Updated: {updated_count}")
