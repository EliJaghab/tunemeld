"""
View count models for tracking track popularity across services.

These models store current and historical view count data for tracks.
Updated by: view count ETL processes
Used by: Analytics and reporting
"""

from typing import ClassVar

from core.models.a_genre_service import Service
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


class ViewCount(models.Model):
    """
    Current view/play counts for tracks from various services.

    Stores the most recent view count data for tracks. This is updated
    regularly by the view count ETL process.

    Example:
        view_count = ViewCount(
            isrc="USSM12201546",
            service=youtube_service,
            view_count=50000000,
            last_updated=timezone.now()
        )
    """

    isrc = models.CharField(
        max_length=12,
        primary_key=True,
        validators=[RegexValidator(r"^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$", "Invalid ISRC format")],
        help_text="International Standard Recording Code (12 characters)",
    )
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    view_count = models.BigIntegerField(help_text="Current view/play count")
    last_updated = models.DateTimeField(help_text="When this count was last fetched")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "view_counts"
        indexes: ClassVar = [
            models.Index(fields=["service"]),
            models.Index(fields=["last_updated"]),
            models.Index(fields=["view_count"]),
        ]
        unique_together: ClassVar = [("isrc", "service")]

    def __str__(self):
        return f"{self.isrc} - {self.view_count:,} views on {self.service.name}"


class HistoricalViewCount(models.Model):
    """
    Historical view count data for trend analysis.

    Stores snapshots of view counts over time to track growth patterns
    and popularity trends.

    Example:
        historical = HistoricalViewCount(
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
    recorded_date = models.DateField(help_text="Date this count was recorded", default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "historical_view_counts"
        indexes: ClassVar = [
            models.Index(fields=["service", "recorded_date"]),
            models.Index(fields=["recorded_date"]),
        ]
        unique_together: ClassVar = [("isrc", "service", "recorded_date")]

    def __str__(self):
        return f"{self.isrc} - {self.view_count:,} views on {self.recorded_date}"
