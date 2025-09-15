import logging
from datetime import timedelta

from core.models.view_counts import HistoricalTrackViewCount
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Compute delta view counts by comparing with previous day's data"

    def handle(self, *args, **options):
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)

        logger.info(f"Computing delta view counts for {today}")

        todays_records = HistoricalTrackViewCount.objects.filter(recorded_date=today, daily_view_change__isnull=True)

        updated_count = 0

        for record in todays_records:
            # Find yesterday's record for the same track and service
            yesterday_record = HistoricalTrackViewCount.objects.filter(
                isrc=record.isrc, service=record.service, recorded_date=yesterday
            ).first()

            if yesterday_record:
                # Calculate daily change and percentage
                daily_change = record.current_view_count - yesterday_record.current_view_count
                record.daily_view_change = daily_change

                # Calculate percentage change (avoid division by zero)
                if yesterday_record.current_view_count > 0:
                    record.daily_change_percentage = (daily_change / yesterday_record.current_view_count) * 100
                else:
                    record.daily_change_percentage = 100.0 if daily_change > 0 else 0.0

                record.save(update_fields=["daily_view_change", "daily_change_percentage"])

                logger.info(
                    f"{record.isrc} on {record.service.name}: "
                    f"{record.current_view_count:,} views "
                    f"(Δ {daily_change:+,} / {record.daily_change_percentage:+.2f}%)"
                )
                updated_count += 1
            else:
                record.daily_view_change = 0
                record.daily_change_percentage = 0.0
                record.save(update_fields=["daily_view_change", "daily_change_percentage"])

                logger.info(
                    f"{record.isrc} on {record.service.name}: {record.current_view_count:,} views (first record)"
                )
                updated_count += 1

        logger.info(f"Updated delta counts for {updated_count} records")
