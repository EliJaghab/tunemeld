"""
Transform and Load phase models for TuneMeld ETL pipeline.
"""

from typing import ClassVar

from core.models.a_lookup_tables import Service
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


class Track(models.Model):
    """
    Represents a unique music track across all services.

    Tracks are identified by ISRC (International Standard Recording Code)
    when available, or by a combination of track name and primary artist.

    Example:
        track = Track(
            track_name="Flowers",
            artist_name="Miley Cyrus",
            isrc="USSM12201546"
        )
    """

    id = models.BigAutoField(primary_key=True)
    track_name = models.CharField(max_length=500, help_text="Name of the track")
    artist_name = models.CharField(max_length=500, help_text="Primary artist name")
    isrc = models.CharField(
        max_length=12,
        blank=True,
        validators=[RegexValidator(r"^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$", "Invalid ISRC format")],
        help_text="International Standard Recording Code (12 characters)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tracks"
        indexes: ClassVar = [
            models.Index(fields=["isrc"]),
            models.Index(fields=["track_name", "artist_name"]),
            models.Index(fields=["artist_name"]),
        ]
        unique_together: ClassVar = [("track_name", "artist_name")]

    def __str__(self):
        return f"{self.track_name} by {self.artist_name}"


class TrackData(models.Model):
    """
    Service-specific metadata for tracks.

    Links tracks to services and stores service-specific information
    like track IDs, URLs, and metadata.

    Example:
        track_data = TrackData(
            track=flowers_track,
            service=spotify_service,
            service_track_id="7xGfFoTpQ2E7fRF5lN10tr",
            service_url="https://open.spotify.com/track/7xGfFoTpQ2E7fRF5lN10tr"
        )
    """

    id = models.BigAutoField(primary_key=True)
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name="track_data")
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    service_track_id = models.CharField(max_length=100, help_text="Track ID on the service")
    service_url = models.URLField(blank=True, help_text="Direct URL to track on service")
    duration_ms = models.IntegerField(null=True, blank=True, help_text="Track duration in milliseconds")
    popularity_score = models.IntegerField(null=True, blank=True, help_text="Service-specific popularity score")
    preview_url = models.URLField(blank=True, help_text="Preview/sample audio URL")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "track_data"
        indexes: ClassVar = [
            models.Index(fields=["service", "service_track_id"]),
            models.Index(fields=["track", "service"]),
        ]
        unique_together: ClassVar = [("track", "service")]

    def __str__(self):
        return f"{self.track_name} by {self.artist_name} on {self.service.name}"


class ViewCount(models.Model):
    """
    Current view/play counts for tracks from various services.

    Stores the most recent view count data for tracks. This is updated
    regularly by the view count ETL process.

    Example:
        view_count = ViewCount(
            track=flowers_track,
            service=youtube_service,
            view_count=50000000,
            last_updated=timezone.now()
        )
    """

    id = models.BigAutoField(primary_key=True)
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name="view_counts")
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    view_count = models.BigIntegerField(help_text="Current view/play count")
    last_updated = models.DateTimeField(help_text="When this count was last fetched")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "view_counts"
        indexes: ClassVar = [
            models.Index(fields=["track", "service"]),
            models.Index(fields=["last_updated"]),
            models.Index(fields=["view_count"]),
        ]
        unique_together: ClassVar = [("track", "service")]

    def __str__(self):
        return f"{self.track} - {self.view_count:,} views on {self.service.name}"


class HistoricalViewCount(models.Model):
    """
    Historical view count data for trend analysis.

    Stores snapshots of view counts over time to track growth patterns
    and popularity trends.

    Example:
        historical = HistoricalViewCount(
            track=flowers_track,
            service=youtube_service,
            view_count=45000000,
            recorded_date=date(2024, 1, 15)
        )
    """

    id = models.BigAutoField(primary_key=True)
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name="historical_view_counts")
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    view_count = models.BigIntegerField(help_text="View count at this point in time")
    recorded_date = models.DateField(help_text="Date this count was recorded", default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "historical_view_counts"
        indexes: ClassVar = [
            models.Index(fields=["track", "service", "recorded_date"]),
            models.Index(fields=["recorded_date"]),
        ]
        unique_together: ClassVar = [("track", "service", "recorded_date")]

    def __str__(self):
        return f"{self.track} - {self.view_count:,} views on {self.recorded_date}"
