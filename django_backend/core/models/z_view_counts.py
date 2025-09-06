"""
Z: View count models (Django and Pydantic) for tracking track popularity across services.

These models store current and historical view count data for tracks.
Updated by: view count ETL processes
Used by: Analytics and reporting

Django models: Database storage for view counts
Pydantic models: ETL data validation and API serialization
"""

from datetime import datetime
from enum import Enum
from typing import ClassVar

from core.models.b_genre_service import Service
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from pydantic import BaseModel, Field

from playlist_etl.constants import ServiceName


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

    id = models.BigAutoField(primary_key=True)
    isrc = models.CharField(
        max_length=12,
        validators=[RegexValidator(r"^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$", "Invalid ISRC format")],
        help_text="International Standard Recording Code (12 characters)",
        db_index=True,
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
    delta_count = models.BigIntegerField(null=True, blank=True, help_text="Change in view count from previous day")
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


class DataSourceServiceName(str, Enum):
    SPOTIFY = ServiceName.SPOTIFY.value
    YOUTUBE = "YouTube"


class StartView(BaseModel):
    view_count: int | None = None
    timestamp: datetime | None = None


class CurrentView(BaseModel):
    view_count: int | None = None
    timestamp: datetime | None = None


class HistoricalView(BaseModel):
    total_view_count: int | None = None
    delta_view_count: int | None = None
    timestamp: datetime | None = None


class YouTubeView(BaseModel):
    view_count: int | None = None
    timestamp: datetime | None = None


class ServiceView(BaseModel):
    service_name: DataSourceServiceName
    start_view: StartView = Field(default_factory=StartView)
    current_view: CurrentView = Field(default_factory=CurrentView)
    historical_view: list[HistoricalView] = []
    youtube_view: YouTubeView = Field(default_factory=YouTubeView)
