"""
Play count models for tracking track popularity across services over time.

Contains both historical snapshots and aggregate calculations for play count analytics.
Updated by: play count ETL processes
Used by: Analytics and reporting
"""

from typing import ClassVar

from core.models.genre_service import Service
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


class HistoricalTrackPlayCount(models.Model):
    """
    Historical play count changelog for individual services.

    Pure changelog that stores raw play count snapshots over time.
    No calculations or aggregations - just the raw data points.

    Example:
        historical = HistoricalTrackPlayCount(
            isrc="USSM12201546",
            service=youtube_service,
            current_play_count=45000000,
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
    current_play_count = models.BigIntegerField(help_text="Raw play count at this point in time")
    recorded_date = models.DateField(help_text="Date this count was recorded", default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "historical_track_play_counts"
        indexes: ClassVar = [
            models.Index(fields=["service", "recorded_date"]),
            models.Index(fields=["recorded_date"]),
        ]
        unique_together: ClassVar = [("isrc", "service", "recorded_date")]

    def __str__(self):
        return f"{self.isrc} - {self.current_play_count:,} plays on {self.recorded_date}"


class AggregatePlayCount(models.Model):
    """
    Service-specific and aggregated play count data with time-based analytics.

    Structure:
    - Individual service rows: One row per service (youtube, spotify, etc.) per ISRC per date
    - "All" service row: Aggregated totals across all services per ISRC per date

    Each row contains:
    - current_play_count: Raw play count for this service (or total for "all")
    - weekly_change: Absolute change from one week ago
    - weekly_change_percentage: Percentage change from one week ago

    Examples:
        # Individual YouTube service row
        AggregatePlayCount(
            isrc="USSM12201546",
            service=youtube_service,
            current_play_count=45000000,
            weekly_change=2000000,
            weekly_change_percentage=4.65,
            recorded_date=date(2024, 1, 15)
        )

        # Aggregated "all" service row
        AggregatePlayCount(
            isrc="USSM12201546",
            service=all_service,
            current_play_count=75000000,
            weekly_change=3500000,
            weekly_change_percentage=4.9,
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

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        help_text="Service for this play count record (individual service or 'all' for aggregated)",
    )

    current_play_count = models.BigIntegerField(
        help_text="Current play count for this service (or total for 'all' service)"
    )

    weekly_change = models.BigIntegerField(null=True, blank=True, help_text="Absolute change from one week ago")
    weekly_change_percentage = models.FloatField(null=True, blank=True, help_text="Percentage change from one week ago")

    recorded_date = models.DateField(
        help_text="Date this aggregate was calculated", default=timezone.now, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "aggregate_play_counts"
        indexes: ClassVar = [
            models.Index(fields=["service", "isrc", "recorded_date"]),
            models.Index(fields=["recorded_date"]),
            models.Index(fields=["isrc", "recorded_date"]),
        ]
        unique_together: ClassVar = [("service", "isrc", "recorded_date")]

    def __str__(self):
        return f"{self.isrc} [{self.service.name}] - {self.current_play_count:,} plays on {self.recorded_date}"
