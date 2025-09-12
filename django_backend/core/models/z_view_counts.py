"""
Z: Historical view count model for tracking track popularity across services over time.

Stores snapshots of view counts over time to track growth patterns and popularity trends.
Updated by: view count ETL processes
Used by: Analytics and reporting
"""

from typing import ClassVar

from core.models.b_genre_service import Service
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


class HistoricalTrackViewCount(models.Model):
    """
    Historical view count data for trend analysis.

    Stores snapshots of view counts over time to track growth patterns
    and popularity trends.

    Example:
        historical = HistoricalTrackViewCount(
            isrc="USSM12201546",
            service=youtube_service,
            view_count=45000000,
            recorded_date=date(2024, 1, 15)
        )
    """

    id = models.BigAutoField(primary_key=True)
    isrc = models.CharField(
        max_length=12,
        validators=[RegexValidator(r"^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$", "Invalid ISRC format")],
        help_text="International Standard Recording Code (12 characters)",
        db_index=True,
    )
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    view_count = models.BigIntegerField(help_text="View count at this point in time")
    delta_count = models.BigIntegerField(null=True, blank=True, help_text="Change in view count from previous day")
    recorded_date = models.DateField(help_text="Date this count was recorded", default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "historical_track_view_counts"
        indexes: ClassVar = [
            models.Index(fields=["service", "recorded_date"]),
            models.Index(fields=["recorded_date"]),
        ]
        unique_together: ClassVar = [("isrc", "service", "recorded_date")]

    def __str__(self):
        return f"{self.isrc} - {self.view_count:,} views on {self.recorded_date}"


