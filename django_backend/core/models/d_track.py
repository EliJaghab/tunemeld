"""
Phase D: Track model for hydrated track metadata.

This model stores consolidated track metadata with ISRC as the primary key.
Created by: d_hydrate_tracks.py
Used by: e_aggregate.py for cross-service aggregation
"""

from typing import ClassVar

from django.core.validators import RegexValidator
from django.db import models


class Track(models.Model):
    """
    Represents a unique music track identified by ISRC.

    Contains all track metadata including service-specific information.
    ISRC serves as the primary key for global uniqueness.

    Example:
        track = Track(
            isrc="USSM12201546",
            track_name="Flowers",
            artist_name="Miley Cyrus",
            album_name="Endless Summer Vacation",
            spotify_url="https://open.spotify.com/track/7xGfFoTpQ2E7fRF5lN10tr"
        )
    """

    isrc = models.CharField(
        max_length=12,
        primary_key=True,
        validators=[RegexValidator(r"^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$", "Invalid ISRC format")],
        help_text="International Standard Recording Code (12 characters)",
    )
    track_name = models.CharField(max_length=500, help_text="Name of the track")
    artist_name = models.CharField(max_length=500, help_text="Primary artist name")
    album_name = models.CharField(max_length=500, null=True, blank=True, help_text="Album name")

    spotify_url = models.URLField(null=True, blank=True, help_text="Spotify track URL")
    apple_music_url = models.URLField(null=True, blank=True, help_text="Apple Music track URL")
    youtube_url = models.URLField(null=True, blank=True, help_text="YouTube track URL")
    soundcloud_url = models.URLField(null=True, blank=True, help_text="SoundCloud track URL")

    album_cover_url = models.URLField(null=True, blank=True, help_text="Album cover image URL")

    aggregate_rank = models.IntegerField(null=True, blank=True, help_text="Cross-service aggregate ranking")
    aggregate_score = models.FloatField(null=True, blank=True, help_text="Cross-service aggregate score")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tracks"
        indexes: ClassVar = [
            models.Index(fields=["track_name", "artist_name"]),
            models.Index(fields=["artist_name"]),
        ]

    def __str__(self):
        return f"{self.track_name} by {self.artist_name} ({self.isrc})"
