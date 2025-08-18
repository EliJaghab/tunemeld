"""
Playlist model for Phase 3: Clean playlist positioning data.

This model stores only playlist positioning information, linking ISRCs
to their positions in service playlists. Track metadata is stored separately
in the Track model to eliminate duplication.
"""

from typing import ClassVar

from core.models.a_lookup_tables import Genre, Service
from django.core.validators import RegexValidator
from django.db import models


class PlaylistTrack(models.Model):
    """
    Playlist track positioning data linking ISRCs to playlist positions.

    Stores only the relationship between tracks (by ISRC) and their
    positions in service playlists. Track metadata is normalized separately.

    Created by: c_normalize_raw_playlists.py
    Used by: d_hydrate_tracks.py for ISRC resolution and Track creation
    """

    id = models.BigAutoField(primary_key=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()
    isrc = models.CharField(
        max_length=12,
        validators=[RegexValidator(r"^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$", "Invalid ISRC format")],
        help_text="International Standard Recording Code (12 characters)",
        db_index=True,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "playlist_tracks"
        ordering: ClassVar = ["service", "genre", "position"]
        indexes: ClassVar = [
            models.Index(fields=["service", "genre"]),
        ]
        unique_together: ClassVar = [("service", "genre", "position")]

    def __str__(self) -> str:
        return f"Position {self.position}: {self.isrc} ({self.service.name} {self.genre.name})"
