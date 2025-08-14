"""
PlaylistTrack model for Phase 3: Normalized playlist data table.

This model stores normalized track data from all services in a single table.
Each row represents one track from one service's playlist, with columns
mapped to a standard schema and NULL values where data isn't available.
"""

from typing import ClassVar

from core.models.a_lookup_tables import Genre, Service
from django.db import models


class PlaylistTrack(models.Model):
    """
    Normalized playlist track data table.

    Stores all tracks from all services in a single normalized table.
    Each service contributes different fields - NULL where unavailable.

    Created by: 03_normalize_raw_playlists.py
    Used by: 04_hydrate_tracks.py for ISRC resolution
    """

    id = models.BigAutoField(primary_key=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)

    position = models.PositiveIntegerField()
    service_track_id = models.CharField(max_length=200, null=True, blank=True)

    track_name = models.CharField(max_length=500)
    artist_name = models.CharField(max_length=500)
    album_name = models.CharField(max_length=500, null=True, blank=True)

    isrc = models.CharField(max_length=12, null=True, blank=True, db_index=True)

    spotify_url = models.URLField(null=True, blank=True)
    apple_music_url = models.URLField(null=True, blank=True)
    soundcloud_url = models.URLField(null=True, blank=True)

    preview_url = models.URLField(null=True, blank=True)
    album_cover_url = models.URLField(null=True, blank=True)

    class Meta:
        db_table = "playlist_tracks"
        ordering: ClassVar = ["service", "genre", "position"]
        indexes: ClassVar = [
            models.Index(fields=["service", "genre"]),
            models.Index(fields=["isrc"]),
            models.Index(fields=["track_name", "artist_name"]),
        ]

    def __str__(self) -> str:
        return f"{self.track_name} by {self.artist_name} ({self.service.name})"
