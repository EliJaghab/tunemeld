"""
Service track model for Phase C: Normalized track data from all services.

This model stores track metadata from each service before ISRC resolution
and consolidation into the final Track model.
"""

from typing import ClassVar

from core.models.a_genre_service import Genre, Service
from django.core.validators import RegexValidator
from django.db import models


class ServiceTrack(models.Model):
    """Normalized track data from all services before consolidation."""

    id = models.BigAutoField(primary_key=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    position = models.PositiveIntegerField(help_text="Position in playlist")

    # Track metadata
    track_name = models.CharField(max_length=500, help_text="Name of the track")
    artist_name = models.CharField(max_length=500, help_text="Primary artist name")
    album_name = models.CharField(max_length=500, null=True, blank=True, help_text="Album name")

    # Service-specific URL
    service_url = models.URLField(help_text="Service-specific track URL")

    isrc = models.CharField(
        max_length=12,
        validators=[RegexValidator(r"^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$", "Invalid ISRC format")],
        help_text="International Standard Recording Code (12 characters)",
    )

    album_cover_url = models.URLField(null=True, blank=True, help_text="Album cover image URL")

    track = models.ForeignKey(
        "Track",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Reference to consolidated Track record",
        related_name="service_tracks",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "service_tracks"
        unique_together: ClassVar = [("service", "genre", "position")]
        indexes: ClassVar = [
            models.Index(fields=["service", "genre"]),
            models.Index(fields=["isrc"]),
            models.Index(fields=["track_name", "artist_name"]),
            models.Index(fields=["service", "isrc"]),
        ]

    def __str__(self) -> str:
        return f"{self.track_name} by {self.artist_name} ({self.service.name})"
