"""
Raw data models for Phase 2: RawPlaylistData storage.

This model stores unprocessed playlist data as received from external APIs.
The data is then normalized in Phase 3 and hydrated in Phase 4.
"""

from typing import ClassVar

from core.models.a_genre_service import Genre, Service
from django.db import models


class RawPlaylistData(models.Model):
    """
    Raw playlist data storage for ETL pipeline.

    Stores unprocessed playlist data as received from external APIs.
    This data is then transformed into the normalized models.

    The data field contains the full JSON response from services like:
    - Spotify API playlist tracks
    - Apple Music playlist data
    - SoundCloud playlist tracks

    Created by: 02_raw_extract.py
    Used by: 03_normalize_raw_playlists.py
    """

    id = models.BigAutoField(primary_key=True)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, help_text="Genre of this playlist data")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, help_text="Service this data came from")

    playlist_url = models.URLField(help_text="Original playlist URL")
    playlist_name = models.CharField(max_length=255, blank=True, help_text="Playlist display name")
    playlist_cover_url = models.URLField(blank=True, help_text="Playlist cover image URL")
    playlist_cover_description_text = models.TextField(blank=True, help_text="Cover image description")

    data = models.JSONField(help_text="Raw JSON data from service API")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "raw_playlist_data"
        indexes: ClassVar = [
            models.Index(fields=["genre", "service"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["playlist_url"]),
        ]
        ordering: ClassVar = ["-created_at"]

    def __str__(self) -> str:
        return f"Raw {self.service.name} {self.genre.name} data"
