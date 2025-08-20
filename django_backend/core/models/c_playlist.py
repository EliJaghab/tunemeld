"""
Playlist model for Phase C: Clean playlist positioning data.

This model stores playlist positioning information and links to ServiceTrack records
which contain the detailed track metadata from each service.
"""

from typing import ClassVar

from core.models.a_genre_service import Genre, Service
from django.core.validators import RegexValidator
from django.db import models


class Playlist(models.Model):
    """
    Playlist positioning data linking to ServiceTrack records.

    Stores the relationship between playlist positions and ServiceTrack records,
    with ISRC populated after Phase D resolution.

    Created by: c_normalize_raw_playlists.py
    Used by: Later phases for aggregation and ranking
    """

    id = models.BigAutoField(primary_key=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()

    # ISRC (populated after Phase D resolution)
    isrc = models.CharField(
        max_length=12,
        validators=[RegexValidator(r"^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$", "Invalid ISRC format")],
        help_text="International Standard Recording Code (12 characters)",
        db_index=True,
        null=True,
        blank=True,
    )

    # Link to the detailed service track record
    service_track = models.ForeignKey(
        "ServiceTrack",
        on_delete=models.CASCADE,
        help_text="Reference to the normalized service track record",
        related_name="playlists",
    )

    class Meta:
        db_table = "playlists"
        ordering: ClassVar = ["service", "genre", "position"]
        indexes: ClassVar = [
            models.Index(fields=["service", "genre"]),
            models.Index(fields=["isrc"]),
        ]
        unique_together: ClassVar = [("service", "genre", "position")]

    def __str__(self) -> str:
        return f"Position {self.position}: {self.isrc} ({self.service.name} {self.genre.name})"
